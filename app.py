from flask import Flask, render_template, redirect, url_for, request, jsonify, make_response
import time
from datetime import datetime, timezone, timedelta
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.models import ImageCarouselTemplate, ImageCarouselColumn, URIAction, TemplateSendMessage
import re
import json
import configparser
from urllib import parse
import os
import pandas as pd
import database
import autoTranslator
import textClassifier

config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
my_line_id = config.get('line-bot', 'my_line_id')
end_point = config.get('line-bot', 'end_point')
line_login_id = config.get('line-bot', 'line_login_id')
line_login_secret = config.get('line-bot', 'line_login_secret')
my_phone = config.get('line-bot', 'my_phone')


app = Flask(__name__, static_folder="statics", static_url_path="/statics")

'''以取得的分類搜尋"collection_categories"資料表'''
# 分類與SQL欄位順序對照
labelNum = {
    5: "Avatar",
    6: "Limited items",
    7: "Virtual world",
    8: "Art",
    9: "Discount",
    10: "Experience"
}
# 分類與顯示名稱對照
labelName = {
    "art": "Art",
    "avatar": "Avatar",
    "discount": "Discount",
    "experience": "Experience",
    "limited_item": "Limited items",
    "virtual_world": "Virtual world"
}


def OrderAnalyse(userID, user_input):
    print(f'OrderAnalyse: {userID}, {user_input}')
    sql = f"SELECT cd.collection_slug, cd.collection_name, cd.collection_description, cd.collection_image, cl.* FROM collection_details cd\
        LEFT JOIN collection_labels cl ON cd.collection_slug = cl.collection_slug\
        WHERE cd.exist=1 AND cd.collection_slug IN (\
        SELECT cl.collection_slug FROM collection_labels WHERE cl.{user_input} IS NOT NULL\
        ) ORDER BY cl.{user_input} DESC"
    slugList = database.readAll(sql)

    results = list()
    for item in slugList:
        results.append(
            {
                "collection-slug": item[0],
                "collection-name": item[1],
                "collection-description": item[2],
                "collection-image": item[3],
                "labels": [labelNum[i] for i in range(5, 11, 1) if item[i]],
            }
        )
    return results


def getRelatedSlug(slug):
    print(f'getRelatedSlug: {slug}')
    '''
    取得related_slugs後,再個別抓每個collection資訊
    '''
    relatedSql = 'SELECT related_slugs FROM collection_details WHERE collection_slug=%s;'
    relatedList = database.read(relatedSql, (slug,))[0].split('|')
    collections = list()
    db = database.connectToDatabase()
    cursor = db.cursor()
    # 為防止載入時間過長，限制找20個項目
    for item in relatedList[:20]:
        collectionSql = "SELECT cd.collection_slug, cd.collection_name, cd.collection_description, cd.collection_image, cl.* FROM collection_details cd\
            LEFT JOIN collection_labels cl ON cd.collection_slug = cl.collection_slug\
            WHERE cd.collection_slug=%s AND cd.exist = 1\
            ORDER BY cd.collection_weekly_sales DESC;"
        cursor.execute(collectionSql, (item,))
        details = cursor.fetchone()
        if details:
            collections.append(details)
    db.close()
    results = list()
    for item in collections:
        results.append(
            {
                "collection-slug": item[0],
                "collection-name": item[1],
                "collection-description": item[2],
                "collection-image": item[3],
                "labels": [labelNum[i] for i in range(5, 11, 1) if item[i]],
            }
        )
    return results


def getUserStatus(lid):
    eventTime = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(
        timezone(timedelta(hours=8))).strftime("%Y/%m/%d-%H:%M:%S")
    sql = "SELECT uid FROM user_info WHERE line_id=%s"
    user_info = database.read(sql, (lid,))
    userID = f"{user_info[0]:04d}"
    return eventTime, userID


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        print('GET method')
    elif request.method == 'POST':
        print('POST method')
        LineBotOrder()

    # 取得Cookies中的lineID的value
    lineID = request.cookies.get("lineID")

    # lineID不存在就跳轉到line_login
    if lineID == None:
        return redirect(url_for('line_login'))

    # lineID存在，則重設cookies的時間
    else:
        res = make_response("Set cookies!")
        name = request.cookies.get("Name")
        lineID = request.cookies.get("lineID")
        pictureURL = request.cookies.get("icon")
        res.set_cookie(key="Name", value=name, expires=time.time()+30*60)
        res.set_cookie(key="lineID", value=lineID, expires=time.time()+30*60)
        res.set_cookie(key="icon", value=pictureURL, expires=time.time()+30*60)

        '''判斷userID是否存在於"user_info"資料表
          True, 設定userID為資料庫中的userID
          False, 生成一個userID，將userID和lineID寫入"使用者資料"資料表'''
        sql = "SELECT * FROM user_info WHERE line_id=%s"
        val = (lineID,)
        user_info = database.read(sql, val)
        print(user_info)
        if user_info == None:
            sql = f"SELECT uid FROM user_info"
            add_user = database.readAll(sql)
            userID = len(add_user)+1
            sql = "INSERT IGNORE INTO user_info (uid, line_id) VALUES (%s, %s)"
            database.write(sql, (userID, lineID))
        else:
            userID = f"{user_info[0]:04d}"
        print(f'uid= {userID}')

        return render_template('index.html', name=name, pictureURL=pictureURL)


