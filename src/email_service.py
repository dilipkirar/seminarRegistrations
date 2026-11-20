import smtplib
from email.message import EmailMessage
from src.config import SENDER_EMAIL, APP_PASSWORD


def send_confirmation_email(name: str, recipient_email: str, seminar: dict) -> tuple[bool, str]:
    """
    Sends an official seminar confirmation pass via Gmail SMTP (SSL:465) with 10s timeout protection.
    """
    if not APP_PASSWORD or APP_PASSWORD == "YOUR_16_CHAR_GMAIL_APP_PASSWORD":
        return True, "Demo Mode: Email simulated (Gmail App Password not configured)."

    try:
        msg = EmailMessage()
        msg["Subject"] = f"CONFIRMED: Seminar Pass - {seminar['title']} ({seminar['id']})"
        msg["From"] = SENDER_EMAIL
        msg["To"] = f"{recipient_email}, {SENDER_EMAIL}"
        msg.set_content(
            f"Dear {name},\n\n"
            f"Your seminar registration has been successfully confirmed!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"OFFICIAL SEMINAR REGISTRATION PASS\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Registration ID : REG-2026-{seminar['id']}\n"
            f"• Seminar Title   : {seminar['title']}\n"
            f"• Scheduled Date  : {seminar['date']}\n"
            f"• Attendance Mode : {seminar['type']}\n"
            f"• Location        : {seminar['city']}, {seminar['state']} (India)\n"
            f"• University      : {seminar['university']}\n"
            f"• Attendee Name   : {name}\n"
            f"• Attendee Email  : {recipient_email}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Please present this email at the venue entrance or use your registered email for online login.\n\n"
            f"Warm regards,\n"
            f"AutoTrain AI Seminar Organizing Team\n"
            f"Support: {SENDER_EMAIL}\n"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)

        return True, f"Official confirmation pass successfully emailed to {recipient_email} and {SENDER_EMAIL}!"
    except Exception as e:
        return False, f"Registration recorded, but email dispatch error: {str(e)}"
