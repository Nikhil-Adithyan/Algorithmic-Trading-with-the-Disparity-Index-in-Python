# IMPORTING PACKAGES

import numpy as np
import requests
import pandas as pd
import matplotlib.pyplot as plt
from math import floor
from termcolor import colored as cl

plt.style.use('fivethirtyeight')
plt.rcParams['figure.figsize'] = (20,10)


# EXTRACTING STOCK DATA

def get_historical_data(symbol, start_date):
    api_key = 'YOUr API KEY'
    api_url = f'https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=5000&apikey={api_key}'
    raw_df = requests.get(api_url).json()
    df = pd.DataFrame(raw_df['values']).iloc[::-1].set_index('datetime').astype(float)
    df = df[df.index >= start_date]
    df.index = pd.to_datetime(df.index)
    return df

googl = get_historical_data('GOOGL', '2020-01-01')
print(googl.tail())


# DISPARITY INDEX CALCULATION

def get_di(data, lookback):
    ma = data.rolling(lookback).mean()
    di = ((data - ma) / ma) * 100
    return di

googl['di_14'] = get_di(googl['close'], 14)
googl = googl.dropna()
print(googl.tail())


# DISPARITY INDEX PLOT

ax1 = plt.subplot2grid((11,1), (0,0), rowspan = 5, colspan = 1)
ax2 = plt.subplot2grid((11,1), (6,0), rowspan = 5, colspan = 1)
ax1.plot(googl['close'], linewidth = 2, color = '#1976d2')
ax1.set_title('GOOGL CLOSING PRICES')
for i in range(len(googl)):
    if googl.iloc[i, 5] >= 0:
        ax2.bar(googl.iloc[i].name, googl.iloc[i, 5], color = '#26a69a')
    else:    
        ax2.bar(googl.iloc[i].name, googl.iloc[i, 5], color = '#ef5350')
ax2.set_title('GOOGL DISPARITY INDEX 14')
plt.show()


# DISPARITY INDEX STRATEGY

def implement_di_strategy(prices, di):
    buy_price = []
    sell_price = []
    di_signal = []
    signal = 0
    
    for i in range(len(prices)):
        if di[i-4] < 0 and di[i-3] < 0 and di[i-2] < 0 and di[i-1] < 0 and di[i] > 0:
            if signal != 1:
                buy_price.append(prices[i])
                sell_price.append(np.nan)
                signal = 1
                di_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                di_signal.append(0)
        elif di[i-4] > 0 and di[i-3] > 0 and di[i-2] > 0 and di[i-1] > 0 and di[i] < 0:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(prices[i])
                signal = -1
                di_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                di_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            di_signal.append(0)
            
    return buy_price, sell_price, di_signal

buy_price, sell_price, di_signal = implement_di_strategy(googl['close'], googl['di_14'])


# DISPARITY INDEX TRADING SIGNALS PLOT

ax1 = plt.subplot2grid((11,1), (0,0), rowspan = 5, colspan = 1)
ax2 = plt.subplot2grid((11,1), (6,0), rowspan = 5, colspan = 1)
ax1.plot(googl['close'], linewidth = 2, color = '#1976d2')
ax1.plot(googl.index, buy_price, marker = '^', markersize = 12, linewidth = 0, label = 'BUY SIGNAL', color = 'green')
ax1.plot(googl.index, sell_price, marker = 'v', markersize = 12, linewidth = 0, label = 'SELL SIGNAL', color = 'r')
ax1.legend()
ax1.set_title('GOOGL CLOSING PRICES')
for i in range(len(googl)):
    if googl.iloc[i, 5] >= 0:
        ax2.bar(googl.iloc[i].name, googl.iloc[i, 5], color = '#26a69a')
    else:    
        ax2.bar(googl.iloc[i].name, googl.iloc[i, 5], color = '#ef5350')
ax2.set_title('GOOGL DISPARITY INDEX 14')
plt.show()


# STOCK POSITION

position = []
for i in range(len(di_signal)):
    if di_signal[i] > 1:
        position.append(0)
    else:
        position.append(1)
        
for i in range(len(googl['close'])):
    if di_signal[i] == 1:
        position[i] = 1
    elif di_signal[i] == -1:
        position[i] = 0
    else:
        position[i] = position[i-1]
        
close_price = googl['close']
di = googl['di_14']
di_signal = pd.DataFrame(di_signal).rename(columns = {0:'di_signal'}).set_index(googl.index)
position = pd.DataFrame(position).rename(columns = {0:'di_position'}).set_index(googl.index)

frames = [close_price, di, di_signal, position]
strategy = pd.concat(frames, join = 'inner', axis = 1)

print(strategy.head())


# BACKTESTING

googl_ret = pd.DataFrame(np.diff(googl['close'])).rename(columns = {0:'returns'})
di_strategy_ret = []

for i in range(len(googl_ret)):
    returns = googl_ret['returns'][i]*strategy['di_position'][i]
    di_strategy_ret.append(returns)
    
di_strategy_ret_df = pd.DataFrame(di_strategy_ret).rename(columns = {0:'di_returns'})
investment_value = 100000
number_of_stocks = floor(investment_value/googl['close'][0])
di_investment_ret = []

for i in range(len(di_strategy_ret_df['di_returns'])):
    returns = number_of_stocks*di_strategy_ret_df['di_returns'][i]
    di_investment_ret.append(returns)

di_investment_ret_df = pd.DataFrame(di_investment_ret).rename(columns = {0:'investment_returns'})
total_investment_ret = round(sum(di_investment_ret_df['investment_returns']), 2)
profit_percentage = floor((total_investment_ret/investment_value)*100)
print(cl('Profit gained from the DI strategy by investing $100k in GOOGL : {}'.format(total_investment_ret), attrs = ['bold']))
print(cl('Profit percentage of the DI strategy : {}%'.format(profit_percentage), attrs = ['bold']))


# SPY ETF COMPARISON

def get_benchmark(start_date, investment_value):
    spy = get_historical_data('SPY', start_date)['close']
    benchmark = pd.DataFrame(np.diff(spy)).rename(columns = {0:'benchmark_returns'})
    
    investment_value = investment_value
    number_of_stocks = floor(investment_value/spy[-1])
    benchmark_investment_ret = []
    
    for i in range(len(benchmark['benchmark_returns'])):
        returns = number_of_stocks*benchmark['benchmark_returns'][i]
        benchmark_investment_ret.append(returns)

    benchmark_investment_ret_df = pd.DataFrame(benchmark_investment_ret).rename(columns = {0:'investment_returns'})
    return benchmark_investment_ret_df

benchmark = get_benchmark('2020-01-01', 100000)

investment_value = 100000
total_benchmark_investment_ret = round(sum(benchmark['investment_returns']), 2)
benchmark_profit_percentage = floor((total_benchmark_investment_ret/investment_value)*100)
print(cl('Benchmark profit by investing $100k : {}'.format(total_benchmark_investment_ret), attrs = ['bold']))
print(cl('Benchmark Profit percentage : {}%'.format(benchmark_profit_percentage), attrs = ['bold']))
print(cl('DI Strategy profit is {}% higher than the Benchmark Profit'.format(profit_percentage - benchmark_profit_percentage), attrs = ['bold']))