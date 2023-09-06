'''
模組: 將任何英文字串做標籤分類，將回傳標籤名和對應機率
使用方法:
>>> import textClassifier
>>> rerult = textClassifier.classify('來源文字', '標籤類型')
標籤類型: 'gaming', 'membership', 'userInput'
'''

import re
import json
import requests
import configparser
import pandas as pd
import database

# 抓取config.ini設定
config = configparser.ConfigParser()
config.read('config.ini')
API_URL = config.get('huggingface', 'huggingface_api_url')
API_TOKEN = config.get('huggingface', 'huggingface_api_token')


def classify(text: str, category: str) -> list:
    # 若text=''或非str，則回傳[]標籤
    if text == '' or type(text) != str:
        return []
    result = query({
        "inputs": text,
        "parameters": {
            # 修: 不論category，算所有6個label的機率
            "candidate_labels": ["avatar", "limited_item", "virtual_world", "art", "discount", "experience"],
            "multi_label": True
        }
    })
    try:
        output = list(zip(result['labels'], result['scores']))
    except KeyError as e:
        print('Error when classifying: ', e)
        return []
    else:
        print(f'classify result: {output}')
        return output


def query(payload):
    data = json.dumps(payload)
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.request(
        "POST", API_URL, headers=headers, data=data, timeout=10000.0)
    return json.loads(response.content.decode("utf-8"))
