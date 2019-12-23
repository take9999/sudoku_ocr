// 開発モード
Vue.config.debug = false;

// Vue.js devtools
Vue.config.devtools = true;

// 背景画像をランダムに表示
var images = [
    'bridge.jpg',
    'flower.jpg',
    'hokkaido.jpg',
    'kouyou.jpg',
    'newyork.jpg',
    'setsugen.jpg'
];
document.body.style.backgroundImage = 'url(img/' +　images[Math.floor(Math.random() * images.length)] + ')';

var cells = [];         // ナンプレテーブル
var masks = [];         // 穴空けマスクテーブル
var isEdit = [];        // 編集中フラグ
var isClear = false;    // クリア判定
var row = '';           // 行候補
var col = '';           // 列除外候補
var box = '';           // 箱除外候補
var choose = '';        // 最終候補
var retry = 0;          // リトライカウント

// 編集中フラグの初期化
for(let e = 0; e < 9; e++)
    isEdit[e] = new Array(9).fill(false);

new Vue({
    delimiters: ["[[", "]]"],
    el: '#app',
    data: {
        cells: cells,
        masks: masks,
        isEdit: isEdit,
        isClear: isClear
    },
    methods: {
        // ページが読み込まれたとき
        window:onload = function() {
            // テーブル初期化
            cells.length = 0;
            masks.length = 0;

            // ナンプレ作成
            for (let i = 0; i < 9; i++) {
                // 行候補初期化
                row = '123456789';

                // 行追加
                cells.push(new Array(9));

                // 列追加
                for (let j = 0; j < 9; j++) {
                    // 列除外候補を収集
                    col = '';
                    for (let k = 0; k < i; k++)
                        col += cells[k][j];

                    // 箱除外候補を収集
                    box = '';
                    for (let k = i % 3; k > 0; k--) {
                        box += cells[i - k][j - (j % 3)];
                        box += cells[i - k][j - (j % 3) + 1];
                        box += cells[i - k][j - (j % 3) + 2];
                    }

                    // 行候補 - 列除外候補 - 箱除外候補 = 最終候補
                    choose = row;
                    for (let n = 0; n < col.length; n++)
                        choose = choose.replace(col.charAt(n), '');
                    for (let m = 0; m < box.length; m++)
                        choose = choose.replace(box.charAt(m), '');

                    // 最終候補から乱数により数字を1つ選択
                    let num = choose.charAt(Math.floor(Math.random() * choose.length));

                    // 最終候補に何も残らなかった場合
                    if (num == '') {
                        // 10回リトライしても無理なら最初からやり直す
                        if (retry > 10) {
                            i = -1;
                            cells.length = 0;
                            retry = 0;
                            break;
                        }

                        // 列追加をやり直す（10回までリトライ）
                        j = -1;
                        row = '123456789';
                        retry++;
                        continue;
                    }

                    // 行候補から取り出してテーブルに反映する
                    row = row.replace(num, '');
                    cells[i][j] = parseInt(num);
                }
            }

            // 穴空けマスク作成
            for (let i = 0; i < 9; i++) {
                // 行追加
                masks.push(new Array(9));

                // 穴空け
                let hole = '012345678';
                for (let n = 0; n < Math.floor(Math.random() * 8) + 2; n++)
                    hole = hole.replace(hole.charAt(Math.floor(Math.random() * (9 - n))), '');
                for (let m = 0; m < hole.length; m++)
                    masks[i][hole.charAt(m)] = 'X';

                // 列追加
                for (let j = 0; j < 9; j++) {
                    // 穴空け箇所 (X) はナンプレテーブルから数字を消去
                    if (masks[i][j] == 'X')
                        cells[i][j] = '';
                }
            }
        },

        // 穴空きセルがクリックされたとき
        clickCell: function(event) {
            // セル番地を取得
            let i = event.target.parentNode.rowIndex;
            let j = event.target.cellIndex;

            // 穴空きセルなら入力モードへ
            if (masks[i][j] == 'X') {
                Vue.set(isEdit[i], j, true);
                this.$nextTick(() => document.getElementById('edit').focus());
            }
        },

        // 穴空きセルの入力が終了したとき
        blurCell: function(event) {
            // セル番地を取得
            let i = event.target.parentNode.parentNode.rowIndex;
            let j = event.target.parentNode.cellIndex;

            // 1-9 の数値または空白ならセルに反映する
            let num = event.target.value;
            if (isFinite(num))
                if (num > 0 && num < 10)
                    Vue.set(cells[i], j, parseInt(event.target.value))
            else if (num == '')
                Vue.set(cells[i], j, '')

            // 入力モードを終了する
            Vue.set(isEdit[i], j, false);

            // クリア判定
            let clear = true;

            // 行のクリア条件：1行の合計が45
            for (let n = 0; n < cells.length; n++) {
                let sum = 0;
                for (let m = 0; m < cells.length; m++) {
                    if (cells[n][m] != '')
                        sum += cells[n][m];
                }
                if (sum != 45)
                    clear = false;
            }

            // 列のクリア条件：1列の合計が45
            for (let n = 0; n < cells.length; n++) {
                let sum = 0;
                for (let m = 0; m < cells.length; m++) {
                    if (cells[m][n] != '')
                        sum += cells[m][n];
                }
                if (sum != 45)
                    clear = false;
            }

            // クリア効果
            if (clear) {
                this.isClear = true;
                document.getElementById('canvas').style.display = 'block';
            }
        }
    }
})