@app.route('/line_login', methods=['GET'])
def line_login():
    '''line_login功能'''

    code = request.args.get("code", None)
    state = request.args.get("state", None)

    if code and state:
        HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
        url = "https://api.line.me/oauth2/v2.1/token"
        FormData = {"grant_type": 'authorization_code', "code": code, "redirect_uri": F"{end_point}/line_login",
                    "client_id": line_login_id, "client_secret": line_login_secret}
        data = parse.urlencode(FormData)
        content = requests.post(url=url, headers=HEADERS, data=data).text
        content = json.loads(content)
        url = "https://api.line.me/v2/profile"
        HEADERS = {
            'Authorization': content["token_type"]+" "+content["access_token"]}
        content = requests.get(url=url, headers=HEADERS).text
        content = json.loads(content)
        name = content["displayName"]
        lineID = content["userId"]
        pictureURL = content["pictureUrl"]
        # print(content)

        # 回傳轉址請求&設定cookies
        userID = ''
        res = make_response(redirect(url_for('index', userID=userID)))
        res.set_cookie(key="Name", value=name, expires=time.time()+30*60)
        res.set_cookie(key="lineID", value=lineID, expires=time.time()+30*60)
        res.set_cookie(key="icon", value=pictureURL, expires=time.time()+30*60)

        return res
    else:
        # 轉址到line login API
        url = f'https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={line_login_id}&redirect_uri={end_point}/line_login&scope=profile%20openid%20email&state=123453sdfgfd'
        return redirect(url)


@app.route('/api/q', methods=['GET'])
def apiPOSTrequest():
    '''
    依照使用者輸入，取得搜尋商品清單
    參數：/api/q?m=<user_input>&i=<userID>
    '''
    # http://127.0.0.1:5000/api/q?m=discount&i=0100

    # 取出query parameter
    query = request.args
    lineID = query['i']
    label = query['m']

    # 儲存輸入紀錄
    eventTime, userID = getUserStatus(lineID)
    eventLog = (userID, label, eventTime)
    sql = "INSERT INTO user_actions(uid, label, time) VALUES (%s, %s, %s)\
        ON DUPLICATE KEY UPDATE time=VALUES(time)"
    database.write(sql, eventLog)

    # 取回商品清單
    response = OrderAnalyse(userID=userID, user_input=label)
    # print(f'response = \n{response}')

    # 以json格式回傳collection清單
    return jsonify(response)


@app.route('/api/nft', methods=['GET'])
def apiClickCount():
    '''
    取得使用者點擊紀錄
    路徑參數：/api/nft?slug=<collection_slug>&n=<name>&i=<userID>
    '''
    # /api/nft?slug=avariksagauniverse&n=洪富璿&i=Ued4680f3266c04973d645b92b44d97b6

    # 取出query parameter
    query = request.args
    lineID = query['i']
    slug = query['slug']

    eventTime, userID = getUserStatus(lineID)

    # 若有輸入slug再存入user_history
    if slug:
        eventLog = (userID, slug, eventTime)
        sql = "INSERT INTO user_history(uid, slug, time) VALUES (%s, %s, %s)\
        ON DUPLICATE KEY UPDATE time=VALUES(time)"
        database.write(sql, eventLog)

    #   以uid為key搜尋"collection點擊紀錄"，列出最近點擊的collection
    sql = f"SELECT cd.*, uh.time FROM collection_details cd JOIN user_history uh ON cd.collection_slug = uh.slug \
            WHERE cd.exist=1 AND cd.collection_slug IN ( \
            SELECT slug FROM user_history WHERE uid={userID} ORDER BY time DESC \
            ) ORDER BY uh.time DESC"
    sluglist = database.readAll(sql)
    history = []
    for item in sluglist:
        history.append(
            {
                "collection-name": item[1],
                "collection-slug": item[0],
                "collection-description": item[2],
                "collection-image": item[4]
            }
        )
    return jsonify(history)


