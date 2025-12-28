import ccxt
import pandas as pd
import numpy as np
from scipy.spatial.distance import euclidean
import plotly.graph_objects as go

# 1. اتصال به Binance و دریافت داده‌ها
def get_data(symbol, timeframe, limit=200):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    return data

# 2. محاسبه درصد تغییرات قیمت نسبت به کندل قبلی
def calculate_percent_changes(data):
    data['percent_change'] = data['close'].pct_change() * 100
    data = data.dropna(subset=['percent_change'])  # حذف NaN‌ها
    return data

# 3. محاسبه شباهت بین دو پنجره
def calculate_similarity(window1, window2):
    # محاسبه درصد تغییرات قیمت برای دو پنجره
    window1_changes = window1['percent_change'].values
    window2_changes = window2['percent_change'].values

    # اطمینان از اینکه اندازه‌ها برابرند
    min_length = min(len(window1_changes), len(window2_changes))
    window1_changes = window1_changes[:min_length]
    window2_changes = window2_changes[:min_length]

    # مقایسه تغییرات درصدی
    return euclidean(window1_changes, window2_changes)

# 4. محاسبه درصد شباهت
def calculate_similarity_percentage(similarity, max_similarity=0):
    # درصد شباهت معکوس فاصله (برای شباهت بالا، مقدار کمتر و درصد بیشتر)
    similarity_percentage = (1 / (1 + similarity)) * 100
    return similarity_percentage

# 5. تقسیم داده‌ها به بخش‌های 50 کندلی
def split_to_windows(data, window_size=50):
    windows = []
    for i in range(len(data) - window_size):
        windows.append(data.iloc[i:i+window_size])
    return windows

# 6. رسم نمودار کندل‌استیک با Plotly
def plot_candlestick(data, title="Candlestick Chart"):
    fig = go.Figure()

    # رسم هر کندل
    for i, row in data.iterrows():
        color = 'green' if row['close'] > row['open'] else 'red'
        fig.add_trace(go.Candlestick(
            x=[row['timestamp']],
            open=[row['open']],
            high=[row['high']],
            low=[row['low']],
            close=[row['close']],
            increasing_line_color='green', 
            decreasing_line_color='red'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False
    )
    
    fig.show()

# 7. اجرای مراحل اصلی
if __name__ == "__main__":
    symbol = "BTC/USDT"  # نماد بیت‌کوین به تتر
    timeframe = "1h"  # تایم‌فریم یک ساعته

    # دریافت داده‌ها
    data = get_data(symbol, timeframe)

    # محاسبه درصد تغییرات قیمت
    data = calculate_percent_changes(data)

    # تقسیم داده‌ها به پنجره‌های 50 کندلی
    historical_windows = split_to_windows(data, window_size=50)

    # انتخاب 50 کندل اخیر (برای مقایسه)
    recent_candles = data.tail(50)

    # محاسبه شباهت الگوها و درصد شباهت
    similarities = []
    for i, window in enumerate(historical_windows):
        similarity = calculate_similarity(recent_candles, window)
        similarity_percentage = calculate_similarity_percentage(similarity)
        similarities.append((i, similarity_percentage))

    # مرتب‌سازی بر اساس درصد شباهت
    similarities_sorted = sorted(similarities, key=lambda x: x[1], reverse=True)

    # نمایش نتایج
    for index, similarity_percentage in similarities_sorted[:3]:  # نمایش 3 پنجره با بیشترین شباهت
        print(f"Window {index + 1}: Similarity: {similarity_percentage:.2f}%")

    # رسم کندل‌استیک 50 کندل اخیر
    plot_candlestick(recent_candles, title="Recent Candles")

    # رسم کندل‌استیک 3 پنجره مشابه
    for i, (index, _) in enumerate(similarities_sorted[:3]):
        similar_window = historical_windows[index]
        plot_candlestick(similar_window, title=f"Similar Pattern {i+1}")
