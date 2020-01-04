# https://qiita.com/keimoriyama/items/7c935c91e95d857714fb

import os
from flask import Flask, request, render_template, send_from_directory, jsonify
from ocr_predict_number import get99imgs, get_ocr_result_list
import csv
from flask_cors import CORS

# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif'])

app = Flask(__name__)
CORS(app)  # <-追加

UPLOAD_FOLDER = "./images"
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
TEXT_FOLDER = "./ocr_text"
if not os.path.isdir(TEXT_FOLDER):
    os.mkdir(TEXT_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEXT_FOLDER'] = TEXT_FOLDER


def allowed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def main_page():
    return render_template("index.html")


@app.route("/post_solve", methods=["POST"])
def solve_sudoku():
    text_file_path = "ocr_text/ocr_text.txt"
    result_json = {}
    if os.path.exists(text_file_path):
        with open(text_file_path, mode="r") as rf:
            i = 1
            for read_line in rf.readlines():
                if len(read_line) == 18:
                    result_json[i] = read_line.replace("\n", "").split(",")
                    i = i + 1
            print(result_json)
        return jsonify(result_json)
    else:
        return jsonify({})


@app.route("/get_ocr_text", methods=["GET"])
def solve_sudoku():
    text_file_path = "ocr_text/ocr_text.txt"
    result_json = {}
    if os.path.exists(text_file_path):
        with open(text_file_path, mode="r") as rf:
            i = 1
            for read_line in rf.readlines():
                if len(read_line) == 18:
                    result_json[i] = read_line.replace("\n", "").split(",")
                    i = i + 1
            print(result_json)
        return jsonify(result_json)
    else:
        return jsonify({})


@app.route("/upload", methods=["POST"])
def upload_img():
    # リクエストがポストかどうかの判別
    if request.method == 'POST':

        # ファイルがなかった場合の処理
        if 'file' not in request.files:
            return render_template("index.html")
        else:
            # データの取り出し
            file = request.files['file']

            # ファイル名がなかった時の処理
            if file.filename == '':
                return render_template("index.html")

            # ファイルのチェック
            if file and allowed_file(file.filename):
                # ファイルの保存
                filename = "sudoku.png"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # sudoku画像のocr実行
                get99imgs(file_path)
                ocr_list = get_ocr_result_list()

                # osr_listを出力
                output_file_path = "ocr_text/ocr_text.txt"
                with open(output_file_path, mode="w") as wf:
                    writer = csv.writer(wf)
                    writer.writerows(ocr_list)

                # アップロード後のページに転送
                return render_template("index.html")


@app.route('/images/<path:path>')
def send_js(path):
    try:
        response = send_from_directory(directory=UPLOAD_FOLDER, filename=path)
        response.headers['Cache-Control'] = 'no-cache'
        response.cache_control.max_age = 0
        response.cache_control.public = True
        return response

    except Exception as e:
        return str(e)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

