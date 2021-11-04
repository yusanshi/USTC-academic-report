import smtplib
import mimetypes
import os
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER, RECEIVERS
from time import sleep


def send_mail(title, body, attchments_path=None):
    if attchments_path is None:
        attchments_path = []
    for receiver in RECEIVERS:
        try:
            message = MIMEMultipart()
            message['From'] = SENDER
            message['To'] = receiver
            message['Subject'] = title
            message.attach(MIMEText(body))

            for attachment_path in attchments_path:
                ctype, encoding = mimetypes.guess_type(attachment_path)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"

                maintype, subtype = ctype.split("/", 1)

                if maintype == "text":
                    fp = open(attachment_path)
                    attachment = MIMEText(fp.read(), _subtype=subtype)
                    fp.close()
                elif maintype == "image":
                    fp = open(attachment_path, "rb")
                    attachment = MIMEImage(fp.read(), _subtype=subtype)
                    fp.close()
                elif maintype == "audio":
                    fp = open(attachment_path, "rb")
                    attachment = MIMEAudio(fp.read(), _subtype=subtype)
                    fp.close()
                else:
                    fp = open(attachment_path, "rb")
                    attachment = MIMEBase(maintype, subtype)
                    attachment.set_payload(fp.read())
                    fp.close()
                    encoders.encode_base64(attachment)
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(attachment_path))
                message.attach(attachment)

            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER, receiver, message.as_string())
            server.quit()
        except Exception as e:
            print(
                f"Sending failed: {e}\n[title]\n{title}\n[body]\n{body}\n[attachment]\n{', '.join(attchments_path)}"
            )
        sleep(10)


if __name__ == '__main__':
    send_mail('Hello from Mars', '来自火星的问候')
