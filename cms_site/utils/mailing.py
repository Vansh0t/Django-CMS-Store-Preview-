import smtplib, ssl
from cms_site.settings import cfg
from django.conf import settings

SMTP_SERVER = cfg['MAILING']['SMTP_SERVER']
PORT = int(cfg['MAILING']['PORT'])  
SENDER_EMAIL = cfg['MAILING']['SENDER_EMAIL']
PASSWORD = cfg['MAILING']['PASSWORD']





def send_email_confirmation(rec_email, url):
    
    if settings.SKIP_MAILING: 
        print('SKIP_MAILING is set to True. ABORTING SENDING.')
        return
    context = ssl.create_default_context()
    server = None
    try:
        server = smtplib.SMTP(SMTP_SERVER,PORT)
        server.starttls(context=context) 
        print(SENDER_EMAIL, PASSWORD)
        server.login(SENDER_EMAIL, PASSWORD)
        message = f"""\
Subject: Confirm Your Email

Confirm your email for website.com using the link below:
{url}

It will expire in 24 hours."""
        server.sendmail(SENDER_EMAIL, rec_email, message)
    except Exception as e:
        print(e)
    finally:
        if server:
            server.quit()

def send_password_reset(rec_email, url):
    if settings.SKIP_MAILING: 
        print('SKIP_MAILING is set to True. ABORTING SENDING.')
        return
    context = ssl.create_default_context()
    server = None
    try:
        server = smtplib.SMTP(SMTP_SERVER,PORT)
        server.starttls(context=context) 
        server.login(SENDER_EMAIL, PASSWORD)
        message = f"""\
Subject: Password Reset Requested

You got this message because password reset request has been acqured for your account. Use the link below to reset the password:

{url}

It will expire in 24 hours."""
        server.sendmail(SENDER_EMAIL, rec_email, message)
    except Exception as e:
        print(e)
    finally:
        if server:
            server.quit()