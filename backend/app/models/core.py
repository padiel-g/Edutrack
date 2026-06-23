from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)

parent_students = db.Table(
    "parent_students",
    db.Column("parent_id", db.Integer, db.ForeignKey("parents.id"), primary_key=True),
    db.Column("student_id", db.Integer, db.ForeignKey("students.id"), primary_key=True),
)

teacher_subjects = db.Table(
    "teacher_subjects",
    db.Column("id", db.Integer, primary_key=True),
    db.Column("teacher_id", db.Integer, db.ForeignKey("teachers.id"), nullable=False, index=True),
    db.Column("subject_id", db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True),
    db.Column("class_id", db.Integer, db.ForeignKey("classes.id"), nullable=True),
    db.Column("academic_year_id", db.Integer, db.ForeignKey("academic_years.id"), nullable=True, index=True),
    db.Column("term_id", db.Integer, db.ForeignKey("terms.id"), nullable=True, index=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow, nullable=False),
    db.Column("updated_at", db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
    db.UniqueConstraint("teacher_id", "subject_id", "class_id", "academic_year_id", name="uq_teacher_subject_class_year"),
)

class_subjects = db.Table(
    "class_subjects",
    db.Column("class_id", db.Integer, db.ForeignKey("classes.id"), primary_key=True),
    db.Column("subject_id", db.Integer, db.ForeignKey("subjects.id"), primary_key=True),
)

teacher_classes = db.Table(
    "teacher_classes",
    db.Column("teacher_id", db.Integer, db.ForeignKey("teachers.id"), primary_key=True),
    db.Column("class_id", db.Integer, db.ForeignKey("classes.id"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow, nullable=False),
)


class StudentSubject(db.Model):
    __tablename__ = "student_subjects"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    student = db.relationship("Student", back_populates="student_subjects")
    subject = db.relationship("Subject")
    __table_args__ = (db.UniqueConstraint("student_id", "subject_id", name="uq_student_subject"),)


class Role(TimestampMixin, db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    permissions = db.relationship("Permission", secondary=role_permissions, back_populates="roles")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "permissions": [p.name for p in self.permissions]}


class Permission(TimestampMixin, db.Model):
    __tablename__ = "permissions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    roles = db.relationship("Role", secondary=role_permissions, back_populates="permissions")


class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(40))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(20), default="Active", nullable=False, index=True)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False, index=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True, index=True)
    token_version = db.Column(db.Integer, default=0, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False, index=True)
    role = db.relationship("Role", foreign_keys=[role_id])
    __table_args__ = (db.Index("ix_users_created_at", "created_at"),)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "name": f"{self.first_name} {self.last_name}",
            "role": self.role.name if self.role else None,
            "permissions": [p.name for p in self.role.permissions] if self.role else [],
            "isActive": self.is_active,
            "status": self.status,
            "mustChangePassword": self.must_change_password,
            "lastLoginAt": self.last_login_at.isoformat() if self.last_login_at else None,
            "passwordChangedAt": self.password_changed_at.isoformat() if self.password_changed_at else None,
        }


