VERSION = '1.0'
from datetime import datetime, timedelta
from dateutil.parser import parse
from time import sleep
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select

import os
import webbrowser
import time
import json
import zipfile
import logging


LABO225_URL = {
    'login'    : 'https://225labo.com/user.php',
    'download' : 'https://225labo.com/modules/downloads_data/index.php?cid=3'
}

class LABO225_Utility:
    logger = logging.getLogger(__name__)

    def __init__(self,
                 userId,
                 pw,
                 driver_path,
                 *_, **__):
        self.userId  = userId
        self.pw      = pw

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument('--window-size=1280,800')
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--enable-logging")
        options.add_argument("--log-level=0")
        options.add_argument("--v=99")
        options.add_argument("--single-process")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--homedir=/tmp")
        
        options.binary_location = "/opt/bin/headless-chromium"
        
        # ブラウザを起動する
        driver = webdriver.Chrome(
            driver_path, chrome_options=options)
        driver.set_window_size(1920,1080)
        driver.maximize_window()

        # ヘッドレスChromeでファイルダウンロードするにはここが必要だった
        driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        driver.execute("send_command", {
            'cmd': 'Page.setDownloadBehavior',
            'params': {
                'behavior': 'allow',
                'downloadPath': '/tmp' # ダウンロード先
             }
        })
        
        self.logger.info(
            '''

            225LABO開始
            [{}] 
            '''.format(datetime.now().strftime('%Y%m%d %H:%M:%S')))
        self.driver = driver
        self.logger.debug(self.__dict__)

    def login(self):
        self.logger.info('225LABOへログイン開始')
        self.driver.get(LABO225_URL['login'])
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.NAME, "uname")))
        self.driver.find_element_by_name("uname").clear()
        self.driver.find_element_by_name("uname").send_keys(self.userId)
        self.driver.find_element_by_name("pass").clear()
        self.driver.find_element_by_name("pass").send_keys(self.pw)
        self.driver.find_element_by_xpath("//*[@id='ModuleContents']/form/div/table/tbody/tr[3]/th/input").click()
        # ログイン成功判定
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.ID, "acc_btn")))
        self.logger.info('225LABOへログイン完了')
    
    #
    # ダウンロードへ遷移
    #
    def downloadData(self):

        # ダウンロードファイル削除
        if os.path.exists('/tmp/N225minif_2021.zip'):
            self.logger.info('N225minif_2021.zipファイル削除')
            os.remove('/tmp/N225minif_2021.zip')

        self.logger.info('ダウンロード開始')
        self.driver.get(LABO225_URL['download'])
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.ID, "down_pro_list")))
        self.driver.find_element_by_xpath('//*[@id="down_pro_list"]/tbody/tr[1]/td[2]/p[2]/a').click()
        self.logger.info('ダウンロード完了')
        time.sleep(10)
        self.logger.info('ダウンロードファイル解凍開始')
        # ダウンロードファイル解凍
        with zipfile.ZipFile('/tmp/N225minif_2021.zip') as existing_zip:
            existing_zip.extractall('/tmp')
        self.logger.info('ダウンロードファイル解凍完了')
            
    '''
    225LABOデータ取得終了
    '''
    def exit(self):
        self.logger.info('Chromeを閉じる 開始')
        self.driver.quit()
        self.logger.info('Chromeを閉じる 完了')

    '''
    225LABOデータ取得処理
    '''
    def start_download(self):
        try:
            self.logger.debug('ダウンロード処理')
            # ログイン
            self.login()
            # ダウンロード処理
            self.downloadData()
            self.exit()
        except Exception as e:
            print(str(e))
            self.logger.error(str(e))
            self.driver.save_screenshot("screen.png")
            self.exit()