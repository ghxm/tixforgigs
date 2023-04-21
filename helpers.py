import  backoff
import  urllib
import urllib.error
import urllib.request
import time
import smtplib
from email.mime.text import MIMEText
import ssl
import config
import random

def random_sleep(low, high):
    time.sleep(random.randint(low,high))


# generates a random header for urllib
def random_header():
    agents = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.3'),
        ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/43.4'),
        ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'),
        ('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko)')
    ]
    return [random.choice(agents)] + [("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"),
                                       ("Accept-Language", "en-GB,en-US;q=0.9,en;q=0.8")]


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
        server.login(config.gmail_login, config.gmail_password)

        for recipient in to:

            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = 'mh.max.haag@googlemail.com'

            server.sendmail(sender, recipient, msg.as_string())


def event_url(id, lang="en-gb"):
    return 'https://www.tixforgigs.com/' + lang + '/Event/' + str(id)

def resale_url(id, lang = "en-gb"):
    return 'https://www.tixforgigs.com/' + lang + '/Resale/' + str(id)
