import json
import re
import requests
import configparser
import pandas as pd
# custom module
import autoTranslator
import textClassifier
import relatedSlug
import database

# 抓取config.ini設定
config = configparser.ConfigParser()
config.read('config.ini')


class OpenseaData:
    '''
    模組: 從MySQL取得collection資料, 加上分類及related slugs後回存MySQL
    使用方法
    >>> theVar = OpenseaData()
    >>> theVar.getAndArrange()
    '''

    def __init__(self):
        self.openseaToken = config.get(
            'opensea', 'opensea_api_token')
        self.collectionDf = None

    def getAndArrange(self):
        '''
        主程式
        '''
        self.makeCollectionDf()
        self.classifyCollection()
        LabelsToMysql(self.collectionDf)
        return 'complete'

    def makeCollectionDf(self):
        sql = f"SELECT cd.*, cc.category FROM collection_details cd JOIN collection_categories cc ON cd.collection_slug = cc.collection_slug WHERE cd.exist = 1"
        collectionArr = pd.read_sql(sql, database.connectToDatabase())
        print(f'collections count: {len(collectionArr)}')

        self.collectionDf = collectionArr
        print('asset dataframe created.')
        # return collectionArr.info()

    def classifyCollection(self):
        input = self.collectionDf.copy()
        # 預處理資料
        input['combined-description'] = input['collection_description'] + \
            input['asset_description']
        input.fillna('', inplace=True)
        input['combined-description'] = input['combined-description'].apply(
            lambda t: cleanText(t))

        # 翻譯資料
        input['translated-description'] = input['combined-description'].apply(
            lambda t: translater(t))

        # 分析一:slug之間相關性
        relatedSlug.find(input)
        print('slugs relationship analysis completed.')

        # 分析二:標籤
        input['labels'] = pd.Series([classifyText(
            t, input['category'][i])for i, t in enumerate(input['translated-description'])])
        input.drop(['translated-description', 'combined-description'],
                   axis='columns', inplace=True)
        self.collectionDf = input
        print('text classification completed.')


def cleanText(input):
    if type(input) != str:
        print('unable to clean text: ', type(input), input)
        return ''
    output = re.sub('http\S*|\s', ' ', input)
    output = re.sub('\s+', ' ', output)
    return output


def translater(text):
    translatedText = autoTranslator.translate(text)
    return translatedText


''' for New Remind System'''


def classifyText(translatedText, category):
    result = textClassifier.classify(translatedText, category)
    try:
        output = [(i[0], f'{i[1]:.4f}') for i in result if i[1] >= 0.7]
    except Exception as e:
        print('Error when getting classify result: ', e)
        return []
    else:
        print(f'classify done (label/correlation score): {output}')
        return output


def LabelsToMysql(df):
    '''
    將分類後collection資料存到mysql
    '''
    db = database.connectToDatabase()
    df.head(10)
    mycursor = db.cursor()
    for i, row in df.iterrows():
        # 預先寫入collection_slug到collection_labels表
        slugSql = 'INSERT IGNORE INTO collection_labels (collection_slug) VALUES (%s)'
        slugVal = (row["collection_slug"],)
        mycursor.execute(slugSql, slugVal)
        if len(row['labels']) == 0:
            continue
        for label in row['labels']:
            labelSql = f'UPDATE collection_labels SET {label[0]}=%s WHERE collection_slug=%s'
            labelVal = (label[1], row["collection_slug"])
            mycursor.execute(labelSql, labelVal)
    db.commit()
    print('labels saved to MySQL: ', mycursor.rowcount)
    db.close()


if __name__ == '__main__':
    memberData = OpenseaData()
    memberData.getAndArrange()
