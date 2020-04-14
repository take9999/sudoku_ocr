# https://qiita.com/keimoriyama/items/7c935c91e95d857714fb

import os
from flask import Flask, request, render_template, send_from_directory, jsonify
from ocr_predict_number import get99imgs, get_ocr_result_list
import csv
from flask_cors import CORS
import pprint
import threading
import glob

from solve_sudoku import set_num

app = Flask(__name__)
CORS(app)

# アップロードされる拡張子の制限
ALLOWED_EXTENSIONS = ('png', 'jpg', 'gif')

UPLOAD_FOLDER = "./images"
TEXT_FOLDER = "./ocr_text"

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
if not os.path.isdir(TEXT_FOLDER):
    os.mkdir(TEXT_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEXT_FOLDER'] = TEXT_FOLDER


# file形式の確認
def allowed_file(filename):
    # .があるかどうかの確認 and 想定された拡張子かどうかの確認
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        return True
    else:
        return False


# OCR処理実行
def do_ocr():
    ocr_list = get_ocr_result_list()

    # TODO 空白行除去(ocr_list)

    # osr_listを出力
    ocr_filename = "ocr_text.txt"
    ocr_file_path = os.path.join(app.config['TEXT_FOLDER'], ocr_filename)
    with open(ocr_file_path, mode="w") as wf:
        writer = csv.writer(wf)
        writer.writerows(ocr_list)


@app.route("/", methods=["GET", "POST"])
def main_page():
    return render_template("index.html")


@app.route("/post_solve", methods=["POST"])
def post_solve():
    cells = request.json["cells"]

    data = []
    return_json = {}
    if cells is not None:
        for row in cells:
            r = []
            for col in row:
                num = 0
                if col != "":
                    try:
                        num = int(col)
                    except:
                        pass
                r.append(num)
            data += [r]

        print("--- 問題データ ---")
        pprint.pprint(data)

        set_num(data, 0)

        # osr_text_solveを読み込み
        ocr_filename = "ocr_text_solve.txt"
        ocr_file_path = os.path.join(app.config['TEXT_FOLDER'], ocr_filename)
        with open(ocr_file_path, mode="r") as rf:
            data = rf.readlines()

        # dataを整形
        for i, d in enumerate(data):
            row_list = []
            d = d.rstrip("\n")
            for num in d.split(","):
                row_list.append(str(num))
            return_json[i+1] = row_list

    return jsonify(return_json)


@app.route("/get_ocr_text", methods=["GET"])
def get_ocr_text():
    ocr_filename = "ocr_text.txt"
    ocr_file_path = os.path.join(app.config['TEXT_FOLDER'], ocr_filename)
    result_json = {}

    # 処理進捗度を返す
    png_path_list = glob.glob("./cell_img/*_finish.png")
    progress = int(len(png_path_list)/81 * 100)
    result_json[99] = progress

    if os.path.exists(ocr_file_path):
        with open(ocr_file_path, mode="r") as rf:
            i = 1
            for read_line in rf.readlines():
                if len(read_line) >= 9:
                    result_json[i] = read_line.replace("\n", "").split(",")
                    i = i + 1
            print(result_json)
        return jsonify(result_json)
    else:
        return jsonify(result_json)


@app.route("/upload", methods=["POST"])
def upload_img():
    # リクエストがポストかどうかの判別
    if request.method == 'POST':

        # requestにアップロードファイルが付与されていなかった場合は、TOPページへ戻す
        if 'file' not in request.files:
            return render_template("index.html")
        else:
            # データの取り出し
            file = request.files['file']

            # ファイル名が無かった場合は、TOPページへ戻す
            if file.filename == '':
                return render_template("index.html")

            # アップロードファイルの内容チェック
            if file and allowed_file(file.filename):
                # ファイルの保存
                filename = "sudoku.png"  # 'sudoku.png'という名前で保存（上書き）
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # 数独エリアを画像として取得
                get99imgs(file_path)

                # マルチスレッドでOCR処理(バックグラウンド処理)
                run_in_bg = threading.Thread(target=do_ocr, name='do_ocr')
                thread_names = [t.name for t in threading.enumerate() if isinstance(t, threading.Thread)]

                if 'do_ocr' not in thread_names:
                    run_in_bg.start()

                return render_template("index.html")
    else:
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

