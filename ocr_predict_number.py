import cv2
import numpy as np
import os
import shutil
import glob
import pprint

# tensorflow 1.13.1
# keras 2.3.1

from keras.datasets import mnist
from keras.utils import to_categorical

from keras.models import Sequential, load_model
from keras.layers import Dense, Activation, Dropout, Conv2D, MaxPooling2D, Flatten, Reshape
from keras import regularizers
from keras.losses import categorical_crossentropy
from keras.callbacks import ModelCheckpoint


def blur(img):
    blur_img = cv2.GaussianBlur(img, (11, 11), 0)
    return blur_img


def morphology(img):
    kernel = np.ones((2, 2), np.uint8)
    morp_img = cv2.morphologyEx(img, cv2.MORPH_ERODE, kernel, iterations=2)
    return morp_img


def get_rect_sudoku(image_bgr, image_2chi, target_path):
    image_bgr = cv2.copyMakeBorder(image_bgr, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
    image_2chi = cv2.copyMakeBorder(image_2chi, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)

    contours, hierarchy = cv2.findContours(image_2chi, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    area_list = list(map(lambda x: cv2.contourArea(x), contours))
    target_index = np.array(area_list).argsort()[::-1][1]  # 面積が2番目に大きい矩形のindex
    target_cnt = contours[target_index]
    x, y, w, h = 0, 0, 0, 0

    if target_cnt is not None:
        x, y, w, h = cv2.boundingRect(target_cnt)
        img_con = cv2.rectangle(image_bgr, (x, y), (x + w, y + h), (0, 0, 255), 1)
        cv2.imwrite(target_path + "_con.png", img_con)

    return x, y, w, h, image_bgr, image_2chi


def split_cell(x, y, w, h, image_2chi):
    if not os.path.exists('./cell_img'):
        os.mkdir('./cell_img')
    shutil.rmtree('./cell_img')
    os.mkdir('./cell_img')

    row_size = int(h / 9)
    col_size = int(w / 9)

    for i in range(9):
        for j in range(9):
            start_y = y + col_size * i
            end_y = start_y + col_size

            start_x = x + row_size * j
            end_x = start_x + row_size

            img_ij = image_2chi[start_y:end_y, start_x:end_x]
            h_ij, w_ij = img_ij.shape[:2]

            # 周囲を白色化
            del_space = int(h_ij * 15/100)  # %を白色化
            img_ij[0:del_space, 0:w_ij] = 255
            img_ij[h_ij-del_space:h, 0:w_ij] = 255
            img_ij[0:h_ij, 0:del_space] = 255
            img_ij[0:h_ij, w_ij-del_space:w_ij] = 255

            # 画像の中央部分に黒色文字がある場合のみ数字が書かれていると判定する
            img_center = img_ij[int(h_ij*30/100): int(h_ij*70/100), int(w_ij*30/100): int(w_ij*70/100)]
            area_white_pixels = cv2.countNonZero(img_center)
            area_all_pixels = img_center.shape[0] * img_center.shape[1]
            area_black_pixels = area_all_pixels - area_white_pixels

            if area_black_pixels >= 10:  # 文字が書かれている場合
                cv2.imwrite("cell_img/{}_{}_t.png".format(i+1, j+1), img_ij)
            else:
                cv2.imwrite("cell_img/{}_{}_f.png".format(i+1, j+1), img_ij)


def get99imgs(image_path):
    img_bgr = cv2.imread(image_path)
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 二値化
    _, img_2chi = cv2.threshold(img_gray, 200, 255, cv2.THRESH_BINARY)

    # 数独表の抽出
    t_x, t_y, t_w, t_h, img_bgr, img_2chi = get_rect_sudoku(img_bgr, img_2chi, image_path)

    # 各セルの画像を取得
    split_cell(t_x, t_y, t_w, t_h, img_2chi)


def predict_number(image_path):
    img_cell = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img_cell = cv2.bitwise_not(img_cell)
    img_cell = cv2.resize(img_cell, (28, 28))

    # 収縮処理
    # kernel = np.ones((3, 3), np.uint8)
    # img_cell = cv2.erode(img_cell, kernel, iterations=1)

    _, img_cell = cv2.threshold(img_cell, 200, 255, cv2.THRESH_BINARY)
    img_cell = img_cell.reshape((1, 28, 28, 1))
    # print(model.predict(img_cell))
    # cv2.imwrite("img_cell.png", img_cell.reshape((28, 28)))

    model_file = "mnist_cnn_model.h5"
    model = Sequential()

    if not os.path.exists(model_file):
        # ########### deep learning ################################
        (x_train, y_train), (x_test, y_test) = mnist.load_data()

        # shuffle
        permutation = np.random.permutation(x_train.shape[0])
        x_train = x_train[permutation]
        y_train = y_train[permutation]

        # 28*28 -> 784
        train_num = 50000  # max 60000
        x_train = x_train[:train_num].reshape((-1, 784))
        x_test = x_test[:1000].reshape((-1, 784))

        # for i in range(10):
        #     cv2.imwrite("{}.png".format(i), x_test[i*100].reshape((28, 28)))

        y_train = to_categorical(y_train[:train_num], num_classes=10)

        y_test = to_categorical(y_test[:1000], num_classes=10)

        mean = np.mean(x_train)
        std = np.std(x_train)
        x_train = (x_train - mean) / std
        x_test = (x_test - mean) / std

        REG = regularizers.l2(1e-4)

        model.add(Reshape((28, 28, 1), input_shape=(784,)))

        model.add(Conv2D(32, (3, 3), padding="same", input_shape=(28, 28, 1)))
        model.add(Activation("relu"))

        model.add(Conv2D(32, (3, 3), padding="same"))
        model.add(Activation("relu"))

        model.add(MaxPooling2D(pool_size=(2, 2)))

        model.add(Dropout(0.5))

        model.add(Conv2D(64, (3, 3), padding="same"))
        model.add(Activation("relu"))

        model.add(Conv2D(64, (3, 3), padding="same"))
        model.add(Activation("relu"))

        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.5))

        model.add(Conv2D(128, (3, 3), padding="same"))
        model.add(Activation("relu"))

        model.add(Conv2D(128, (3, 3), padding="same"))
        model.add(Activation("relu"))

        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.5))

        model.add(Flatten())

        model.add(Dense(100))
        model.add(Activation("relu"))

        model.add(Dropout(0.5))

        model.add(Dense(10))
        model.add(Activation('softmax'))

        model.compile(loss=categorical_crossentropy,
                      optimizer='Adam',
                      metrics=['accuracy'])

        batch_size = 200
        total_epoch = 50
        log = model.fit(x_train, y_train,
                        batch_size=batch_size,
                        epochs=total_epoch,
                        verbose=1)

        model.save(model_file)

    model = load_model(model_file)

    result = np.argmax(model.predict(img_cell))
    print(result)
    return result


def get_ocr_result_list():
    ocr_result_list = []

    png_path_list = glob.glob("./cell_img/*.png")
    now_row = '1'
    row_list = []
    for png_path in sorted(png_path_list):
        row, col, bool_val = png_path[-9:].replace(".png", "").split("_")
        if now_row != row:
            ocr_result_list.append(row_list)
            row_list = []
            now_row = row

        # 文字が書かれている場合は、数字予測を実施
        if bool_val == 't':
            row_list.append(str(predict_number(png_path)))
        else:
            row_list.append('')

        # OCR完了した画像の名前を変更
        renamed_path = png_path.replace(".png", "_finish.png")
        os.rename(png_path, renamed_path)

    # last row append
    ocr_result_list.append(row_list)

    return ocr_result_list


if __name__ == '__main__':
    target_path = "images/sudoku5.png"

    # 画像から最大の四角形を検知し、9*9の各セルの画像を取得
    get99imgs(target_path)
    pprint.pprint(get_ocr_result_list())
