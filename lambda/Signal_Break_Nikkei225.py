import pandas as pd
import pandas.tseries.offsets as offsets
import math
from decimal import Decimal
import datetime as dt
import csv
import requests

import os
def send_line_notify(notification_message):
    """
    LINEに通知する
    """
    line_notify_token = 'xxxxxxxxxxxx'
    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_notify_token}'}
    data = {'message': f'{notification_message}'}
    requests.post(line_notify_api, headers = headers, data = data)

def getSessionDF():
    dictDF = pd.read_excel('/tmp/N225minif_2021.xlsx', index_col=0, engine='openpyxl', sheet_name=['日中日足', 'ナイト場足','取引日日足'])
    dictDF['日中日足'] = dictDF['日中日足'].drop("Unnamed: 6", axis=1)
    dictDF['日中日足']['flg'] = 1
    dictDF['ナイト場足']['flg'] = 0

    df = pd.concat([dictDF['日中日足'], dictDF['ナイト場足']], axis=0).reset_index().sort_values(['日付', 'flg'])
    try:
        df = df.drop(df.columns[[6]], axis=1)
    except:
        pass
    feature = ['date', 'open', 'high', 'low', 'close','vol']
    df.columns = feature
    # df = df.set_axis(['date', 'open', 'high', 'low', 'close','vol'], axis=1)
    return df

def getTorihikiDay():
    dictDF = pd.read_excel('N225minif_2021.xlsx', index_col=0, engine='openpyxl', sheet_name=['日中日足', 'ナイト場足','取引日日足'])
    dictDF['取引日日足'].columns = ['取引日_始値','取引日_高値','取引日_安値','取引日_終値','取引日_出来高']
    df = pd.concat([dictDF['取引日日足']], axis=1)
    df = df.reset_index()
    df['日付'] = pd.to_datetime(df['日付'])
    try:
        df = df.drop(df.columns[[6]], axis=1)
    except:
        pass
    df = df.set_axis(['date', 'open', 'high', 'low', 'close','vol'], axis=1)
    return df

def getSignal():
    df = getSessionDF()
    df['upper']    = df['high']
    df['lower']    = df['low']
    row = df.tail(1)
    msg = '''
    戦略:{}
    高値：{}
    安値：{}
    '''
    send_line_notify(msg.format('ブレイクアウト',row.iloc[0]['upper'], row.iloc[0]['lower']))
    return row.iloc[0]['upper'], row.iloc[0]['lower']
