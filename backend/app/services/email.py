import smtplib
import threading
from email.message import EmailMessage

from flask import current_app


def send_password_reset_code(recipient, code):
    host = current_app.config["SMTP_HOST"]
    port = current_app.config["SMTP_PORT"]
    username = current_app.config["SMTP_USERNAME"]
    password = current_app.config["SMTP_PASSWORD"]
    sender = current_app.config["SMTP_FROM_EMAIL"] or username
    if not host or not username or not password or not sender:
        raise RuntimeError("Email password reset is not configured.")

    message = EmailMessage()
    message["Subject"] = "EduTrack teacher password verification code"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "Your EduTrack password verification code is:\n\n"
        f"{code}\n\n"
        "This code expires in 10 minutes. If you did not request a password "
        "reset, you can ignore this email."
    )

    try:
        if current_app.config["SMTP_USE_SSL"]:
            smtp = smtplib.SMTP_SSL(host, port, timeout=current_app.config["SMTP_TIMEOUT"])
        else:
            smtp = smtplib.SMTP(host, port, timeout=current_app.config["SMTP_TIMEOUT"])
        with smtp:
            smtp.ehlo()
            if current_app.config["SMTP_USE_TLS"] and not current_app.config["SMTP_USE_SSL"]:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(username, password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        current_app.logger.error("Password reset email delivery failed: %s", error)
        raise RuntimeError("Unable to send the email verification code.") from error


def send_password_reset_code_async(recipient, code):
    app = current_app._get_current_object()

    def deliver():
        with app.app_context():
            try:
                send_password_reset_code(recipient, code)
            except RuntimeError:
                app.logger.exception("Asynchronous password reset email delivery failed.")

    threading.Thread(target=deliver, name="password-reset-email", daemon=True).start()
