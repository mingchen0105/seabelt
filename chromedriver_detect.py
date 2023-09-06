import os
import requests
from bs4 import BeautifulSoup
import re
import zipfile

def WebdriverDownload():
    try:
        os.remove('./chromedriver.exe')
    except FileNotFoundError as e:
        print(e)
    url_patern = r"[https://chromedriver.storage.googleapis.com/index.html?path=]+[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
    #"https://chromedriver.storage.googleapis.com/index.html?path=114.0.5735.90/"
    try:
        html = requests.get('https://chromedriver.chromium.org/downloads')
        bs_html = BeautifulSoup(html.text, 'lxml')
        bsfind = bs_html.find('a',href=re.compile(url_patern))
        Link = bsfind.get('href')
    except:
        print('GET Error in line 10~13')
    else:
        print(Link)
    try:
        DownloadLink = rf'https://chromedriver.storage.googleapis.com/{Link[Link.rfind("=")+1:]}chromedriver_win32.zip'
        print(DownloadLink)
        chromedriver = requests.get(DownloadLink)
    except:
        print('GET Error in line 19~21')
    else:
        with open('chromedriver.zip','wb') as file:
            file.write(chromedriver.content)
            file.close()
    if os.path.exists('./chromedriver.zip'):
        print('Download complete.Starting to unzip.')
        with zipfile.ZipFile('./chromedriver.zip') as zf:
            zf.extractall('./')
            zf.close()
        print('Complete unzip.')
        os.remove('./chromedriver.zip')
        os.remove('./LICENSE.chromedriver')
    else:
        print('No such file.')


if __name__ == '__main__':
    WebdriverDownload()
    print('closed')