class PasswordResetCode(db.Model):
    __tablename__ = "password_reset_codes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    code_hash = db.Column(db.String(255), nullable=False)
    reset_token_hash = db.Column(db.String(255), nullable=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = db.relationship("User")


class SchoolClass(TimestampMixin, db.Model):
    __tablename__ = "classes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, index=True)
    grade_level = db.Column(db.String(80), nullable=False, index=True)
    stream = db.Column(db.String(80), nullable=True, index=True)
    capacity = db.Column(db.Integer, default=35)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=True, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    subjects = db.relationship("Subject", secondary=class_subjects, back_populates="classes")
    class_teacher = db.relationship("Teacher", foreign_keys=[teacher_id])
    academic_year = db.relationship("AcademicYear")
    assigned_teachers = db.relationship(
        "Teacher",
        secondary=teacher_classes,
        viewonly=True,
        order_by="Teacher.last_name, Teacher.first_name",
    )

    __table_args__ = (
        db.UniqueConstraint("name", "academic_year_id", name="uq_class_name_academic_year"),
        db.Index("ix_classes_created_at", "created_at"),
    )

    def to_dict(self):
        class_teacher = None
        if self.class_teacher:
            class_teacher = {
                "id": self.class_teacher.id,
                "name": " ".join(
                    part for part in [self.class_teacher.first_name, self.class_teacher.middle_name, self.class_teacher.last_name] if part
                ),
                "employeeNumber": self.class_teacher.employee_number,
                "email": self.class_teacher.email,
            }
        return {
            "id": self.id,
            "name": self.name,
            "gradeLevel": self.grade_level,
            "stream": self.stream,
            "capacity": self.capacity,
            "academicYearId": self.academic_year_id,
            "academicYear": self.academic_year.name if self.academic_year else None,
            "classTeacherId": self.teacher_id,
            "classTeacher": class_teacher,
            "studentCount": len(self.students),
            "teachers": [
                {
                    "id": teacher.id,
                    "name": " ".join(
                        part for part in [teacher.first_name, teacher.middle_name, teacher.last_name] if part
                    ),
                    "employeeNumber": teacher.employee_number,
                }
                for teacher in self.assigned_teachers
            ],
            "subjects": [subject.to_dict() for subject in self.subjects],
        }


class Student(TimestampMixin, db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, index=True)
    registration_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    admission_number = db.Column(db.String(60), unique=True, nullable=True, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    middle_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    birth_certificate_number = db.Column(db.String(80), index=True)
    national_id = db.Column(db.String(80), index=True)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(40))
    email = db.Column(db.String(160), index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True, index=True)
    class_type = db.Column(db.String(80), nullable=True, index=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=True, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("parents.id"), nullable=True, index=True)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.String(30), default="active", nullable=False, index=True)
    grade_form = db.Column(db.String(40), nullable=True, index=True)
    class_stream = db.Column(db.String(60), nullable=True, index=True)
    number_of_subjects = db.Column(db.Integer, nullable=True)
    parent_password_hash = db.Column(db.String(255), nullable=True)
    parent_must_change_password = db.Column(db.Boolean, default=True, nullable=False)
    parent_failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    parent_locked_until = db.Column(db.DateTime, nullable=True, index=True)
    parent_token_version = db.Column(db.Integer, default=0, nullable=False)
    user = db.relationship("User", foreign_keys=[user_id])
    school_class = db.relationship("SchoolClass", backref="students")
    academic_year = db.relationship("AcademicYear")
    primary_parent = db.relationship("Parent", foreign_keys=[parent_id])
    parents = db.relationship("Parent", secondary=parent_students, back_populates="children")
    student_subjects = db.relationship("StudentSubject", back_populates="student", cascade="all, delete-orphan")
    __table_args__ = (db.Index("ix_students_created_at", "created_at"),)

    def set_parent_password(self, password):
        self.parent_password_hash = generate_password_hash(password)

    def check_parent_password(self, password):
        return bool(self.parent_password_hash) and check_password_hash(self.parent_password_hash, password)

    def to_dict(self):
        full_name = " ".join([p for p in [self.first_name, self.middle_name, self.last_name] if p])
        return {
            "id": self.id,
            "userId": self.user_id,
            "registrationNumber": self.registration_number,
            "admissionNumber": self.admission_number or self.registration_number,
            "firstName": self.first_name,
            "middleName": self.middle_name,
            "lastName": self.last_name,
            "name": full_name,
            "gender": self.gender,
            "dateOfBirth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "birthCertificateNumber": self.birth_certificate_number,
            "nationalId": self.national_id,
            "classId": self.class_id,
            "class": self.school_class.name if self.school_class else None,
            "classType": self.class_type,
            "academicYearId": self.academic_year_id,
            "parentId": self.parent_id,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "enrollmentDate": self.enrollment_date.isoformat() if self.enrollment_date else None,
            "status": self.status,
            "gradeForm": self.grade_form,
            "classStream": self.class_stream,
            "numberOfSubjects": self.number_of_subjects,
            "parentMustChangePassword": self.parent_must_change_password,
            "subjects": [link.subject.to_dict() for link in self.student_subjects if link.subject],
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class Parent(TimestampMixin, db.Model):
    __tablename__ = "parents"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, index=True)
    occupation = db.Column(db.String(120))
    relationship = db.Column(db.String(60), default="Guardian")
    user = db.relationship("User", foreign_keys=[user_id])
    children = db.relationship("Student", secondary=parent_students, back_populates="parents")
    __table_args__ = (db.Index("ix_parents_created_at", "created_at"),)

    def to_dict(self):
        return {"id": self.id, "name": self.user.to_dict()["name"], "children": [c.admission_number for c in self.children]}


