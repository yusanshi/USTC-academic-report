import smtplib

from email.mime.text import MIMEText
from email.header import Header
from config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER, RECEIVERS
from time import sleep


def send_mail(title, body):
    for receiver in RECEIVERS:
        try:
            message = MIMEText(body, 'plain', 'utf-8')
            message['From'] = SENDER
            message['To'] = receiver
            message['Subject'] = Header(title, 'utf-8')

            smtpObj = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
            smtpObj.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtpObj.sendmail(SENDER, [receiver], message.as_string())
            smtpObj.quit()
        except Exception as e:
            print(f'Sending failed: {e}\n[title]\n{title}\n[body]\n{body}')
        sleep(10)


if __name__ == '__main__':
    send_mail('Hello from Mars', '来自火星的问候')
