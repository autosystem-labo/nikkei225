# -*- coding: utf-8 -*-
# VERSION
# 2021/02/27 
# SBI証券共通ライブラリ
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


import logging

driver_path = '.\\chromedriver.exe'

SBI_URL = {
    'login'    : 'https://www.sbisec.co.jp/ETGate',
    'domestic' : 'https://site0.sbisec.co.jp/marble/domestic/top.do?',
}

class SBI_Utility:
    logger = logging.getLogger(__name__)

    def __init__(self,
                 userId,
                 pw,
                 orderPw,
                 number,
                 month,
                 driver_path,
                 *_, **__):
        self.userId  = userId
        self.pw      = pw
        self.orderPw = orderPw
        self.number  = number
        self.month   = month

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

            SBI証券へエントリー開始
            [{}]
            '''.format(datetime.now().strftime('%Y%m%d %H:%M:%S')))
        self.driver = driver
        self.logger.debug(self.__dict__)

    def login(self):
        self.logger.info('SBI証券へログイン開始')
        self.driver.get(SBI_URL['login'])
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.NAME, "user_id")))
        self.driver.find_element_by_name("user_id").clear()
        self.driver.find_element_by_name("user_id").send_keys(self.userId)
        self.driver.find_element_by_name("user_password").clear()
        self.driver.find_element_by_name("user_password").send_keys(self.pw)
        self.driver.find_element_by_name("ACT_login").click()
        # ログイン成功判定
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.ID, "logout")))
        self.logger.info('SBI証券へログイン完了')
    
    #
    # 先物オプション取引画面へ遷移
    #
    def selectSakimonoOption(self):
        self.logger.info('先物オプション取引画面へ遷移開始')
        self.driver.find_element_by_xpath("//*[@id='navi01P']/ul/li[8]/a/img").click() # 先物OP押下
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.XPATH, "//*[@id='MAINAREA01-INNER-R']/div[3]/div/div[2]/p/a/img"))) # 先物・オプション取引サイトへ表示判定
        self.driver.find_element_by_xpath("//*[@id='MAINAREA01-INNER-R']/div[3]/div/div[2]/p/a/img").click() # 先物・オプション取引サイトへクリック
        self.driver.switch_to.window(self.driver.window_handles[1]) # タブ切替
        # フレーム切替　開始
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.NAME, "menu")))
        self.logger.info('先物オプション取引画面へ遷移完了')

    #
    # 一括注文取消し
    #
    def cancelOrder(self):
        self.logger.info('一括注文取消し')
        print('一括注文取消し')
        # フレーム切替
        frame = self.driver.find_element_by_name("menu")
        self.driver.switch_to_frame(frame)
        frame = self.driver.find_element_by_name("menuBody")
        self.driver.switch_to_frame(frame)
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.XPATH, "//*[@id='menu30']")))
        self.driver.find_element_by_xpath("//*[@id='menu30']").click() # 取引状況クリック
        time.sleep(2)
        self.driver.find_element_by_id("formCM0004:subMenu32").click() # 未約定一覧クリック
        self.driver.switch_to.default_content() # 元のフレームに切り替え
        frame = self.driver.find_element_by_name("main")
        self.driver.switch_to_frame(frame)
        frame = self.driver.find_element_by_name("contents")
        self.driver.switch_to_frame(frame)
        time.sleep(2)
        self.logger.info('コンテンツ画面遷移完了')
        print('コンテンツ画面遷移完了')
        c = self.driver.find_elements_by_id('formRF0201_2:SCR_PC_RF_0201_link')
        if len(c) > 0:
            self.driver.find_element_by_id("formRF0201_2:SCR_PC_RF_0201_link").click() # 一括決済クリック
        else:
            print('一括注文取消し対象なし')
            return
        time.sleep(2)
        self.driver.find_element_by_id("formRF0201_3:SCR_PC_RF_0201_hidelink4").click() # 一括取消し押下
        print('一括取消し完了')
        time.sleep(10)
        
    #
    # 先物オプション取引実行
    #
    def orderSakimonoOption(self, buy_price, sell_price, buyOrsell=None):
        self.logger.info('先物オプション取引実行開始')
        # フレーム切替
        frame = self.driver.find_element_by_name("menu")
        self.driver.switch_to_frame(frame)
        frame = self.driver.find_element_by_name("menuBody")
        self.driver.switch_to_frame(frame)
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.XPATH, "//*[@id='menu20']")))
        self.driver.find_element_by_xpath("//*[@id='menu20']").click() # 取引クリック
        self.driver.switch_to.default_content() # 元のフレームに切り替え
        frame = self.driver.find_element_by_name("main")
        self.driver.switch_to_frame(frame)
        frame = self.driver.find_element_by_name("contents")
        self.driver.switch_to_frame(frame)
        time.sleep(2)
        self.driver.find_element_by_id("formOD0101:product:1").click() # 商品（ミニ日経225先物）
        self.logger.info('商品（ミニ日経225先物）設定完了')
        time.sleep(2)
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.ID, "formOD0101:securityCd")))
        dropdown = self.driver.find_element_by_id("formOD0101:securityCd")
        select = Select(dropdown)
        if len(self.month) == 0:
            pass # 限月設定
        else:
            select.select_by_visible_text(self.month) # 限月設定
        self.logger.info('限月設定完了')
        time.sleep(2)

        if buyOrsell is None:
            # OCOエントリー
            print('OCO注文')
            self.orderOCO(buy_price, sell_price)
        else:
            print('成行(FAK)注文')
            self.orderMarket(buyOrsell)
        self.driver.find_element_by_id("formOD0101:confirmId").click() # 確認画面の省略設定
        self.logger.info('確認画面の省略設定完了')
        self.driver.find_element_by_id("formOD0101:orderButtonId").click() # 注文する
        time.sleep(2)
        c = self.driver.find_elements_by_id('formOD0102:doRegisterFuture')
        if len(c) > 0:
            self.driver.find_element_by_id("formOD0102:doRegisterFuture").click() # 一括決済クリック
        else:
            print('現値ワーニングなし')
        
        self.logger.info('先物オプション取引実行完了')
        print('先物オプション取引実行完了')
        time.sleep(10)
    
    # OCO設定
    def orderOCO(self, buy_price, sell_price):
        self.driver.find_element_by_id("formOD0101:orderPatternPairId1").click() # OCO指定
        time.sleep(2)
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.ID, "formOD0101:bsPairId:0")))
        # 買い
        self.driver.find_element_by_id("formOD0101:bsCls:0").click()
        time.sleep(2)
        dropdown = self.driver.find_element_by_id("formOD0101:conditionPair1Id")
        select = Select(dropdown)
        select.select_by_visible_text('逆指値') # 逆指値指定
        time.sleep(1)
        self.driver.find_element_by_id("formOD0101:triggerConditionPriceId").clear()
        self.driver.find_element_by_id("formOD0101:triggerConditionPriceId").send_keys(str(buy_price))# 買い価格指定
        dropdown = self.driver.find_element_by_id("formOD0101:inpConditionGyakusashiId")
        select = Select(dropdown)
        select.select_by_visible_text('成行(FAK)') # 指値(FAK)指定
        time.sleep(1)
        # self.driver.find_element_by_id("formOD0101:orderPriceId").clear()
        # self.driver.find_element_by_id("formOD0101:orderPriceId").send_keys(str(buy_price))# 指値買い価格指定
        # 売り
        self.driver.find_element_by_id("formOD0101:bsPairId:1").click()
        time.sleep(1)
        self.driver.find_element_by_id("formOD0101:triggerConditionPricePairId").clear()
        self.driver.find_element_by_id("formOD0101:triggerConditionPricePairId").send_keys(str(sell_price))# 売り価格指定
        dropdown = self.driver.find_element_by_id("formOD0101:inpConditionGyakusashiPairId")
        select = Select(dropdown)
        select.select_by_visible_text('成行(FAK)') # 指値(FAK)指定
        time.sleep(1)
        # self.driver.find_element_by_id("formOD0101:pricePairId").clear()
        # self.driver.find_element_by_id("formOD0101:pricePairId").send_keys(str(sell_price))# 指値売り価格指定

        # 数量
        self.driver.find_element_by_id("formOD0101:qtyRcvd").clear()
        self.driver.find_element_by_id("formOD0101:qtyRcvd").send_keys(str(self.number))# 数量指定

        # 有効期間設定
        self.driver.find_element_by_id("formOD0101:durationId:0").click()

    # 成行（FAK）設定
    def orderMarket(self,buyOrsell):
        self.driver.find_element_by_id("formOD0101:orderPatternTujyoId1").click() # OCO指定
        time.sleep(2)
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.ID, "formOD0101:conditionId")))
        if 'buy' in buyOrsell:
            # 買い
            self.driver.find_element_by_id("formOD0101:bsCls:0").click()
        else:
            # 売り
            self.driver.find_element_by_id("formOD0101:bsCls:1").click()
        time.sleep(2)
        dropdown = self.driver.find_element_by_id("formOD0101:conditionId")
        select = Select(dropdown)
        select.select_by_visible_text('成行(FAK)') # 成行(FAK)指定
        time.sleep(1)

        # 数量
        self.driver.find_element_by_id("formOD0101:qtyRcvd").clear()
        self.driver.find_element_by_id("formOD0101:qtyRcvd").send_keys(str(self.number))# 数量指定

        # 有効期間設定
        self.driver.find_element_by_id("formOD0101:durationId:0").click()
        
    #
    # 先物オプション取引実行（決済）
    #
    def closeSakimonoOption(self):
        self.logger.info('先物オプション決済実行開始')
        # フレーム切替
        frame = self.driver.find_element_by_name("menu")
        self.driver.switch_to_frame(frame)
        frame = self.driver.find_element_by_name("menuBody")
        self.driver.switch_to_frame(frame)
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.XPATH, "//*[@id='menu20']")))
        self.driver.find_element_by_xpath("//*[@id='menu20']").click() # 取引クリック
        time.sleep(2)
        self.driver.find_element_by_id("formCM0004:subMenu24").click() # 決済注文クリック
        self.driver.switch_to.default_content() # 元のフレームに切り替え
        frame = self.driver.find_element_by_name("main")
        self.driver.switch_to_frame(frame)
        frame = self.driver.find_element_by_name("contents")
        self.driver.switch_to_frame(frame)
        self.logger.info('コンテンツ画面遷移完了')
        time.sleep(2)
        c = self.driver.find_elements_by_xpath('/html/body/div/table/tbody/tr/td/form/table[2]/tbody/tr[3]/td/span/table[2]/tbody/tr[1]/td/table/tbody/tr[1]/td[11]/a/img')
        if len(c) > 0:
            self.driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/form/table[2]/tbody/tr[3]/td/span/table[2]/tbody/tr[1]/td/table/tbody/tr[1]/td[11]/a/img").click() # 一括決済クリック
        else:
            print('決済対象なし')
            self.logger.info('決済対象なし')
            return
        time.sleep(2)
        self.logger.info('対象ポジションクリック完了')
        self.driver.find_element_by_id("formOD0201:SCR_PC_OD_0201_out:0:allButtonId").click() # 全数量
        self.driver.find_element_by_id("formOD0201:orderPatternTujyoId1").click() # 通常指定
        time.sleep(2)
        dropdown = self.driver.find_element_by_id("formOD0201:conditionId")
        select = Select(dropdown)
        select.select_by_visible_text('成行(FAK)') # 成行(FAK)指定
        self.logger.info('成行(FAK)完了')
        time.sleep(1)

        # 有効期間設定
        self.driver.find_element_by_id("formOD0201:durationId:0").click()
        
        # 確認画面の省略設定
        self.driver.find_element_by_id("formOD0201:confirmId").click()
        self.logger.info('確認画面の省略設定完了')
        
        self.driver.find_element_by_id("formOD0201:orderButtonId").click() # 注文する
        self.logger.info('先物オプション決済実行完了')
        print('先物オプション決済実行完了')
        time.sleep(10)

    #
    # 先物オプション取引実行（引成決済）
    #
    def hikeCloseSakimonoOption(self):
        self.logger.info('先物オプション決済実行開始')
        # フレーム切替
        frame = self.driver.find_element_by_name("menu")
        self.driver.switch_to_frame(frame)
        frame = self.driver.find_element_by_name("menuBody")
        self.driver.switch_to_frame(frame)
        WebDriverWait(self.driver, 30).until(expected_conditions.visibility_of_element_located((By.XPATH, "//*[@id='menu20']")))
        self.driver.find_element_by_xpath("//*[@id='menu20']").click() # 取引クリック
        time.sleep(2)
        self.driver.find_element_by_id("formCM0004:subMenu24").click() # 決済注文クリック
        self.driver.switch_to.default_content() # 元のフレームに切り替え
        frame = self.driver.find_element_by_name("main")
        self.driver.switch_to_frame(frame)
        frame = self.driver.find_element_by_name("contents")
        self.driver.switch_to_frame(frame)
        self.logger.info('コンテンツ画面遷移完了')
        time.sleep(2)
        c = self.driver.find_elements_by_xpath('/html/body/div/table/tbody/tr/td/form/table[2]/tbody/tr[3]/td/span/table[2]/tbody/tr[1]/td/table/tbody/tr[1]/td[11]/a/img')
        if len(c) > 0:
            self.driver.find_element_by_xpath("/html/body/div/table/tbody/tr/td/form/table[2]/tbody/tr[3]/td/span/table[2]/tbody/tr[1]/td/table/tbody/tr[1]/td[11]/a/img").click() # 一括決済クリック
        else:
            print('決済対象なし')
            self.logger.info('決済対象なし')
            return
        time.sleep(2)
        self.logger.info('対象ポジションクリック完了')
        self.driver.find_element_by_id("formOD0201:SCR_PC_OD_0201_out:0:allButtonId").click() # 全数量
        self.driver.find_element_by_id("formOD0201:orderPatternTujyoId1").click() # 通常指定
        time.sleep(2)
        dropdown = self.driver.find_element_by_id("formOD0201:conditionId")
        select = Select(dropdown)
        select.select_by_visible_text('引成') # 引成指定
        self.logger.info('引成完了')
        time.sleep(1)

        # 有効期間設定
        self.driver.find_element_by_id("formOD0201:durationId:0").click()
        
        # 確認画面の省略設定
        self.driver.find_element_by_id("formOD0201:confirmId").click()
        self.logger.info('確認画面の省略設定完了')
        
        self.driver.find_element_by_id("formOD0201:orderButtonId").click() # 注文する
        self.logger.info('先物オプション決済実行完了')
        print('先物オプション決済（引成決済）実行完了')
        time.sleep(10)
        
    '''
    SBI証券終了
    '''
    def exit(self):
        self.logger.info('Chromeを閉じる 開始')
        self.driver.quit()
        self.logger.info('Chromeを閉じる 完了')
    
    '''
    キャンセルメイン処理
    '''
    def start_cancel(self):
        try:
            self.logger.debug('キャンセル処理')
            # ログイン
            self.login()
            # 先物オプション取引画面へ遷移
            self.selectSakimonoOption()
            # 先物オプション取引実行
            self.cancelOrder()
            self.exit()
        except Exception as e:
            print(str(e))
            self.logger.error(str(e))
            self.driver.save_screenshot("screen.png")
            self.exit()
            
    '''
    エントリーメイン処理
    '''
    def start_entry(self, buy_price, sell_price, buyOrsell=None):
        try:
            self.logger.debug('エントリー処理')
            # ログイン
            self.login()
            # 先物オプション取引画面へ遷移
            self.selectSakimonoOption()
            # 先物オプション取引実行
            self.orderSakimonoOption(buy_price, sell_price, buyOrsell)
            self.exit()
        except Exception as e:
            print(str(e))
            self.logger.error(str(e))
            self.exit()

    '''
    決済メイン処理
    '''
    def start_close(self):
        try:
            self.logger.debug('決済処理')
            # ログイン
            self.login()
            # 先物オプション取引画面へ遷移
            self.selectSakimonoOption()
            # 先物オプション決済実行
            self.closeSakimonoOption()
            self.exit()
        except Exception as e:
            self.logger.error(str(e))
            self.exit()
    '''
    決済メイン処理
    '''
    def start_hikeClose(self):
        try:
            self.logger.debug('決済引成処理')
            # ログイン
            self.login()
            # 先物オプション取引画面へ遷移
            self.selectSakimonoOption()
            # 先物オプション引成決済実行
            self.hikeCloseSakimonoOption()
            self.exit()
        except Exception as e:
            self.logger.error(str(e))
            self.exit()

from pathlib import Path
import configparser
dic = {}
config = configparser.ConfigParser()
path = os.path.join(Path(__file__).parent, "config.ini")
print(path)
config.read(path, encoding='utf-8')
config.optionxform = str
for section in config.sections(): # ini ファイルの値をディクショナリに格納
    for key in config.options(section):
        dic[key] = config.get(section, key)
print(dic)
if __name__ == '__main__':
    print("=== Start ===")
    sbi = SBI_Utility(
        userId=dic['user_id'],
        driver_path=dic['driver_path'],
        pw=dic['user_password'],
        orderPw=dic['order_password'],
        month=dic['month'],
        number=dic['qty']
        )
    # sbi.start_entry(50000,10000)
    # sbi.start_close()

    print("=== Finish ===")


