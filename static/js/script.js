// https://qiita.com/Kazuya_Murakami/items/f5ef5fed850b8b9e7a81

function is_not_Empty(obj){
  return Object.keys(obj).length;
}

// 開発モード
Vue.config.debug = false;

// Vue.js devtools
Vue.config.devtools = true;

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

            axios.get('/get_ocr_text')
                .then(response => {
                    console.log('status:', response.status); // 200
                    console.log('body:', response.data);     // response body.

                    if (is_not_Empty(response.data)) {
                        for (let i=1; i<=9; i++){
                            cells.push(response.data[i]);
                        }
                    }

                    // 穴空けマスク作成(全てのマスを編集可能にする)
                    for (let i = 0; i < 9; i++) {
                        masks.push(new Array(9));
                        for (let j = 0; j < 9; j++) {
                            masks[i][j] = 'X';
                        }
                    }
                }).catch(err => {
                    console.log('err:', err);
                });
        },
        // 穴空きセルがクリックされたとき
        clickCell: function(event) {
            // セル番地を取得
            let i = event.target.parentNode.rowIndex;
            let j = event.target.cellIndex;

            // 穴空きセルなら入力モードへ
            if (masks[i][j] == 'X') {
                Vue.set(isEdit[i], j, true);
                cells[i][j] = '';
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
        },
        //解答を取得ボタンが押されたとき
        clickSolve: function(event){
            axios.post('/post_solve', {
                cells: cells
            })
            .then(function (response) {
                console.log(response);
            })
            .catch(function (error) {
                console.log(error);
            });
        }
    }
})