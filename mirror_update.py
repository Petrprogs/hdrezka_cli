""" 
    Module for refreshing HDrezka mirror link
"""
import re
import smtplib
import time
import json
from imapclient import IMAPClient

EMAIL = ""
EMAIL_PASSWORD = ""

SMTP_SERVER = ""
IMAP_SERVER = ""
IMAP_PORT = 993

MIRROR_EMAILS = ["mirror@hdrezka.org","mirror@hdrezka.ag",]

def update_mirror():
    """
        Function to update key "mirror_url" of "settings.json" file
    """
    smtp = smtplib.SMTP_SSL(SMTP_SERVER)
    try:
        print("\033[1;32;92m Logging to SMTP server... \033[1;32;92m")
        smtp.login(EMAIL, EMAIL_PASSWORD)
        print("\033[1;32;92m Login succesful! Sending email... \033[1;32;92m")
        smtp.sendmail(EMAIL, MIRROR_EMAILS[0], "Mirror")
        print("\033[1;32;92m Email sent succesfuly! \033[1;32;92m")
        smtp.close()
        server = IMAPClient(IMAP_SERVER,IMAP_PORT, use_uid=True)
        print("\033[1;32;92m Logging to IMAP server... \033[1;32;92m")
        server.login(EMAIL, EMAIL_PASSWORD)
        server.select_folder('INBOX', readonly=False)
        messages = server.search(['FROM', MIRROR_EMAILS[0]])
        print(f"\033[1;32;92m Waiting for email from {MIRROR_EMAILS[0]}... \033[1;32;92m")
        time.sleep(2)
        print(server.list_folders())
        while len(messages) == len(server.search(['FROM', MIRROR_EMAILS[0]])):
            time.sleep(3)
        messages = server.search(['FROM', MIRROR_EMAILS[0]])
        print("\033[1;32;92m Found email! \033[1;32;92m")
        email_regex = re.search(r'hdrezka[\d\w]+[.][org|net]{3}',
            str(server.fetch(messages, "RFC822")))
        server.move(messages,'Корзина')
        server.expunge()
        server.logout()
        settings_file = open("settings.json", "r+", encoding='utf-8')
        settings_json = json.load(settings_file)
        print(f"\033[1;32;92m Mirror link: {email_regex.group(0)} \033[1;32;92m")
        settings_json["mirror_link"] = email_regex.group(0)
        print("\033[1;32;92m Updating settings... \033[1;32;92m")
        settings_file.truncate(0)
        json.dump(settings_json, settings_file, indent=4)
        settings_file.close()
        print("\033[1;32;92m Settings updated succesfuly! \033[1;32;92m")
        print("\033[1;32;92m Email removed \033[1;32;92m")
    except smtplib.SMTPHeloError:
        print("\033[1;31;91m The server didn't reply properly to the helo greeting! \033[0m 1;31;92m")
        return False
    except smtplib.SMTPAuthenticationError:
        print("\033[1;31;91m The server didn't accept the username/password combination! \033[0m 1;31;92m")
        return False
    except smtplib.SMTPRecipientsRefused:
        print("\033[1;31;91m The server rejected ALL recipients! \033[0m 1;31;92m")
        return False
    except smtplib.SMTPException as ex:
        print(f"\033[1;31;91m Unknown SMTP exception! Message: {ex.strerror} \033[0m 1;31;92m")
        return False
    return True