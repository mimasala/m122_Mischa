from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, Content)


# send email with attachment
def send_email(email, subject, message, api_key, Attachments=None):
    mailMessage = Mail(
        from_email='mytallmusic@gmail.com',
        to_emails=email,
        subject=subject,
        html_content=message,
    )
    if Attachments:
        for attachment in Attachments:
            mailMessage.add_attachment(attachment)
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(mailMessage)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)

