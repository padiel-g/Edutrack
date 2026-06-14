import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from xml.sax.saxutils import escape

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func

from app.extensions import db, limiter
from app.models import (
    AcademicYear,
    Attendance,
    ReportCard,
    ReportSignature,
    SchoolClass,
    SchoolSetting,
    Student,
    StudentResult,
    Subject,
    Teacher,
    Term,
    User,
    teacher_subjects,
)
from app.services.audit import write_audit
from app.utils.security import roles_required

report_cards_bp = Blueprint("report_cards", __name__)
EFFORT_GRADES = ["Excellent", "Very Good", "Good", "Satisfactory", "Needs Improvement"]
SUMMARY_GRADES = ["Excellent", "Very Good", "Good", "Satisfactory", "Needs Improvement"]
REPORT_STATUSES = {"Draft", "Pending Approval", "Returned", "Rejected", "Approved", "Published"}


def current_teacher():
    identity = get_jwt_identity()
    return Teacher.query.filter_by(user_id=int(identity)).first() if identity and str(identity).isdigit() else None


def number(value, field):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} must be a number.")
    if parsed < 0 or parsed > 100:
        raise ValueError(f"{field} must be between 0 and 100.")
    return parsed


def period_options():
    return {
        "academicYears": [
            {"id": item.id, "name": item.name, "isCurrent": item.is_current}
            for item in AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
        ],
        "terms": [
            {
                "id": item.id,
                "name": item.name,
                "academicYearId": item.academic_year_id,
                "isCurrent": item.is_current,
            }
            for item in Term.query.order_by(Term.start_date.desc()).all()
        ],
    }


def assigned_subject(teacher_id, class_id, subject_id):
    return db.session.execute(
        db.select(teacher_subjects.c.teacher_id).where(
            teacher_subjects.c.teacher_id == teacher_id,
            teacher_subjects.c.class_id == class_id,
            teacher_subjects.c.subject_id == subject_id,
        )
    ).first() is not None


def class_teacher_for(student):
    return student.school_class.class_teacher if student.school_class else None


def attendance_rate(student_id, term):
    query = Attendance.query.filter_by(student_id=student_id)
    if term:
        query = query.filter(Attendance.date >= term.start_date, Attendance.date <= term.end_date)
    total = query.count()
    present = query.filter(func.lower(Attendance.status) == "present").count()
    return round((present / total) * 100, 1) if total else 0


def report_payload(report):
    payload = report.to_dict()
    payload["attendanceRate"] = attendance_rate(report.student_id, report.term)
    return payload


@report_cards_bp.get("/teacher/report-options")
@jwt_required()
@roles_required("Teacher")
def teacher_report_options():
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404
    rows = db.session.execute(
        db.select(SchoolClass, Subject)
        .join(teacher_subjects, teacher_subjects.c.class_id == SchoolClass.id)
        .join(Subject, Subject.id == teacher_subjects.c.subject_id)
        .where(teacher_subjects.c.teacher_id == teacher.id)
        .order_by(SchoolClass.grade_level, SchoolClass.name, Subject.name)
    ).all()
    classes = {}
    for school_class, subject in rows:
        entry = classes.setdefault(
            school_class.id,
            {
                "id": school_class.id,
                "name": school_class.name,
                "isClassTeacher": school_class.teacher_id == teacher.id,
                "subjects": [],
                "students": [
                    {"id": student.id, "registrationNumber": student.registration_number, "name": student.to_dict()["name"]}
                    for student in sorted(school_class.students, key=lambda item: (item.last_name, item.first_name))
                    if student.status == "active"
                ],
            },
        )
        entry["subjects"].append(subject.to_dict())
    class_teacher_classes = SchoolClass.query.filter_by(teacher_id=teacher.id).all()
    for school_class in class_teacher_classes:
        classes.setdefault(
            school_class.id,
            {
                "id": school_class.id,
                "name": school_class.name,
                "isClassTeacher": True,
                "subjects": [],
                "students": [
                    {"id": student.id, "registrationNumber": student.registration_number, "name": student.to_dict()["name"]}
                    for student in sorted(school_class.students, key=lambda item: (item.last_name, item.first_name))
                    if student.status == "active"
                ],
            },
        )
    return jsonify({"teacher": {"id": teacher.id, "name": teacher.to_dict()["name"]}, "classes": list(classes.values()), **period_options(), "effortGrades": EFFORT_GRADES, "summaryGrades": SUMMARY_GRADES})


