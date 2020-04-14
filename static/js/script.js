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
var progress = 0;       // OCR進捗状況(パーセンテージ)

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
        isClear: isClear,
        progress: progress,
        updateOCRTimer: null,
        compUpdate: false
    },
    computed: {
        calcStyle: function() {
            return('width: ' + this.progress + '%');
        }
    },
    methods: {
        // OCR結果の取得
        updateOCR: function(event) {
            let self = this;
            if (self.compUpdate == false) {
                axios.get('/get_ocr_text')
                    .then(response => {
                        console.log('status:', response.status); // 200
                        console.log('body:', response.data);     // response body.

                        self.progress = response.data[99];
                        if (self.progress == 100) {
                            // response.dataが存在する場合
                            if (is_not_Empty(response.data)) {
                                for (let i=1; i<=9; i++){
                                    self.cells.push(response.data[i]);
                                }
                            }
                            // progressが100になった時、1回だけ画面更新
                            self.compUpdate = true
                        }

                        // 穴空けマスク作成(全てのマスを編集可能にする)
                        for (let i = 0; i < 9; i++) {
                            self.masks.push(new Array(9));
                            for (let j = 0; j < 9; j++) {
                                self.masks[i][j] = 'X';
                            }
                        }
                }).catch(err => {
                    console.log('err:', err);
                });
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
            let self = this;
            axios.post('/post_solve', {
                cells: self.cells
            })
            .then(function (response) {
                console.log(response);
                // response.dataが存在する場合
                if (is_not_Empty(response.data)) {
                    self.cells.length = 0;
                    for (let i=1; i<=9; i++){
                        self.cells.push(response.data[i]);
                    }
                }
            })
            .catch(function (error) {
                console.log(error);
            });
        }
    },
    mounted() {
        // bs custom file input
        bsCustomFileInput.init()

        this.cells.length = 0;
        this.masks.length = 0;
        this.updateOCR();
        this.updateOCRTimer = setInterval(this.updateOCR, 5000);
    },
    destroyed() {
        clearInterval(this.updateOCRTimer);
    }
})