import time
import pickle
import base64
import os.path
import datetime
import mimetypes

from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.utils import parsedate_tz, mktime_tz

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from pprint import pprint as pp

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

def getService():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    s = build('gmail', 'v1', credentials=creds)
    return s

def getProfile(service, userId='me'):
    profile = service.users().getProfile(userId=userId).execute()
    return profile

def getInbox(service, userId='me'):
    msgList = service.users().messages().list(userId=userId, labelIds='INBOX', maxResults=10).execute()
    messages = msgList.get('messages', [])
    res = []
    if messages:
        for message in messages:
            msg = service.users().messages().get(userId=userId, id=message['id'], format='metadata', metadataHeaders=['Subject', 'From', 'Date']).execute()
            temp = {}
            temp[u'id'] = msg['id']
            temp[u'Snippet'] = msg['snippet']
            for m in msg['payload']['headers']:
                temp[m['name']] = m['value']

            email_ts = mktime_tz(parsedate_tz(temp[u'Date']))
            today_str = time.strftime("%m/%d/%Y") + " 00:00:00"
            today_ts = int(time.mktime(time.strptime(today_str,"%m/%d/%Y %H:%M:%S")))
            et = datetime.datetime.fromtimestamp(email_ts)
            # if email kemarin tampilin Mmm dd else tampilin hh:mm
            temp[u'Date'] = et.strftime('%b %d' if email_ts < today_ts else '%H:%M')

            res.append(temp)
    return res

def getDetailInbox(service, msgId, userId='me'):
    msg = service.users().messages().get(userId=userId, id=msgId).execute()
    return msg

def sendEmail(service, message, userId='me'):
    message = service.users().messages().send(userId=userId, body=message).execute()
    return message

def createMessage(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def createMessageWithAttachment(sender, to, subject, message_text, file_dir, filename):
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    path = os.path.join(file_dir, filename)
    content_type, encoding = mimetypes.guess_type(path)

    main_type, sub_type = None, None
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(path, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(path, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(path, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()

    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_string())}
