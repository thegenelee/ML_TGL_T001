import yfinance as yf
import pandas as pd
from datetime import date
import requests

from bs4 import BeautifulSoup
#獲取目前SP500 PE ratio
url = 'https://www.multpl.com/s-p-500-pe-ratio'

# 发送HTTP GET请求并获取网页内容
response = requests.get(url)
html_content = response.text

# 使用BeautifulSoup解析HTML内容
soup = BeautifulSoup(html_content, 'html.parser')

# 找到PE比率所在的HTML元素
pe_ratio_element = soup.find('div', {'id': 'current'}) 

# 提取PE比率数值并删除多余字符和空格
pe_ratio = pe_ratio_element.text.split(':')[1].strip().split()[0]

pe_msg=['SP500 PE ratio:', pe_ratio+' ,21為均價']


# 獲取今天的日期
today = date.today()

# 用於存儲發送到Line Notify的訊息
line_notify_messages = []

# 構造日期訊息字串
date_message = f"{today}\n"

# 股票代號和名稱字典
stock_dict = {
    '0050.TW': '台灣50',
    '2002.TW': '中鋼',
    '^DJI': '美國道瓊',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^SOX': '費城半導體'
}

# 獲取股票數據並計算相關指標
for stock in stock_dict.keys():
    df = yf.download(stock, period="max")

    # 计算日、周和月的KD指标
    df['High_MA_Daily'] = df['High'].rolling(window=9).max()
    df['Low_MA_Daily'] = df['Low'].rolling(window=9).min()
    df['Close_MA_Daily'] = df['Close'].rolling(window=9).mean()
    df['RSV_Daily'] = (df['Close'] - df['Low_MA_Daily']) / (df['High_MA_Daily'] - df['Low_MA_Daily'])
    df['K_Daily'] = df['RSV_Daily'].rolling(window=3).mean()
    df['D_Daily'] = df['K_Daily'].rolling(window=3).mean()

    df_weekly = df.resample('W').last()
    df_weekly['High_MA_Weekly'] = df_weekly['High'].rolling(window=9).max()
    df_weekly['Low_MA_Weekly'] = df_weekly['Low'].rolling(window=9).min()
    df_weekly['Close_MA_Weekly'] = df_weekly['Close'].rolling(window=9).mean()
    df_weekly['RSV_Weekly'] = (df_weekly['Close'] - df_weekly['Low_MA_Weekly']) / (df_weekly['High_MA_Weekly'] - df_weekly['Low_MA_Weekly'])
    df_weekly['K_Weekly'] = df_weekly['RSV_Weekly'].rolling(window=3).mean()
    df_weekly['D_Weekly'] = df_weekly['K_Weekly'].rolling(window=3).mean()

    df_monthly = df.resample('M').last()
    df_monthly['High_MA_Monthly'] = df_monthly['High'].rolling(window=9).max()
    df_monthly['Low_MA_Monthly'] = df_monthly['Low'].rolling(window=9).min()
    df_monthly['Close_MA_Monthly'] = df_monthly['Close'].rolling(window=9).mean()
    df_monthly['RSV_Monthly'] = (df_monthly['Close'] - df_monthly['Low_MA_Monthly']) / (df_monthly['High_MA_Monthly'] - df_monthly['Low_MA_Monthly'])
    df_monthly['K_Monthly'] = df_monthly['RSV_Monthly'].rolling(window=3).mean()
    df_monthly['D_Monthly'] = df_monthly['K_Monthly'].rolling(window=3).mean()

    # 获取最新的日、周和月的KD值
    latest_k_daily = round(df['K_Daily'][-1], 2)
    latest_d_daily = round(df['D_Daily'][-1], 2)
    latest_k_weekly = round(df_weekly['K_Weekly'][-1], 2)
    latest_d_weekly = round(df_weekly['D_Weekly'][-1], 2)
    latest_k_monthly = round(df_monthly['K_Monthly'][-1], 2)
    latest_d_monthly = round(df_monthly['D_Monthly'][-1], 2)

    # 获取历史最高价
    historical_high = df['Close'].max()

    # 计算与历史最高价的差距百分比
    current_price = df['Close'].iloc[-1]
    price_diff_percentage = round((current_price - historical_high) / historical_high * 100, 1)

    # 输出股票代号、名称和与历史高点的差距百分比
    stock_name = stock_dict.get(stock, '')
    print(f"{stock_name}, 距高点{price_diff_percentage}%")

    # 输出日、周和月的KD值和收盘价
    print("值| 日 | 周 | 月 |   價")
    print(f"K |{latest_k_daily:.2f}|{latest_k_weekly:.2f}|{latest_k_monthly:.2f}| {historical_high:.2f}(史高)")
    print(f"D |{latest_d_daily:.2f}|{latest_d_weekly:.2f}|{latest_d_monthly:.2f}| {current_price:.2f}(現價)")
    # 構造股票訊息字串
    stock_name = stock_dict.get(stock, '')
    stock_message = f"{stock_name}，距高點{price_diff_percentage}%\n"
    stock_message += "值 |  日  |  周  |  月  |     價\n"
    stock_message += f"K  | {latest_k_daily:.2f} | {latest_k_weekly:.2f} | {latest_k_monthly:.2f} | {historical_high:.2f}(史高)\n"
    stock_message += f"D  | {latest_d_daily:.2f} | {latest_d_weekly:.2f} | {latest_d_monthly:.2f} | {current_price:.2f}(現價)\n"

    # 將股票訊息添加到列表中
    line_notify_messages.append(stock_message)

# 合併日期訊息和股票訊息
message = date_message +'\n'.join(pe_msg)+'\n' + '\n'.join(line_notify_messages)

# Line Notify訪問令牌
access_token = "line token"

# 發送訊息到Line Notify
url = "https://notify-api.line.me/api/notify"
headers = {
    "Authorization": "Bearer " + access_token,
    "Content-Type": "application/x-www-form-urlencoded"
}
payload = {"message": message}
response = requests.post(url, headers=headers, data=payload)
print(response.text)