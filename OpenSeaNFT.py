from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime
import requests
from threading import Thread
import database
import controller

from chromedriver_detect import WebdriverDownload  # 更新webdriver外部程式


def ScrollandSearch(browser, url, category):

    # 開啟網頁，取得頁面長度，設定每次滾動距離&滾輪初始位置
    browser.get(url)
    newpos = browser.execute_script("return document.body.scrollHeight")
    gap = newpos//6
    pos = 0

    # 取得slug
    while True:
        sleep(3)

        # find Ranking talbe裡各個collection的a標籤
        alist = browser.find_elements(By.XPATH, '//*/a[@role="row"]')
        print(len(alist))

        # 取出a標籤內的href -> slug
        try:  # 預期在find element可能會找不到
            tmplist = list(
                map(lambda a: a.get_attribute('href').split('/')[-1], alist))
        except:
            print('Get slug fail.')
            break

        # 判斷取得的slug是否重複，並寫入collection_categories資料表
        for slug in tmplist:

            sql = 'INSERT IGNORE INTO collection_categories (collection_slug, `category`) VALUES (%s, %s)'
            database.write(sql, (slug, category))
            sleep(0.5)

        # 操控browser畫面做滾動
        pos += gap
        if pos >= newpos:
            break
        else:
            browser.execute_script(f"document.documentElement.scrollTop={pos}")
        # 回到while

    # 爬取完畢，關閉browser
    browser.close()


def GetNFTData(category):
    # 1h, 6h 24h, 7day的url list
    DayRange = [
        f"https://opensea.io/rankings/trending?category={category}",
        f"https://opensea.io/rankings/trending?category={category}&sortBy=six_hour_volume",
        f"https://opensea.io/rankings/trending?category={category}&sortBy=one_day_volume",
        f"https://opensea.io/rankings/trending?category={category}&sortBy=seven_day_volume"
    ]

    # 啟動browser
    browsers = list(map(lambda b: webdriver.Chrome(), range(len(DayRange))))

    # 呼叫ScrollandSearch方法，開始取得資料
    tmp = []  # 存放threading task
    for i in range(len(DayRange)):
        tmp.append(Thread(target=ScrollandSearch, args=(
            browsers[i], DayRange[i], category)))  # 建立threading task
        tmp[i].start()
        print(f'Category\t{category},\ttask{i} starting.')

    for i in range(len(tmp)):
        tmp[i].join()  # threading task結束
        print(f'Category\t{category},\ttask{i} finish.')  # 爬蟲結束

# 每次丟一筆collection detail進來


def WriteCollectionToSQL(slug, data, asset_data):
    try:
        '''取得collection_detail資料'''
        Slug = data['collection']['slug']
        Name = data['collection']['name']
        Des = data['collection']['description']
        Sales = data['collection']['stats']['seven_day_sales']
        Img = data['collection']['image_url']
        exist = 1
    except KeyError as err:
        '''collection_detail資料為空，例外處理'''
        print(f"{err} with data\n{data}")
        Slug = slug
        Name = 'NA'
        Des = ''
        Sales = 0  # weekly_sales
        Img = ''
        exist = 0  # exist

    try:
        '''取得asset的描述'''
        asset_Des = asset_data['assets'][0]['description']
    except (IndexError, KeyError) as err:
        '''無asset的例外處理'''
        print(f"{err} with asset_data\n{asset_data}")
        asset_Des = ''

    # 將資料打包
    collection_detail = (
        Slug,
        Name,
        Des,
        Sales,  # weekly_sales
        Img,
        exist,
        asset_Des
    )

    # 寫入collection_details資料表
    sql = 'INSERT INTO collection_details (collection_slug, collection_name, collection_description, collection_weekly_sales, collection_image, exist, asset_description)\
            VALUES (%s, %s, %s, %s, %s, %s, %s)\
            ON DUPLICATE KEY UPDATE collection_name=VALUES(collection_name),collection_description=VALUES(collection_description),collection_weekly_sales=VALUES(collection_weekly_sales),collection_image=VALUES(collection_image),exist=VALUES(exist),asset_description=VALUES(asset_description)'
    database.write(sql, collection_detail)


def callAPI(slug):
    API_KEY = '344f1ec4e70247fd9687d598c837ae78'

    headers = {
        "accept": "application/json",
        "X-API-KEY": f"{API_KEY}"
    }

    # 用OpenSea的https api interface取得每個collection資料
    print(f'Getting {slug} data...')
    url = f'https://api.opensea.io/api/v1/collection/{slug}'
    detail_response = requests.get(url, headers=headers)

    url = f"https://api.opensea.io/api/v1/assets?collection={slug}"
    asset_response = requests.get(url, headers=headers)

    # 將資料整理成資料庫需要的形式並寫入
    WriteCollectionToSQL(slug, data=detail_response.json(),
                         asset_data=asset_response.json())


if __name__ == '__main__':
    print(datetime.now().strftime('%Y%m%d-%H%M'))
    try:
        # 測試webdriver能否正常啟動
        browsers = webdriver.Chrome()
        browsers.close()
    except:
        # 呼叫外部方法更新webdriver
        WebdriverDownload()

    # 多工並行，處理爬蟲
    threadinglist = []
    for i, j in enumerate(['gaming', 'memberships']):
        threadinglist.append(Thread(target=GetNFTData, args=(j,)))
        threadinglist[i].start()
    for x in threadinglist:
        x.join()
    # 完成更新collection_categories資料表
    print(f'Web Crawler finish at {datetime.now().strftime("%Y%m%d-%H%M")}')

    # 開始獲取collections資料
    print(f'Start to call API...')

    # 從資料庫讀取slug清單
    sql = 'SELECT collection_slug FROM collection_categories'
    mycursor = database.readAll(sql)
    sluglist = [result[0] for result in mycursor]
    print(f'\nslug list {len(sluglist)}\n')

    # 單工，處理callAPI()
    for i, j in enumerate(sluglist):
        callAPI(j)

    # 多工並行，處理callAPI()
    # threadinglist = []
    # for i, j in enumerate(sluglist):
    #     threadinglist.append(Thread(target=callAPI, args=(j,)))
    #     threadinglist[i].start()
    #     sleep(1)
    # for x in threadinglist:
    #     x.join()
    # 資料寫入完成
    print(f'Data Upload complet')

    # 呼叫NewController分析標籤
    print('Start to tag label')
    data = controller.OpenseaData()
    data.getAndArrange()
    print('Taging complet.')
