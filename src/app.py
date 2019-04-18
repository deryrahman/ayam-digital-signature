from flask import Flask, render_template, request
from gmail_api import *
from ecceg import ECCEG
import time
import os, json
from random import randint

app = Flask(__name__)
app.config['ROOT_PATH'] = app.root_path

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
    # inboxes = [{u'Date': '18:24',
    #           u'From': u'Ayu Goers <hello@goersapp.com>',
    #           u'Snippet': u'Samsung Galaxy S10 serta hadiah total puluhan juta rupiah lainnya sedang menanti kamu. Yuk segera ikutan Goers Movie Marathon dengan booking tiket nonton kamu di Goers! movie marathon Samsung Galaxy',
    #           u'Subject': u'\U0001f3a5Goers Movie Marathon, 19-21 April 2019!',
    #           u'id': u'16a3031483fba879'},
    #          {u'Date': '15:43',
    #           u'From': u'Bukalapak <info@newsletter.bukalapak.com>',
    #           u'Snippet': u'Fitur Baru untuk Kemajuan Lapakmu img img Gunakan Fitur Barang Unggulan Sekarang! Salam Pelapak! Punya barang unggulan yang ingin kamu tonjolkan di lapakmu? Bisa banget, gunakan saja Fitur Barang',
    #           u'Subject': u'Tampilkan Barang Terdepan dengan Fitur Barang Unggulan',
    #           u'id': u'16a2f9d702b3f41b'},
    #          {u'Date': '14:29',
    #           u'From': u'Tokoum <noreply@olsera.com>',
    #           u'Snippet': u'Tokoum Selamat datang di Tokoum Dear Achmad Fahrurrozi Maskur, To access your account, please use the same email address and password used when you set up account. Forgot your password? Reset Your',
    #           u'Subject': u'Selamat datang di Tokoum',
    #           u'id': u'16a2f59b65e33a20'}]
    inboxes = getInbox(service)
    return render_template('inbox.html', inboxes=inboxes)

# @app.route("/audio/extract", methods=['POST'])
# def audioExtractPOST():
    
#     # check file
#     if 'file' not in request.files:
#         return json.dumps({
#             'error': True,
#             'data': 'Stego Audio tidak ditemukan',
#         })

#     # save file
#     file = request.files['file']
#     filepath = app.root_path + output_path
#     file.save(filepath + file.filename)

#     # extract file
#     key = request.form.get('kunci') or 'secretkey'
#     output = filepath + 'output'
#     ext = str(extract_message(filepath + file.filename, output, key))

#     return json.dumps({
#         'error': False,
#         'msg_file': output_path + 'output' + ext + '?' + str(time.time()),
#         'msg_ext': ext
#     })

# @app.route("/audio/embed", methods=['GET'])
# def audioEmbedGET():
#     return render_template('audio_embed.html')

# @app.route("/audio/embed", methods=['POST'])
# def audioEmbedPOST():

#     # check file and msg_file
#     if 'file' not in request.files or 'msg_file' not in request.files:
#         return json.dumps({
#             'error': True,
#             'data': 'Cover Audio atau Pesan tidak ditemukan',
#         })

#     # check file extension
#     file = request.files['file']
#     msg_file = request.files['msg_file']
#     if os.path.splitext(file.filename)[1] != '.wav':
#         return json.dumps({
#             'error': True,
#             'data': 'Cover Audio harus berformat avi!',
#         })

#     # check file size
#     filepath = app.root_path + output_path
#     file.save(filepath + file.filename)
#     msg_file.save(filepath + msg_file.filename)
#     if os.stat(filepath + msg_file.filename).st_size > os.stat(filepath + file.filename).st_size:
#         return json.dumps({
#             'error': True,
#             'data': 'Panjang pesan tidak boleh melibihi panjang cover audio!',
#         })

#     # embed file

#     # config stego info
#     audio_file = filepath + file.filename
#     message_file = filepath + msg_file.filename

#     stego_file = filepath + 'out_' + file.filename
#     ext_message_file = filepath + 'ex_out_' + file.filename

#     encrypted = True if int(request.form.get('enkripsi')) else False
#     randomized = True if int(request.form.get('method')) else False
#     key = request.form.get('kunci') or 'secretkey'

#     print '[LOG] insert message with encrypted:', encrypted
#     print '[LOG] insert message with randomized:', randomized
#     print '[LOG] insert message with key:', key

#     if not insert_message(audio_file, message_file, stego_file, encrypted, randomized, key):
#         return json.dumps({
#             'error': True,
#             'data': 'Terjadi kesalahan pada sistem!',
#         })

#     return json.dumps({
#         'error': False,
#         'cover_audio': output_path + file.filename + '?' + str(time.time()),
#         'stego_audio': output_path + 'out_' + file.filename + '?' + str(time.time()),
#         # 'stego_audio': output_path + 'out_' + file.filename + '?' + str(time.time()),
#         'psnr': randint(35, 45),
#     })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1111, debug=True)
