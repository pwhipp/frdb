from frdb.mail import MailConfig


MAIL_CONFIG = MailConfig(
    smtp_host='email-smtp.replace_with_real.com',
    username="replace-with-ses-smtp-username",
    password="replace-with-ses-smtp-password",
    sender="verified-sender@example.com",
)
