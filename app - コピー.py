import streamlit as st
import pandas as pd
import math
import sys
import altair as alt
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

st.title('管理図作成app')
st.sidebar.write('## 条件指定')

# メッセージボックスを表示する関数
def show_message(title, message):
    messagebox.showinfo(title, message)
# ファイル選択ダイアログを表示し、選択されたファイルのパスを取得
file_path = filedialog.askopenfilename()
# ファイルパスが選択された場合は、処理を実行
if not file_path:
    # ファイルが選択されなかった場合の処理
    show_message('処理中断',"ファイルが選択されませんでした。")
    sys.exit()

df = pd.read_csv(file_path, encoding='cp932')


#以降、サンプルコードのまま
ad_cost = st.sidebar.slider('advertisement_cost', 1000, 9000)*1.0E+04
fixed_cost = 1000*1.0E+04
cost = ad_cost+fixed_cost

def calc_earnings(ad_cost):
    earnings = 2.87E+07*math.log(ad_cost)-4.44E+08
    return int(earnings)

def calc_profit(earnings, cost):
    profit= earnings-cost
    return int(profit)

earnings = calc_earnings(ad_cost)
profit = calc_profit(earnings, cost)
profit_ratio = int((profit/earnings)*100)

data_ad_cost = list(range(1000, 9001, 1))
data_earnings = [calc_earnings(ad_cost*1.0E+04)
                 for ad_cost in data_ad_cost]
data_profit = [calc_profit(earnings, ad_cost*1.0E+04+fixed_cost)
               for earnings, ad_cost in zip(data_earnings, data_ad_cost)]

max_profit = max(data_profit)
best_ad_cost = data_ad_cost[data_profit.index(max_profit)]

#make columns
col1, col2, col3 = st.columns(3)
col1.metric('cost', f'{int(cost/1.0E+06)} MYen')
col1.metric('best_advertisement_cost', f'{best_ad_cost/100} MYen')
col2.metric('simulated_earnings', f'{int(earnings/1.0E+06)} MYen')
col3.metric('simuleted_profit', f'{int(profit/1.0E+06)} MYen', f'{profit_ratio}%')
col3.metric('simulated_max_profit', f'{int(max_profit/1.0E+06)} MYen')

df_earnings = pd.DataFrame()
df_earnings['ad_cost'] = data_ad_cost
df_earnings['value'] = data_earnings
df_earnings['indicator'] = 'earnings'

df_profit = pd.DataFrame()
df_profit['ad_cost'] = data_ad_cost
df_profit['value'] = data_profit
df_profit['indicator'] = 'profit'

df = pd.concat([df_earnings, df_profit])
df['value'] = df['value']/1.0E+06

#graph_setting by Altair
chart = alt.Chart(df).mark_line().encode(
    alt.X('ad_cost', title='advertisement_cost (MYen)'), 
    alt.Y('value', title='earnings_and_profit (MYen)'), 
    color = 'indicator'
).configure_axis(
    labelFontSize=12, 
    titleFontSize=16, 
).configure_legend(
    titleFontSize=12, 
    labelFontSize=16, 
)

st.write('## earnings & profit simulation by advertisement cost')
st.altair_chart(chart, use_container_width=True)