class Teacher(TimestampMixin, db.Model):
    __tablename__ = "teachers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, index=True)
    employee_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    middle_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(20))
    national_id = db.Column(db.String(80), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(40))
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    address = db.Column(db.String(255))
    qualification = db.Column(db.String(160))
    department = db.Column(db.String(120))
    specialization = db.Column(db.String(160))
    hire_date = db.Column(db.Date)
    employment_status = db.Column(db.String(30), default="Active", nullable=False, index=True)
    user = db.relationship("User", foreign_keys=[user_id])
    subjects = db.relationship("Subject", secondary=teacher_subjects, back_populates="teachers")
    assigned_classes = db.relationship(
        "SchoolClass",
        secondary=teacher_classes,
        order_by="SchoolClass.name",
    )
    class_teacher_classes = db.relationship(
        "SchoolClass",
        foreign_keys="SchoolClass.teacher_id",
        viewonly=True,
        order_by="SchoolClass.name",
    )
    __table_args__ = (db.Index("ix_teachers_created_at", "created_at"),)

    def to_dict(self):
        # Classes the teacher is assigned to teach. Primary source is the
        # teacher_classes association; we also union in any classes inferred
        # from teacher_subjects to keep historical data visible.
        class_rows = list(self.assigned_classes)
        assignment_rows = db.session.execute(
            db.select(
                teacher_subjects.c.class_id,
                teacher_subjects.c.subject_id,
                SchoolClass.name.label("class_name"),
                Subject.code.label("subject_code"),
                Subject.name.label("subject_name"),
            )
            .join(SchoolClass, SchoolClass.id == teacher_subjects.c.class_id)
            .join(Subject, Subject.id == teacher_subjects.c.subject_id)
            .where(teacher_subjects.c.teacher_id == self.id)
            .order_by(SchoolClass.name, Subject.name)
        ).all()
        return {
            "id": self.id,
            "userId": self.user_id,
            "employeeNumber": self.employee_number,
            "firstName": self.first_name,
            "middleName": self.middle_name,
            "lastName": self.last_name,
            "name": " ".join(part for part in [self.first_name, self.middle_name, self.last_name] if part),
            "gender": self.gender,
            "nationalId": self.national_id,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "qualification": self.qualification,
            "department": self.department,
            "specialization": self.specialization,
            "hireDate": self.hire_date.isoformat() if self.hire_date else None,
            "employmentStatus": self.employment_status,
            "status": self.user.status if self.user else None,
            "mustChangePassword": self.user.must_change_password if self.user else None,
            "subjects": [subject.to_dict() for subject in self.subjects],
            "classes": [{"id": row.id, "name": row.name} for row in class_rows],
            "assignments": [
                {
                    "classId": row.class_id,
                    "subjectId": row.subject_id,
                    "className": row.class_name,
                    "subjectCode": row.subject_code,
                    "subjectName": row.subject_name,
                }
                for row in assignment_rows
            ],
            "classTeacherOf": [
                {"id": cls.id, "name": cls.name}
                for cls in self.class_teacher_classes
            ],
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class Subject(TimestampMixin, db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    stream = db.Column(db.String(60), nullable=True, index=True)
    teachers = db.relationship("Teacher", secondary=teacher_subjects, back_populates="subjects")
    classes = db.relationship("SchoolClass", secondary=class_subjects, back_populates="subjects")

    def to_dict(self):
        return {"id": self.id, "code": self.code, "name": self.name, "stream": self.stream}


class AcademicYear(TimestampMixin, db.Model):
    __tablename__ = "academic_years"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False, index=True)


class Term(TimestampMixin, db.Model):
    __tablename__ = "terms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False, index=True)
    academic_year = db.relationship("AcademicYear", backref="terms")


class Timetable(TimestampMixin, db.Model):
    __tablename__ = "timetables"
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False, index=True)
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    school_class = db.relationship("SchoolClass")
    subject = db.relationship("Subject")
    teacher = db.relationship("Teacher")

    def to_dict(self):
        return {
            "id": self.id,
            "classId": self.class_id,
            "class": self.school_class.to_dict() if self.school_class else None,
            "subjectId": self.subject_id,
            "subject": self.subject.to_dict() if self.subject else None,
            "teacherId": self.teacher_id,
            "teacher": {
                "id": self.teacher.id,
                "name": self.teacher.to_dict()["name"],
                "employeeNumber": self.teacher.employee_number,
            } if self.teacher else None,
            "dayOfWeek": self.day_of_week,
            "startTime": self.start_time.strftime("%H:%M"),
            "endTime": self.end_time.strftime("%H:%M"),
        }


