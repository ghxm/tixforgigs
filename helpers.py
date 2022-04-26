import  backoff
import  urllib
import urllib.error
import urllib.request
import time
import smtplib
from email.mime.text import MIMEText
import ssl
import config


def fatal_code(e):
    try:
        return 400 <= e.code < 500 and e.code not in [408, 401, 409, 405, 503, 500]
    except:
        return False


@backoff.on_exception(backoff.expo, urllib.error.HTTPError, giveup=fatal_code, max_time=60*3)
def url_open(url, headers=[], retry_with_ip_switch=False):
    time.sleep(0.01)
    opener = urllib.request.build_opener()
    opener.addheaders = headers

    return opener.open(url)

def send_mail(subject, body, to, sender):
    port = 465  # For SSL

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(gmail_login, gmail_password)

        for recipient in to:

            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = 'mh.max.haag@googlemail.com'

            server.sendmail(sender, recipient, msg.as_string())