@report_cards_bp.get("/results/class/<int:class_id>")
@jwt_required()
@roles_required("Teacher")
def class_results(class_id):
    teacher = current_teacher()
    subject_id = request.args.get("subjectId", type=int)
    term_id = request.args.get("termId", type=int)
    year_id = request.args.get("academicYearId", type=int)
    if not teacher or not subject_id or not assigned_subject(teacher.id, class_id, subject_id):
        return jsonify({"error": "You are not assigned to this subject and class."}), 403
    query = StudentResult.query.filter_by(teacher_id=teacher.id, class_id=class_id, subject_id=subject_id)
    if term_id:
        query = query.filter_by(term_id=term_id)
    if year_id:
        query = query.filter_by(academic_year_id=year_id)
    return jsonify({"items": [item.to_dict() for item in query.order_by(StudentResult.student_id).all()]})


@report_cards_bp.post("/results")
@jwt_required()
@roles_required("Teacher")
@limiter.limit("120 per hour")
def save_result():
    data = request.get_json() or {}
    teacher = current_teacher()
    required = ["studentId", "subjectId", "termId", "academicYearId"]
    if any(not data.get(field) for field in required):
        return jsonify({"error": "Student, subject, academic year, and term are required."}), 400
    student = db.session.get(Student, int(data["studentId"]))
    if not student or not student.class_id:
        return jsonify({"error": "Student is not assigned to a class."}), 400
    if not teacher or not assigned_subject(teacher.id, student.class_id, int(data["subjectId"])):
        return jsonify({"error": "You can only enter marks for your assigned subject and class."}), 403
    term = db.session.get(Term, int(data["termId"]))
    if not term or term.academic_year_id != int(data["academicYearId"]):
        return jsonify({"error": "The selected term does not belong to the academic year."}), 400
    locked_report = ReportCard.query.filter_by(
        student_id=student.id,
        term_id=term.id,
        academic_year_id=int(data["academicYearId"]),
    ).first()
    if locked_report and locked_report.status in {"Pending Approval", "Approved", "Published"}:
        return jsonify({"error": "Marks are locked while the report is under review or published."}), 409
    try:
        ca_mark = number(data.get("caMark"), "CA mark")
        exam_mark = number(data.get("examMark"), "Examination mark")
        final_mark = number(data.get("finalMark"), "Final mark")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    effort = (data.get("effortGrade") or "").strip()
    if effort not in EFFORT_GRADES:
        return jsonify({"error": "Select a valid effort grade."}), 400
    result = StudentResult.query.filter_by(
        student_id=student.id,
        subject_id=int(data["subjectId"]),
        term_id=term.id,
        academic_year_id=int(data["academicYearId"]),
    ).first()
    if result and result.teacher_id != teacher.id:
        return jsonify({"error": "This result belongs to another assigned teacher."}), 403
    if not result:
        result = StudentResult(
            student_id=student.id,
            subject_id=int(data["subjectId"]),
            teacher_id=teacher.id,
            class_id=student.class_id,
            term_id=term.id,
            academic_year_id=int(data["academicYearId"]),
        )
        db.session.add(result)
    result.ca_mark = ca_mark
    result.exam_mark = exam_mark
    result.final_mark = final_mark
    result.effort_grade = effort
    db.session.flush()
    write_audit("student_result_saved", "StudentResult", result.id, {"studentId": student.id, "subjectId": result.subject_id})
    db.session.commit()
    return jsonify({"message": "Result saved successfully.", "item": result.to_dict()}), 201


@report_cards_bp.put("/results/<int:result_id>")
@jwt_required()
@roles_required("Teacher")
def update_result(result_id):
    result = db.session.get(StudentResult, result_id)
    teacher = current_teacher()
    if not result or not teacher or result.teacher_id != teacher.id or not assigned_subject(teacher.id, result.class_id, result.subject_id):
        return jsonify({"error": "Result not found or access denied."}), 404
    locked_report = ReportCard.query.filter_by(
        student_id=result.student_id,
        term_id=result.term_id,
        academic_year_id=result.academic_year_id,
    ).first()
    if locked_report and locked_report.status in {"Pending Approval", "Approved", "Published"}:
        return jsonify({"error": "Marks are locked while the report is under review or published."}), 409
    data = request.get_json() or {}
    try:
        result.ca_mark = number(data.get("caMark"), "CA mark")
        result.exam_mark = number(data.get("examMark"), "Examination mark")
        result.final_mark = number(data.get("finalMark"), "Final mark")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    effort = (data.get("effortGrade") or "").strip()
    if effort not in EFFORT_GRADES:
        return jsonify({"error": "Select a valid effort grade."}), 400
    result.effort_grade = effort
    write_audit("student_result_updated", "StudentResult", result.id)
    db.session.commit()
    return jsonify({"message": "Result updated.", "item": result.to_dict()})


