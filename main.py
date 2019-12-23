import os
from flask import *

app = Flask(__name__)

SAVE_DIR = "./images"
if not os.path.isdir(SAVE_DIR):
    os.mkdir(SAVE_DIR)


@app.route("/", methods=["GET", "POST"])
def main_page():
    return render_template("index.html")


@app.route('/images/<path:path>')
def send_js(path):
    return send_from_directory(SAVE_DIR, path)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

