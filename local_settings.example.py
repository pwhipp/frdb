from frdb.mail import MailConfig


MAIL_CONFIG = MailConfig(
    smtp_host="email-smtp.ap-southeast-2.amazonaws.com",
    username="replace-with-ses-smtp-username",
    password="replace-with-ses-smtp-password",
    sender="verified-sender@example.com",
)
