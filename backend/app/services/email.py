import smtplib
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
    except smtplib.SMTPAuthenticationError as error:
        current_app.logger.error("Password reset email authentication failed for %s: %s", username, error)
        raise RuntimeError("Email login failed. Check SMTP_USERNAME and the Gmail app password.") from error
    except smtplib.SMTPRecipientsRefused as error:
        current_app.logger.error("Password reset email recipient was refused for %s: %s", recipient, error)
        raise RuntimeError("The teacher email address was refused by the mail server.") from error
    except smtplib.SMTPSenderRefused as error:
        current_app.logger.error("Password reset email sender was refused for %s: %s", sender, error)
        raise RuntimeError("SMTP_FROM_EMAIL was refused. Use the Gmail account address or a verified alias.") from error
    except (OSError, smtplib.SMTPException) as error:
        current_app.logger.error("Password reset email delivery failed: %s", error)
        raise RuntimeError("Unable to send the email verification code.") from error
