import streamlit as st
import pandas as pd
import altair as alt
import statistics

#初期値 (ファイル読み込み前のエラー防止)
item_list=[]
coa_list=[]
stratify_list=[None]
df = pd.DataFrame()

#タイトル
st.title('管理図作成app')
#解析対象ファイルの読み込みボタン
uploaded_file = st.file_uploader("管理図作成アプリ読み込み用.csvを読み込んでください")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='cp932')
    item_list = sorted(df['item'].unique())
    
    thickness_list = sorted(df['膜厚'].unique())
    if len(thickness_list)>1:
        stratify_list = [None, 'coating', '膜厚']
    st.write('ファイルは正常に読み込まれました')

#サイドバーに表示する項目
st.sidebar.write('## 条件指定')
item_select = st.sidebar.selectbox("品種", item_list)
if uploaded_file is not None:
    df = df[df['item']==item_select]
    coa_list = sorted(df['検査項目'].unique())
    coa_select = st.sidebar.selectbox("検査項目", coa_list)
    if len(thickness_list)>1:
        min_thickness = st.sidebar.number_input("解析対象の膜厚(下限)",step=2.5)
        max_thickness = st.sidebar.number_input("解析対象の膜厚(上限)", value=200.0, step=2.5)
    stratify = st.sidebar.selectbox("層別", stratify_list)

#sidebarの絞り込み条件に応じてデータを絞り込む
if item_select is not None:
    df = df[df['item']==item_select]
    df = df[df['検査項目']==coa_select]
    if len(thickness_list)>1:
        df = df[df['膜厚']>=min_thickness]
        df = df[df['膜厚']<=max_thickness]

#CLCRの算出式を定義
def calc_UCLCR(data, UCL):
    mean_value = statistics.mean(data)
    std_value = statistics.stdev(data)
    if std_value != 0:
        UCLCR = ((mean_value+3*std_value)-UCL)/std_value
        UCLCR = round(UCLCR,2)
    else: UCLCR = "-"
    return UCLCR

def calc_LCLCR(data, LCL):
    mean_value = statistics.mean(data)
    std_value = statistics.stdev(data)
    if std_value != 0:
        LCLCR = (LCL - (mean_value-3*std_value))/std_value
        LCLCR = round(LCLCR,2)
    else: LCLCR = "-"
    return LCLCR

if uploaded_file is not None:

    try:
        #検査項目が選択された場合、SL, CLを取得する
        #SLはグラフの表示範囲設定用なのでそれほど重要ではない
        #但し、膜厚によってCLが異なる場合はメトリクスにはvariousと表示し、グラフは各点に応じたCLを表示する
        if coa_select is not None:
            USL = max(df['USL'])
            LSL = min(df['LSL'])
            if len(df['UCL'].unique())==1:
                cur_UCL = max(df['UCL'])
                cur_UCLCR = calc_UCLCR(df['測定値'], cur_UCL)
            else:
                cur_UCL = 'various'
                cur_UCLCR = '-'
            if len(df['LCL'].unique())==1:
                cur_LCL = min(df['LCL'])
                cur_LCLCR = calc_LCLCR(df['測定値'], cur_LCL)
            else:
                cur_LCL = 'various'
                cur_LCLCR = '-'
            # 新UCL,LCL設定欄を表示させる。数値を入れると自動でCLCRが計算される
            # 最初から表示しないのは、初期値を実際のUCL,LCLに近い値にしていないとグラフ表示がエラーするため
            new_UCL = st.sidebar.number_input('UCL案を入力', value=max(df["UCL"]))
            new_UCLCR = calc_UCLCR(df['測定値'], new_UCL)
            new_LCL = st.sidebar.number_input('LCL案を入力', value=min(df["LCL"]))
            new_LCLCR = calc_LCLCR(df['測定値'], new_LCL)

            df['new_UCL'] = new_UCL
            df['new_LCL'] = new_LCL
            # チャート、新旧UCL,LCLを重ね書きする
            # ベースの横軸
            base = alt.Chart(df).encode(alt.X('受入日:T', title='date'))
            
            # チャート、サイドバーで層別をNone以外で選択肢ていれば層別する
            selection = alt.selection_multi(fields=['coating'], bind='legend')

            if stratify is not None:
                chart = base.mark_line().encode(
                    alt.Y('測定値:Q', title=f'{coa_select} 測定実績', scale=alt.Scale(domain=[LSL, USL])), 
                    color = stratify, opacity=alt.condition(selection, alt.value(1), alt.value(0.1))).add_selection(selection)
            else: 
                chart = base.mark_line().encode(
                    alt.Y('測定値:Q', title=f'{coa_select} 測定実績', scale=alt.Scale(domain=[LSL, USL])))
            # 新旧CL
            UCL_line = base.mark_line(color="green").encode(alt.Y('UCL:Q'))
            LCL_line = base.mark_line(color="green").encode(alt.Y('LCL:Q'))
            new_UCL_line = base.mark_line(color="red", strokeDash=[1,1]).encode(alt.Y("new_UCL:Q"))
            new_LCL_line = base.mark_line(color="red", strokeDash=[1,1]).encode(alt.Y("new_LCL:Q"))
            # 上記を重ねる
            layer = alt.layer(chart, UCL_line, LCL_line, new_UCL_line, new_LCL_line)
            # タイトル
            st.write('## Trend chart')
            st.altair_chart(layer, use_container_width=True)

        # メトリクスの表示、データ取り込み前の初期値は - としておく
        col1, col2, col3 = st.columns(3)
        if item_select is None:
            col1.metric('N', '-')
            col1.metric('Average', '-')
            col1.metric('Std.', '-')
            col2.metric('Current UCL', '-')
            col2.metric('Current LCL', '-')
            col3.metric('New UCL', '-')
            col3.metric('New LCL', '-')

        else:
            col1.metric('N', len(df['測定値']))
            col1.metric('Average', round(statistics.mean(df['測定値']),1))
            col1.metric('Std.', round(statistics.stdev(df['測定値']),2))
            col2.metric('Current UCL', cur_UCL, help='variousと表示される場合は膜厚範囲を絞り込んでください')
            col2.metric('Current UCLCR', cur_UCLCR)
            col2.metric('Current LCL', cur_LCL, help='variousと表示される場合は膜厚範囲を絞り込んでください')
            col2.metric('Current LCLCR', cur_LCLCR)
            col3.metric('New UCL', new_UCL)
            col3.metric('New UCLCR', new_UCLCR)
            col3.metric('New LCL', new_LCL)
            col3.metric('New LCLCR', new_LCLCR)
    except:
        st.write('## 表示するデータがありません。\n### データ範囲を拡げてください。')
