import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import altair as alt
import plotly.express as px
import plotly.graph_objs as go

from functions import *


## Seting page style
page_style()

# Set dashboard title
st.header(":rotating_light: 전력소비량 모니터링 Dashboard") ## emoji: rotating_light / battery / zap
st.subheader(" ")
st.subheader(" ")

# Set view date
today = datetime.now().date() - relativedelta(years=4)
yesterday = today - timedelta(1)

st.sidebar.subheader("조회 기간 설정")
startday_filter = st.sidebar.slider('최근 n일 기록을 조회합니다.', 1, 60, 30) # 사이드바에 넣을 경우
startday = today - timedelta(startday_filter)


### Load Dataset + View recent n days
df = load_dataset()
df_n = df[(df['date']>=startday)&(df['date']<=today)]


### Page Layout

# Layout - lv.1
layout_lv1(df_n)

# Layout - lv.2
layout_lv2(df_n)

# Layout - lv.3
layout_lv3(df_n)


### Download raw data

st.sidebar.subheader("데이터 원본 다운로드")

# button 1
daily_anomaly = df_n.groupby('date')[['total_kW_sum','warning_yn','danger_yn']].sum().reset_index()\
                    .rename(columns={'total_kW_sum':'total_consumption','warning_yn':'warning', 'danger_yn':'danger'})

download_button(daily_anomaly,'일자별 전력소비량', 'daily_power_consumption_data.csv')

# button 2
hourly_anomaly = df_n.groupby(['date','hour'])[['total_kW_sum','warning_yn','danger_yn']].sum().reset_index()\
                     .rename(columns={'total_kW_sum':'total_consumption','warning_yn':'warning', 'danger_yn':'danger'})

download_button(hourly_anomaly,'일자별,시간대별 전력소비량', 'daily_hourly_power_consumption_data.csv')
