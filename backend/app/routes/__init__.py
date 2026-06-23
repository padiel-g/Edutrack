from app.routes.analytics import analytics_bp
from app.routes.admin_classes import admin_classes_bp
from app.routes.admin_students import admin_students_bp
from app.routes.admin_teachers import admin_teachers_bp
from app.routes.attendance import attendance_bp
from app.routes.auth import auth_bp
from app.routes.crud import crud_bp
from app.routes.finance import finance_bp
from app.routes.exam_timetables import exam_timetables_bp
from app.routes.pdfs import pdf_bp
from app.routes.teacher_subjects import teacher_subjects_bp
from app.routes.learning_materials import learning_materials_bp
from app.routes.announcements import announcements_bp
from app.routes.portal_timetables import portal_timetables_bp
from app.routes.payment_workflow import accounts_payments_bp, admin_payments_bp, parent_payments_bp
from app.routes.report_cards import report_cards_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_classes_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_students_bp, url_prefix="/api/admin")
    app.register_blueprint(admin_teachers_bp, url_prefix="/api/admin")
    app.register_blueprint(finance_bp, url_prefix="/api/finance")
    app.register_blueprint(exam_timetables_bp, url_prefix="/api/exam-timetables")
    app.register_blueprint(crud_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api/dashboard")
    app.register_blueprint(pdf_bp, url_prefix="/api/pdf")
    app.register_blueprint(teacher_subjects_bp, url_prefix="/api/teacher")
    app.register_blueprint(learning_materials_bp, url_prefix="/api/teacher/learning-materials")
    app.register_blueprint(attendance_bp, url_prefix="/api")
    app.register_blueprint(announcements_bp, url_prefix="/api/announcements")
    app.register_blueprint(portal_timetables_bp, url_prefix="/api/portal/timetables")
    app.register_blueprint(accounts_payments_bp, url_prefix="/api/accounts")
    app.register_blueprint(parent_payments_bp, url_prefix="/api/parents")
    app.register_blueprint(admin_payments_bp, url_prefix="/api/admin")
    app.register_blueprint(report_cards_bp, url_prefix="/api")
