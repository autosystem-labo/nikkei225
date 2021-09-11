import json
import os
from pathlib import Path
import configparser
# from selenium import webdriver
from labo225 import LABO225_Utility
from SBICommon import SBI_Utility
import Signal_Break_Nikkei225


def lambda_handler(event, context):
    
    try:      
        print(event['trigger'])
    except Exception as e:
        print(e)
        result = {
          'statusCode': 200,
          'body': '日経データ取得失敗'
        }
        return result
    dic = {}
    config = configparser.ConfigParser()
    path = os.path.join(Path(__file__).parent, "config.ini")
    config.read(path, encoding='utf-8')
    config.optionxform = str
    for section in config.sections(): # ini ファイルの値をディクショナリに格納
        for key in config.options(section):
            dic[key] = config.get(section, key)
    #
    # 225LABOからデータ取得
    #
    dic = {}
    config = configparser.ConfigParser()
    path = os.path.join(Path(__file__).parent, "config.ini")
    config.read(path, encoding='utf-8')
    config.optionxform = str
    for section in config.sections(): # ini ファイルの値をディクショナリに格納
        for key in config.options(section):
            dic[key] = config.get(section, key)

    labo = LABO225_Utility(
        userId=dic['labo_user_id'],
        driver_path=dic['driver_path'],
        pw=dic['labo_user_password']
        )
    labo.start_download()
    buy_price, sell_price = Signal_Break_Nikkei225.getSignal()
    
    sbi = SBI_Utility(
        userId=dic['user_id'],
        driver_path=dic['driver_path'],
        pw=dic['user_password'],
        orderPw=dic['order_password'],
        month=dic['month'],
        number=dic['qty']
        )
    sbi.start_cancel()
    
    sbi = SBI_Utility(
        userId=dic['user_id'],
        driver_path=dic['driver_path'],
        pw=dic['user_password'],
        orderPw=dic['order_password'],
        month=dic['month'],
        number=dic['qty']
        )
    sbi.start_close()
    
    sbi = SBI_Utility(
        userId=dic['user_id'],
        driver_path=dic['driver_path'],
        pw=dic['user_password'],
        orderPw=dic['order_password'],
        month=dic['month'],
        number=dic['qty']
        )
    sbi.start_entry(buy_price,sell_price)

    result = {
       'statusCode': 200,
       'body': '成功'
    }
   
    return result