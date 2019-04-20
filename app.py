from flask import Flask, render_template, request
# from gmail_api import *
from ecceg import ECCEG
import time
import os, json
from random import randint

app = Flask(__name__)
app.config['ROOT_PATH'] = app.root_path

output_path = '/static/output/'
ecceg_ = ECCEG()
# service = getService()

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
    return render_template('send.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1111, debug=True)
