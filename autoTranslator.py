'''
模組: 將任何語言翻譯成英文
使用方法:
>>> import autoTranslator
>>> rerult = autoTranslator.translate('來源文字')
'''

import os
import re
import json
import requests
import configparser

# 抓取config.ini設定
config = configparser.ConfigParser()
config.read('config.ini')
API_URL = config.get('aws-translate', 'aws_translate_api_url')


def translate(text: str) -> str:
    if text == '' or type(text) != str:
        print('translation not needed.')
        return ''
    result = query({
        "text": text
    })
    print('translation done.')
    # print(f'from: {text}\nto: {result.encode().decode("unicode_escape")}')
    return result.encode().decode('unicode_escape')


def query(payload):
    data = json.dumps(payload)
    response = requests.request(
        "POST", API_URL, data=data, timeout=10000.0)
    return response.text
