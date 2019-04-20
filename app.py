from flask import Flask, render_template, request, redirect, url_for

import re
import time
import os, json
from sha import SHA1
from gmail_api import *
from ecceg import ECCEG
from chill import Chill
from base64 import b64encode, b64decode

app = Flask(__name__)
app.config['ROOT_PATH'] = app.root_path

MARK_START = "---ayamayam---"
MARK_END = "---tokpetok---"

output_path = '/static/output/'
ecceg_ = ECCEG()
service = getService()

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/genkey", methods=['POST'])
def eccegGenKey():
    privKey, pubKey = ecceg_.generate_key()

    filepath = app.root_path + output_path
    with open(filepath + 'kunci.pub', 'w') as jf:
        json.dump({'public_key': pubKey}, jf)
    with open(filepath + 'kunci.pri', 'w') as jf:
        json.dump({'private_key': privKey}, jf)

    return json.dumps({
        'error': False,
        'pubKey': output_path + 'kunci.pub?' + str(time.time()),
        'priKey': output_path + 'kunci.pri?' + str(time.time()),
    })

@app.route("/inbox", methods=['GET'])
def inboxGET():
    inboxes = getInbox(service)
    return render_template('inbox.html', inboxes=inboxes)

@app.route("/inbox/<msgId>", methods=['GET'])
def detailInboxGET(msgId):
    inbox = getDetailInbox(service, msgId)
    return render_template('message.html', inbox=inbox)

@app.route("/send-email", methods=['GET'])
def sendEmailGET():
    return render_template('send.html')

@app.route("/send-email", methods=['POST'])
def sendEmailPOST():

    femail = request.form.get('femail')
    fsubject = request.form.get('fsubject')
    fbody = request.form.get('fbody')
    fkey = request.form.get('fkey')
    fattach, fsign = None, None

    if 'fattach' in request.files:
        fattach = request.files['fattach']
    if 'fsign' in request.files:
        fsign = request.files['fsign']

    filepath = app.root_path + output_path
    ret = {}

    if femail and fsubject and fbody:
        if fkey: # encrypt dulu
            ch = Chill(plain_text=fbody,
                       key=fkey,
                       mode='CBC',
                       cipher_text_path=filepath+'cipher.txt')
            ch.encrypt()
            fbody = b64encode(ch.cipher_text)
        if fsign: # sign dulu

            # hash dulu terus encrypt
            sha1 = SHA1()
            hs = sha1.do_hash(fbody.encode())

            # save and load private key
            fsign.save(filepath + 'kunci.pri')
            with open(filepath + 'kunci.pri', 'r') as f:
                fsign = json.load(f)

            priK = fsign['private_key']
            fsign = (priK[0], priK[1])
            sign, _ = ecceg_.encrypt(fsign, hs)

            ds = '\n'+MARK_START+b64encode(sign)+MARK_END
            fbody += ds

        if fattach: # createWithAttach
            # save and load attachfile
            filename = fattach.filename
            fattach.save(filepath + filename)

            print 'Sending with Attach'
            print '---'
            print 'From:', 'fahrurrozi31@gmail.com'
            print 'To:', femail
            print 'Subject:', fsubject
            print '---'
            print fbody
            print '---'
            print 'Attachment', filepath + filename
            msg = createMessageWithAttachment(femail, fsubject, fbody, filepath, filename)
        else: # biasa
            print 'Sending without Attach'
            print '---'
            print 'From:', 'fahrurrozi31@gmail.com'
            print 'To:', femail
            print 'Subject:', fsubject
            print '---'
            print fbody
            print '---'
            msg = createMessage(femail, fsubject, fbody)
        res = sendEmail(service, msg)
        if res['id']:
            return redirect(url_for('inboxGET'))
        else:
            ret['error'] = True
        return render_template('send.html', ret=ret)
    else:
        # error
        # TODO: improve ux
        ret['error'] = True
        ret['message'] = "Make sure email destination or subject or body not empty!"
    return render_template('send.html', ret=ret)

def isBase64(s):
    try:
        return b64encode(b64decode(s)) == s
    except Exception:
        return False

@app.route("/inbox/decrypt", methods=['POST'])
def decryptMessage():

    fkey = request.form.get('fkey')
    fbody = (request.form.get('fbody')).strip()
    print fkey
    print fbody

    if not fkey:
        return json.dumps({
            'error': True,
            'error_message': 'Key not found',
        })

    # check if hash exists
    res = re.search(MARK_START+"(.*)"+MARK_END, fbody)
    # fbody displit jadi fmsg dan fhash if hash exists
    fmsg = fbody.split(res.group(0))[0][:-1] if res else fbody

    # cek if fmsg is b64encoded
    if not isBase64(fmsg):
        return json.dumps({
            'error': True,
            'error_message': 'Message isn\'t encrypted',
        })

    ch = Chill(plain_text='dummy', key=fkey, mode='CBC')
    ch.cipher_text = b64decode(fmsg)
    ch.decrypt()
    
    return json.dumps({
        'error': False,
        'plaintext': ch.plain_text,
        'sign': MARK_START+res.group(1)+MARK_END if res else ''
    })

@app.route("/inbox/verify", methods=['POST'])
def verifySignature():
    
    fbody = (request.form.get('fbody')).strip()
    if 'fsign' in request.files:
        fsign = request.files['fsign']
    else:
        return json.dumps({
            'error': True,
            'correct': False,
            'error_message': 'Public key not found'
        })
    
    # check if hash exists
    res = re.search(MARK_START+"(.*)"+MARK_END, fbody)
    if res:
        # fbody displit jadi fmsg dan fhash
        fmsg = (fbody.split(res.group(0))[0]).strip()
        fhash = res.group(1)
    else:
        return json.dumps({
            'error': True,
            'correct': False,
            'error_message': 'Signature not found'
        })

    sha1 = SHA1()
    fmsg_hash = sha1.do_hash(fmsg.encode())

    # save and load public key
    filepath = app.root_path + output_path
    fsign.save(filepath + 'kunci.pub')
    with open(filepath + 'kunci.pub', 'r') as f:
        fsign = json.load(f)

    pubK = fsign['public_key']
    try:
        sign, _ = ecceg_.decrypt(pubK, b64decode(fhash))
    except Exception as e:
        return json.dumps({
            'error': True,
            'correct': False,
            'error_message': 'Decrypt error, check your public key'
        })

    print fmsg_hash
    print sign

    return json.dumps({
        'error': False,
        'correct': (fmsg_hash == sign),
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1111, debug=True)
