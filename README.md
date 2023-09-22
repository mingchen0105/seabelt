# SeaBelt NFT 商品推薦平台

<img src="https://raw.githubusercontent.com/mingchen0105/seabelt/main/statics/brand_icon.png" width="360" alt="seabelt logo">

SeaBelt 以知名 NFT 商品公開交易平台 - OpenSea 網站上各商品敘述為分析依據，利用 TF-IDF 方法及 BART 模型分析後，根據用戶瀏覽紀錄或預設商品分類，向其推薦或有興趣的商品。

## 系統需求
1. python 3.11
2. chrome 86.0.4240.111
3. (選用) docker daemon

## 安裝方法

* 直接執行
1. 將檔案存放於欲執行的環境
2. 設定`config.ini`的所有API服務
3. 安裝 requirements.txt 所需套件
`> pip install -r requirements.txt`
4. 啟動 flask 服務
`> python app.py` 

* 使用 docker 建立 container image
1. 設定`config.ini`的所有API服務
2. 建立容器
`> docker build -t <container名稱> .`
3. 測試 flask 運行狀況
`> docker run -p 5000:5000 flask-container`