@app.route('/api/message')
def classifyUserInput():
    '''
    (20230830新增)
    分析使用者輸入文字
    '''
    lineId = request.args.get('id')
    input = request.args.get('input')

    # 儲存輸入紀錄
    eventTime, userID = getUserStatus(lineId)
    eventLog = (userID, input, eventTime)
    sql = "INSERT INTO user_input (uid, input_text, time) VALUES (%s, %s, %s)"
    database.write(sql, eventLog)

    inputToEng = autoTranslator.translate(input)
    print(f'input: {input} to english: {inputToEng}')
    labels = textClassifier.classify(inputToEng, 'all')
    result = dict()
    for label in labels:
        thisLabel = labelName[label[0]]
        matchInStr = re.search(f'(?i){thisLabel}', inputToEng)
        if label[1] >= 0.5 or matchInStr:
            params = {
                'i': lineId,
                'm': label[0],
                't': input
            }
            try:
                res = requests.get('http://localhost:5000/api/q',
                                   params=params)
            except UnboundLocalError as e:
                print('Error when fetching products info: ' + e)
            else:
                res = res.json()
                result[labelName[label[0]]] = [res[i:i+4]
                                               for i in range(0, len(res), 4)]
    if result == {}:
        lastSlug = request.args.get('slug', None)
        if not lastSlug:
            print('user沒有歷史紀錄')
        else:
            relatedSlugs = getRelatedSlug(lastSlug)
            result['related'] = [relatedSlugs[i:i+4]
                                 for i in range(0, len(relatedSlugs), 4)]
    return jsonify(result)


# 20230804
# line bot function


def LineBotOrder():
    body = request.json
    events = body["events"][0]
    lineID = events['source']['userId']
    replyToken = events['replyToken']

    if events['type'] == 'message':
        user_input = events['message']['text']
        # print(f'user_input = {user_input}')

        if user_input in ['avatar', 'limited_item', 'virtual_world', 'art', 'discount', 'experience']:
            LineBotLabel(lineID, user_input, replyToken)
        else:
            return line_bot_api.reply_message(reply_token=replyToken, messages='請點選主選單的標籤')


def LineBotLabel(lineID, label, replyToken):

    eventTime = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(
        timezone(timedelta(hours=8))).strftime("%Y/%m/%d-%H:%M:%S")

    # sql = f"SELECT * FROM user_info WHERE line_id='{lineID}'"
    sql = "SELECT * FROM user_info WHERE line_id=%s"
    val = (lineID,)
    user_info = database.read(sql, val)
    userID = f"{user_info[0]:04d}"

    eventLog = (userID, label, eventTime)

    '''存入"user_actions"資料表'''
    sql = "INSERT INTO user_actions(uid, label, time) VALUES (%s, %s, %s)"
    database.write(sql, eventLog)

    # 取回商品清單
    response = OrderAnalyse(userID=userID, user_input=label)

    # [print(f'{end_point}/api/linebotnft?slug={item["collection-slug"]}&i={userID}') for item in response[:10]]

    # 使用Image Carousel Template輸出多頁訊息 (如果不需要文字描述，只有圖片連結的場合)
    image_carousel_template = ImageCarouselTemplate(columns=[
        ImageCarouselColumn(
            image_url=item["collection-image"],
            action=URIAction(label=item['collection-name'][:12] if len(item['collection-name']) >= 12 else item['collection-name'],
                             uri=f'{end_point}/api/linebotnft?slug={item["collection-slug"]}&i={userID}')
        ) for item in response[:10]
    ])

    # 根據需要選擇使用Carousel Template或Image Carousel Template
    template_message = TemplateSendMessage(
        alt_text='NFT推薦', template=image_carousel_template)

    # 發送訊息給使用者
    line_bot_api.reply_message(replyToken, template_message)

# 經由flask再跳轉至opensea


@app.route('/api/linebotnft', methods=['GET'])
def LineBotNFT():  # /api/linebotnft?slug=<collection_slug>&i=<userID>
    print('LineBotNFT')
    # 取出query parameter
    query = request.args
    userID = query['i']
    slug = query['slug']
    eventTime = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(
        timezone(timedelta(hours=8))).strftime("%Y/%m/%d-%H:%M:%S")

    eventLog = (userID, slug, eventTime)

    '''存入"user_history"資料表'''
    sql = "INSERT INTO user_history(uid, slug, time) VALUES (%s, %s, %s)\
        ON DUPLICATE KEY UPDATE time=VALUES(time)"
    database.write(sql, eventLog)

    return redirect(f'https://opensea.io/collection/{slug}')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