class ExamTimetable(TimestampMixin, db.Model):
    __tablename__ = "exam_timetables"
    id = db.Column(db.Integer, primary_key=True)
    exam_date = db.Column(db.Date, nullable=False, index=True)
    class_type = db.Column(db.String(80), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(120))
    paper = db.Column(db.String(120))
    notes = db.Column(db.String(255))
    subject = db.relationship("Subject")

    def to_dict(self):
        return {
            "id": self.id,
            "examDate": self.exam_date.isoformat(),
            "classType": self.class_type,
            "subjectId": self.subject_id,
            "subject": self.subject.to_dict() if self.subject else None,
            "startTime": self.start_time.strftime("%H:%M"),
            "endTime": self.end_time.strftime("%H:%M"),
            "venue": self.venue,
            "paper": self.paper,
            "notes": self.notes,
        }


class Attendance(TimestampMixin, db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, index=True)
    notes = db.Column(db.String(255))
    student = db.relationship("Student")
    school_class = db.relationship("SchoolClass")
    teacher = db.relationship("Teacher")
    __table_args__ = (db.UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),)


class ClassRegister(TimestampMixin, db.Model):
    __tablename__ = "class_registers"
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    school_class = db.relationship("SchoolClass")
    teacher = db.relationship("Teacher")
    __table_args__ = (db.UniqueConstraint("class_id", "date", name="uq_register_class_date"),)

    @property
    def is_locked(self):
        return self.submitted_at is not None


class ContinuousAssessment(TimestampMixin, db.Model):
    __tablename__ = "continuous_assessments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False, index=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Numeric(6, 2), nullable=False)
    max_score = db.Column(db.Numeric(6, 2), nullable=False, default=100)


class ExamResult(TimestampMixin, db.Model):
    __tablename__ = "exam_results"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False, index=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=False, index=True)
    score = db.Column(db.Numeric(6, 2), nullable=False)
    grade = db.Column(db.String(5))
    teacher_comment = db.Column(db.String(255))


class FinalResult(TimestampMixin, db.Model):
    __tablename__ = "final_results"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False, index=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=False, index=True)
    average_score = db.Column(db.Numeric(6, 2), nullable=False)
    position = db.Column(db.Integer)
    status = db.Column(db.String(20), nullable=False)


class StudentResult(TimestampMixin, db.Model):
    __tablename__ = "student_results"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False, index=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=False, index=True)
    ca_mark = db.Column(db.Numeric(6, 2), nullable=False)
    exam_mark = db.Column(db.Numeric(6, 2), nullable=False)
    final_mark = db.Column(db.Numeric(6, 2), nullable=False)
    effort_grade = db.Column(db.String(40), nullable=False)
    student = db.relationship("Student")
    subject = db.relationship("Subject")
    teacher = db.relationship("Teacher")
    school_class = db.relationship("SchoolClass")
    term = db.relationship("Term")
    academic_year = db.relationship("AcademicYear")
    __table_args__ = (
        db.UniqueConstraint(
            "student_id", "subject_id", "term_id", "academic_year_id",
            name="uq_student_result_period_subject",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "studentId": self.student_id,
            "student": self.student.to_dict() if self.student else None,
            "subjectId": self.subject_id,
            "subject": self.subject.to_dict() if self.subject else None,
            "teacherId": self.teacher_id,
            "teacher": self.teacher.to_dict()["name"] if self.teacher else None,
            "classId": self.class_id,
            "termId": self.term_id,
            "term": self.term.name if self.term else None,
            "academicYearId": self.academic_year_id,
            "academicYear": self.academic_year.name if self.academic_year else None,
            "caMark": float(self.ca_mark),
            "examMark": float(self.exam_mark),
            "finalMark": float(self.final_mark),
            "effortGrade": self.effort_grade,
        }


class Assignment(TimestampMixin, db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False, index=True)
    due_date = db.Column(db.DateTime, nullable=False)


class Submission(TimestampMixin, db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    file_url = db.Column(db.String(255))
    score = db.Column(db.Numeric(6, 2))
    feedback = db.Column(db.String(255))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class LearningMaterial(TimestampMixin, db.Model):
    __tablename__ = "learning_materials"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    file_url = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=True, unique=True)
    original_filename = db.Column(db.String(255), nullable=True)
    mime_type = db.Column(db.String(120), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False, index=True)
    subject = db.relationship("Subject")
    teacher = db.relationship("Teacher")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "subjectId": self.subject_id,
            "subject": self.subject.to_dict() if self.subject else None,
            "teacherId": self.teacher_id,
            "teacherName": self.teacher.to_dict()["name"] if self.teacher else None,
            "originalFilename": self.original_filename,
            "mimeType": self.mime_type,
            "fileSize": self.file_size,
            "downloadUrl": f"/teacher/learning-materials/{self.id}/download",
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class Invoice(TimestampMixin, db.Model):
    __tablename__ = "invoices"
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    fee_account_id = db.Column(db.Integer, db.ForeignKey("student_fee_accounts.id"), nullable=True, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False, index=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=True, index=True)
    issue_date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), default="Unpaid", nullable=False, index=True)
    student = db.relationship("Student", backref="invoices")
    fee_account = db.relationship("StudentFeeAccount", backref="invoices")
    payments = db.relationship("Payment", back_populates="invoice")
    items = db.relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    __table_args__ = (db.Index("ix_invoices_created_at", "created_at"),)

    def to_dict(self):
        return {
            "id": self.id,
            "invoiceNumber": self.invoice_number,
            "studentId": self.student_id,
            "student": self.student.to_dict() if self.student else None,
            "amount": float(self.amount or 0),
            "paidAmount": float(self.paid_amount or 0),
            "balance": float(self.balance or 0),
            "dueDate": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
        }