def ensure_class_teacher(student, teacher):
    return bool(student and student.school_class and teacher and student.school_class.teacher_id == teacher.id)


@report_cards_bp.get("/reports/student/<int:student_id>")
@jwt_required()
@roles_required("Teacher", "Admin", "Super Admin")
def student_report(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found."}), 404
    teacher = current_teacher() if get_jwt().get("role") == "Teacher" else None
    if teacher and not ensure_class_teacher(student, teacher):
        return jsonify({"error": "Only the assigned Class Teacher can complete this report."}), 403
    term_id = request.args.get("termId", type=int)
    year_id = request.args.get("academicYearId", type=int)
    if not term_id or not year_id:
        return jsonify({"error": "Academic year and term are required."}), 400
    report = ReportCard.query.filter_by(student_id=student_id, term_id=term_id, academic_year_id=year_id).first()
    results = StudentResult.query.filter_by(student_id=student_id, term_id=term_id, academic_year_id=year_id).join(Subject).order_by(Subject.name).all()
    return jsonify({
        "student": student.to_dict(),
        "classTeacher": class_teacher_for(student).to_dict()["name"] if class_teacher_for(student) else None,
        "results": [item.to_dict() for item in results],
        "attendanceRate": attendance_rate(student_id, db.session.get(Term, term_id)),
        "report": report_payload(report) if report else None,
    })


@report_cards_bp.post("/reports/complete")
@report_cards_bp.put("/reports/update")
@jwt_required()
@roles_required("Teacher")
def complete_report():
    data = request.get_json() or {}
    teacher = current_teacher()
    student = db.session.get(Student, int(data.get("studentId") or 0))
    if not ensure_class_teacher(student, teacher):
        return jsonify({"error": "Only the assigned Class Teacher can complete this report."}), 403
    term = db.session.get(Term, int(data.get("termId") or 0))
    year = db.session.get(AcademicYear, int(data.get("academicYearId") or 0))
    if not term or not year or term.academic_year_id != year.id:
        return jsonify({"error": "Select a valid academic year and term."}), 400
    results = StudentResult.query.filter_by(student_id=student.id, term_id=term.id, academic_year_id=year.id).count()
    if results == 0:
        return jsonify({"error": "No subject teachers have submitted results for this student."}), 400
    fields = {
        "teacher_comment": "teacherComment",
        "overall_achievement": "overallAchievement",
        "attitude_to_learning": "attitudeToLearning",
        "behaviour": "behaviour",
        "attendance_summary": "attendance",
        "targets": "targets",
    }
    targets = data.get("targets")
    has_targets = (
        any(str(item).strip() for item in targets)
        if isinstance(targets, list)
        else bool(str(targets or "").strip())
    )
    text_fields = [source for source in fields.values() if source != "targets"]
    if any(not str(data.get(source) or "").strip() for source in text_fields) or not has_targets:
        return jsonify({"error": "Complete the teacher comment, summary, attendance, and targets."}), 400
    report = ReportCard.query.filter_by(student_id=student.id, term_id=term.id, academic_year_id=year.id).first()
    if report and report.status in {"Approved", "Published", "Rejected"}:
        return jsonify({"error": "Finalized or rejected reports cannot be edited."}), 409
    if not report:
        report = ReportCard(student_id=student.id, term_id=term.id, academic_year_id=year.id)
        db.session.add(report)
    report.class_teacher_id = teacher.id
    for target, source in fields.items():
        value = data[source]
        if source == "targets" and isinstance(value, list):
            value = "\n".join(str(item).strip() for item in value if str(item).strip())
        setattr(report, target, str(value).strip())
    report.status = "Pending Approval"
    report.admin_comment = None
    db.session.flush()
    write_audit("report_submitted_for_approval", "ReportCard", report.id, {"studentId": student.id})
    db.session.commit()
    return jsonify({"message": "Report submitted for approval.", "report": report_payload(report)}), 201


@report_cards_bp.get("/reports/pending")
@jwt_required()
@roles_required("Admin", "Super Admin")
def pending_reports():
    status = (request.args.get("status") or "").strip()
    query = ReportCard.query
    if status:
        query = query.filter_by(status=status)
    else:
        query = query.filter(ReportCard.status.in_(["Pending Approval", "Returned", "Rejected", "Approved", "Published"]))
    return jsonify({"items": [report_payload(item) for item in query.order_by(ReportCard.updated_at.desc()).all()]})


def admin_report_action(action):
    data = request.get_json() or {}
    report = db.session.get(ReportCard, int(data.get("reportId") or 0))
    if not report:
        return jsonify({"error": "Report not found."}), 404
    if report.status != "Pending Approval":
        return jsonify({"error": "Only reports pending approval can be reviewed."}), 409
    user_id = int(get_jwt_identity())
    comment = (data.get("comment") or "").strip() or None
    if action == "approve":
        now = datetime.utcnow()
        report.status = "Published"
        report.approved_by_id = user_id
        report.approved_at = now
        report.published_at = now
        report.admin_comment = comment
        signature_path = setting("admin_signature_path")
        signature = report.signature or ReportSignature(report=report, admin_id=user_id)
        signature.admin_id = user_id
        signature.signature_image = signature_path
        db.session.add(signature)
        audit_action = "report_published"
        message = "Report approved and published."
    elif action == "return":
        report.status = "Returned"
        report.admin_comment = comment or "Please correct and resubmit this report."
        audit_action = "report_returned"
        message = "Report returned for corrections."
    else:
        report.status = "Rejected"
        report.admin_comment = comment or "Report rejected."
        audit_action = "report_rejected"
        message = "Report rejected."
    write_audit(audit_action, "ReportCard", report.id, {"comment": report.admin_comment})
    db.session.commit()
    return jsonify({"message": message, "report": report_payload(report)})


@report_cards_bp.post("/reports/approve")
@jwt_required()
@roles_required("Admin", "Super Admin")
def approve_report():
    return admin_report_action("approve")


@report_cards_bp.post("/reports/return")
@jwt_required()
@roles_required("Admin", "Super Admin")
def return_report():
    return admin_report_action("return")


@report_cards_bp.post("/reports/reject")
@jwt_required()
@roles_required("Admin", "Super Admin")
def reject_report():
    return admin_report_action("reject")


@report_cards_bp.get("/parent/reports")
@jwt_required()
@roles_required("Parent")
def parent_reports():
    student_id = get_jwt().get("studentId")
    reports = ReportCard.query.filter_by(student_id=student_id, status="Published").order_by(ReportCard.published_at.desc()).all()
    return jsonify({"items": [report_payload(item) for item in reports], **period_options()})


@report_cards_bp.get("/parent/report/<int:student_id>")
@jwt_required()
@roles_required("Parent")
def parent_report(student_id):
    if get_jwt().get("studentId") != student_id:
        return jsonify({"error": "You can only view reports for your own child."}), 403
    term_id = request.args.get("termId", type=int)
    year_id = request.args.get("academicYearId", type=int)
    query = ReportCard.query.filter_by(student_id=student_id, status="Published")
    if term_id:
        query = query.filter_by(term_id=term_id)
    if year_id:
        query = query.filter_by(academic_year_id=year_id)
    report = query.order_by(ReportCard.published_at.desc()).first()
    return jsonify({"report": report_payload(report) if report else None})


def setting(key, default=None):
    item = SchoolSetting.query.filter_by(key=key).first()
    return item.value if item else default


def can_view_report(report):
    role = get_jwt().get("role")
    if role in {"Admin", "Super Admin"}:
        return True
    if role == "Parent":
        return get_jwt().get("studentId") == report.student_id and report.status == "Published"
    if role == "Teacher":
        teacher = current_teacher()
        return bool(teacher and report.student.school_class and report.student.school_class.teacher_id == teacher.id)
    return False


def report_pdf_buffer(report):
    navy = colors.HexColor("#08285c")
    border = colors.HexColor("#8090a8")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontSize=20, leading=24, textColor=navy, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="SectionHead", parent=styles["Heading3"], textColor=colors.white, backColor=navy, alignment=TA_CENTER, spaceAfter=0, leading=17))
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=14 * mm, leftMargin=14 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    story = []
    logo_path = setting("school_logo_path")
    school_name = setting("school_name", "EduTrack School")
    title = f"{report.student.first_name} {report.term.name} Report - {report.student.grade_form or (report.student.school_class.name if report.student.school_class else '')}"
    header_left = Image(logo_path, width=28 * mm, height=28 * mm) if logo_path and os.path.isfile(logo_path) else Paragraph("<b>EDUTRACK</b><br/>SCHOOL", styles["Heading2"])
    header = Table(
        [[header_left, Paragraph(f"<b>{escape(title)}</b><br/><font size='11'>{escape(school_name)}</font>", styles["ReportTitle"])]],
        colWidths=[35 * mm, 145 * mm],
    )
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (1, 0), (1, 0), 1.5, navy)]))
    story.extend([header, Spacer(1, 4 * mm)])
    info = [
        ["Student Name:", report.student.to_dict()["name"], "Registration:", report.student.registration_number],
        ["Form / Class:", report.student.school_class.name if report.student.school_class else report.student.grade_form or "-", "Academic Year:", report.academic_year.name],
        ["Term:", report.term.name, "Class Teacher:", report.class_teacher.to_dict()["name"] if report.class_teacher else "-"],
    ]
    info_table = Table(info, colWidths=[28 * mm, 62 * mm, 30 * mm, 60 * mm])
    info_table.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 0), (0, -1), navy), ("TEXTCOLOR", (2, 0), (2, -1), navy), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.extend([info_table, Spacer(1, 4 * mm)])
    result_rows = [["SUBJECT", "RESULT", "EFFORT"]]
    for result in report.to_dict()["results"]:
        result_rows.append([result["subject"]["name"], f'{result["finalMark"]:.0f}%', result["effortGrade"]])
    results_table = Table(result_rows, colWidths=[88 * mm, 43 * mm, 49 * mm], repeatRows=1)
    results_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), .6, border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fb")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([results_table, Spacer(1, 5 * mm)])
    teacher_comment = Table(
        [
            [Paragraph("CLASS TEACHER COMMENT", styles["SectionHead"])],
            [Paragraph(escape(report.teacher_comment or "-"), styles["BodyText"])],
        ],
        colWidths=[88 * mm],
    )
    teacher_comment.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .6, border), ("PADDING", (0, 1), (0, 1), 8)]))
    summary_data = [
        [Paragraph("SUMMARY", styles["SectionHead"]), ""],
        ["Overall Achievement:", report.overall_achievement or "-"],
        ["Attitude to Learning:", report.attitude_to_learning or "-"],
        ["Behaviour:", report.behaviour or "-"],
        ["Attendance:", report.attendance_summary or "-"],
    ]
    summary = Table(summary_data, colWidths=[50 * mm, 42 * mm])
    summary.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("GRID", (0, 0), (-1, -1), .6, border), ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"), ("PADDING", (0, 1), (-1, -1), 6)]))
    story.append(Table([[teacher_comment, summary]], colWidths=[88 * mm, 92 * mm], style=[("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(Spacer(1, 5 * mm))
    target_lines = "".join(f"&#8226;&nbsp; {escape(target)}<br/>" for target in report.to_dict()["targets"]) or "-"
    targets = Table([[Paragraph("NEXT TERM / NEXT YEAR TARGETS", styles["SectionHead"])], [Paragraph(target_lines, styles["BodyText"])]], colWidths=[180 * mm])
    targets.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .6, border), ("PADDING", (0, 1), (0, 1), 8)]))
    story.extend([targets, Spacer(1, 5 * mm)])
    signature_path = report.signature.signature_image if report.signature else None
    signature = Image(signature_path, width=35 * mm, height=12 * mm) if signature_path and os.path.isfile(signature_path) else Paragraph("<i>Digitally approved</i>", styles["BodyText"])
    approval = Table([
        ["Approved By:", report.approved_by.to_dict()["name"] if report.approved_by else "-", "Signature:", signature],
        ["Date Approved:", report.approved_at.strftime("%d %B %Y") if report.approved_at else "-", "Status:", report.status],
    ], colWidths=[28 * mm, 60 * mm, 25 * mm, 67 * mm])
    approval.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .5, border), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("PADDING", (0, 0), (-1, -1), 6)]))
    story.extend([KeepTogether(approval), Spacer(1, 5 * mm)])
    motto = setting("school_motto", "Learn - Grow - Succeed")
    contact = setting("school_contact", "")
    story.append(
        Paragraph(
            f"<b>{escape(motto)}</b><br/><font size='8'>{escape(contact)}</font>",
            ParagraphStyle(name="Footer", parent=styles["BodyText"], alignment=TA_CENTER, textColor=navy),
        )
    )
    doc.build(story)
    buffer.seek(0)
    return buffer


@report_cards_bp.get("/reports/<int:report_id>/pdf")
@jwt_required()
def report_pdf(report_id):
    report = db.session.get(ReportCard, report_id)
    if not report or not can_view_report(report):
        return jsonify({"error": "Report not found or access denied."}), 404
    return send_file(report_pdf_buffer(report), mimetype="application/pdf", as_attachment=True, download_name=f"{report.student.registration_number}-{report.term.name}-report.pdf")
