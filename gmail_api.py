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
from base64 import urlsafe_b64decode as bd

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
    res = service.users().messages().get(userId=userId, id=msgId).execute()
    msg = {}

    res = res['payload']
    for m in res['headers']:
        msg[m['name']] = m['value']

    # process timestamp
    et = mktime_tz(parsedate_tz(msg[u'Date']))
    et = datetime.datetime.fromtimestamp(et)
    msg[u'Date'] = et.strftime('%a, %d %b %Y %I:%M %p')

    # process body
    msg['Attachments'] = []
    if 'parts' in res:
        for m in res['parts']:
            if m['filename']:
                getAttachments(service, 'me', msgId, m['body']['attachmentId'], m['filename'])
                msg['Attachments'].append(m['filename'])
            else:
                if m['mimeType'] == 'text/plain' or m['mimeType'] == 'text/html':
                    msg[u'body'] = (bd(str(m['body']['data']))).decode('utf-8')
                if m['mimeType'] == 'multipart/alternative':
                    for n in m['parts']:
                        if n['mimeType'] == 'text/plain' or n['mimeType'] == 'text/html':
                            msg[u'body'] = (bd(str(n['body']['data']))).decode('utf-8')
    else:
        msg[u'body'] = (bd(str(res['body']['data']))).decode('utf-8')
    # process from
    msg[u'From'] = msg[u'From'].split(' ')
    if len(msg[u'From']) > 1:
        msg[u'FromName'] = ' '.join(msg[u'From'][:-1])
        msg[u'FromEmail'] = msg[u'From'][-1]
    else:
        msg[u'FromName'] = msg[u'From'][0]
        msg[u'FromEmail'] = msg[u'From'][0]
    return msg

def sendEmail(service, message, userId='me'):
    message = service.users().messages().send(userId=userId, body=message).execute()
    return message

def createMessage(to, subject, message_text):
    message = MIMEText(message_text)
    message['To'] = to
    message['Subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def createMessageWithAttachment(to, subject, message_text, file_dir, filename):
    message = MIMEMultipart()
    message['To'] = to
    message['Subject'] = subject

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

    return {'raw': base64.urlsafe_b64encode(message.as_string()).decode()}

def getAttachments(service, user_id, msg_id, id_, filename):
    message = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=id_).execute()
    if 'data' in message:
        file_data = bd(message['data'].encode('UTF-8'))
        path = ''.join(['static/output/', filename])
        f = open(path, 'w')
        f.write(file_data)
        f.close()