class StudentFeeAccount(TimestampMixin, db.Model):
    __tablename__ = "student_fee_accounts"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), unique=True, nullable=False, index=True)
    account_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=True, index=True)
    total_fee = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total_paid = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    opening_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    current_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(30), default="Unpaid", nullable=False, index=True)
    student = db.relationship("Student", backref=db.backref("fee_account", uselist=False))
    term = db.relationship("Term")

    def to_dict(self):
        return {
            "id": self.id,
            "studentId": self.student_id,
            "accountNumber": self.account_number,
            "termId": self.term_id,
            "term": self.term.name if self.term else None,
            "totalFee": float(self.total_fee or 0),
            "totalPaid": float(self.total_paid or 0),
            "currentBalance": float(self.current_balance or 0),
            "status": self.status,
            "student": self.student.to_dict() if self.student else None,
        }


class FeeStructure(TimestampMixin, db.Model):
    __tablename__ = "fee_structures"
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=False, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class InvoiceItem(TimestampMixin, db.Model):
    __tablename__ = "invoice_items"
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False, index=True)
    description = db.Column(db.String(180), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_amount = db.Column(db.Numeric(12, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    invoice = db.relationship("Invoice", back_populates="items")


class Payment(TimestampMixin, db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    payment_reference = db.Column(db.String(80), unique=True, nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    fee_account_id = db.Column(db.Integer, db.ForeignKey("student_fee_accounts.id"), nullable=True, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=True, index=True)
    term_name = db.Column(db.String(80), nullable=True, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.String(40), nullable=False)
    reference_number = db.Column(db.String(100), nullable=True, index=True)
    note = db.Column(db.Text, nullable=True)
    previous_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    new_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    invoice = db.relationship("Invoice", back_populates="payments")
    student = db.relationship("Student", backref="payments")
    fee_account = db.relationship("StudentFeeAccount")
    term = db.relationship("Term")
    recorded_by = db.relationship("User", foreign_keys=[recorded_by_id])

    def to_dict(self):
        return {
            "id": self.id, "paymentReference": self.payment_reference, "referenceNumber": self.reference_number,
            "invoiceId": self.invoice_id, "studentId": self.student_id, "feeAccountId": self.fee_account_id,
            "termId": self.term_id, "term": self.term.name if self.term else self.term_name,
            "amount": float(self.amount or 0), "method": self.method, "note": self.note,
            "previousBalance": float(self.previous_balance or 0), "newBalance": float(self.new_balance or 0),
            "paidAt": self.paid_at.isoformat() if self.paid_at else None,
            "student": self.student.to_dict() if self.student else None,
            "recordedBy": self.recorded_by.to_dict()["name"] if self.recorded_by else None,
        }


class Receipt(TimestampMixin, db.Model):
    __tablename__ = "receipts"
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("payments.id"), nullable=False, unique=True, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    pdf_url = db.Column(db.String(255))
    issued_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    payment = db.relationship("Payment")
    student = db.relationship("Student")
    issued_by = db.relationship("User", foreign_keys=[issued_by_id])

    def to_dict(self):
        return {
            "id": self.id, "receiptNumber": self.receipt_number, "paymentId": self.payment_id,
            "studentId": self.student_id, "amount": float(self.amount or 0),
            "issuedAt": self.issued_at.isoformat() if self.issued_at else None,
            "issuedBy": self.issued_by.to_dict()["name"] if self.issued_by else None,
            "downloadUrl": f"/accounts/receipts/{self.id}/download",
        }


class FeeReminder(TimestampMixin, db.Model):
    __tablename__ = "fee_reminders"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True, index=True)
    message = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(40), default="email", nullable=False)
    status = db.Column(db.String(30), default="Queued", nullable=False, index=True)
    sent_at = db.Column(db.DateTime)
    student = db.relationship("Student")
    invoice = db.relationship("Invoice")


class Announcement(TimestampMixin, db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    audience = db.Column(db.String(80), default="all", index=True)
    target_id = db.Column(db.Integer, nullable=True, index=True)
    video_path = db.Column(db.String(255), nullable=True)
    video_filename = db.Column(db.String(255), nullable=True)
    video_mime_type = db.Column(db.String(120), nullable=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "audience": self.audience,
            "targetId": self.target_id,
            "hasVideo": bool(self.video_path),
            "videoFilename": self.video_filename,
            "publishedAt": self.published_at.isoformat() if self.published_at else None,
        }


class Message(TimestampMixin, db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    subject = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    read_at = db.Column(db.DateTime)


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(60), nullable=False, index=True)
    read_at = db.Column(db.DateTime)


class ReportCard(TimestampMixin, db.Model):
    __tablename__ = "report_cards"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False, index=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey("academic_years.id"), nullable=False, index=True)
    class_teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=True, index=True)
    teacher_comment = db.Column(db.Text, nullable=True)
    overall_achievement = db.Column(db.String(40), nullable=True)
    attitude_to_learning = db.Column(db.String(40), nullable=True)
    behaviour = db.Column(db.String(40), nullable=True)
    attendance_summary = db.Column(db.String(40), nullable=True)
    targets = db.Column(db.Text, nullable=True)
    admin_comment = db.Column(db.Text, nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    pdf_url = db.Column(db.String(255))
    status = db.Column(db.String(30), default="Draft", nullable=False, index=True)
    student = db.relationship("Student")
    term = db.relationship("Term")
    academic_year = db.relationship("AcademicYear")
    class_teacher = db.relationship("Teacher")
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])
    signature = db.relationship("ReportSignature", back_populates="report", uselist=False, cascade="all, delete-orphan")
    __table_args__ = (
        db.UniqueConstraint("student_id", "term_id", "academic_year_id", name="uq_report_card_student_period"),
        db.Index("ix_report_cards_created_at", "created_at"),
    )

    def to_dict(self, include_results=True):
        output = {
            "id": self.id,
            "studentId": self.student_id,
            "student": self.student.to_dict() if self.student else None,
            "termId": self.term_id,
            "term": self.term.name if self.term else None,
            "academicYearId": self.academic_year_id,
            "academicYear": self.academic_year.name if self.academic_year else None,
            "classTeacherId": self.class_teacher_id,
            "classTeacher": self.class_teacher.to_dict()["name"] if self.class_teacher else None,
            "teacherComment": self.teacher_comment,
            "overallAchievement": self.overall_achievement,
            "attitudeToLearning": self.attitude_to_learning,
            "behaviour": self.behaviour,
            "attendance": self.attendance_summary,
            "targets": [line.strip() for line in (self.targets or "").splitlines() if line.strip()],
            "adminComment": self.admin_comment,
            "approvedBy": self.approved_by.to_dict()["name"] if self.approved_by else None,
            "approvedAt": self.approved_at.isoformat() if self.approved_at else None,
            "publishedAt": self.published_at.isoformat() if self.published_at else None,
            "status": self.status,
            "downloadUrl": f"/reports/{self.id}/pdf",
        }
        if include_results:
            output["results"] = [
                item.to_dict()
                for item in StudentResult.query.filter_by(
                    student_id=self.student_id,
                    term_id=self.term_id,
                    academic_year_id=self.academic_year_id,
                ).join(Subject).order_by(Subject.name).all()
            ]
        return output


class ReportSignature(TimestampMixin, db.Model):
    __tablename__ = "report_signatures"
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("report_cards.id"), nullable=False, unique=True, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    signature_image = db.Column(db.String(255), nullable=True)
    report = db.relationship("ReportCard", back_populates="signature")
    admin = db.relationship("User", foreign_keys=[admin_id])


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(30), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=False, index=True)
    entity_id = db.Column(db.Integer, index=True)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class SchoolSetting(TimestampMixin, db.Model):
    __tablename__ = "school_settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)
