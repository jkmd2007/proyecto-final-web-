"""Envío de correo. Sin MAIL_SERVER configurado solo escribe en el log."""

import smtplib
from email.message import EmailMessage

from flask import current_app


def send_mail(to, subject, body):

    server = current_app.config.get("MAIL_SERVER")

    if not server:
        current_app.logger.info("[CORREO SIMULADO] Para: %s | %s | %s", to, subject, body)
        return False

    message = EmailMessage()
    message["From"] = current_app.config["MAIL_SENDER"]
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(server, current_app.config["MAIL_PORT"], timeout=10) as smtp:
            if current_app.config.get("MAIL_USE_TLS"):
                smtp.starttls()
            if current_app.config.get("MAIL_USERNAME"):
                smtp.login(
                    current_app.config["MAIL_USERNAME"],
                    current_app.config["MAIL_PASSWORD"]
                )
            smtp.send_message(message)
        return True
    except Exception as error:
        current_app.logger.warning("No se pudo enviar el correo a %s: %s", to, error)
        return False
