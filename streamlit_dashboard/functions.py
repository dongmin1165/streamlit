import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import altair as alt
import plotly.express as px
import plotly.graph_objs as go

today = datetime.now().date() - relativedelta(years=4)
yesterday = today - timedelta(1)

# Set page style
def page_style():

    st.set_page_config(page_title="streamlit_dongmin", page_icon="chart_with_upwards_trend",
                        layout="wide", initial_sidebar_state="expanded")

    css='''
    [data-testid="metric-container"] {
        width: fit-content;
        margin: auto;
    }
    [data-testid="metric-container"] > div {
        width: fit-content;
        margin: auto;
    }
    [data-testid="metric-container"] label {
        width: fit-content;
        margin: auto;
    }
    '''

    st.markdown(f'<style>{css}</style>',unsafe_allow_html=True)


# Load Dataset
def load_dataset():
    df = pd.read_parquet('streamlit_dashboard/data/power_consumption_2019_preprocessed.parquet')
    
    # 이상탐지 로직 적용
    ## D-1일까지의 누적데이터로 주중주말/시간대별 임계치 체크 - 경고: 시간대별 상위 5% / 위험:시간대별 상위 2.275%
    df_til_yesterday = df[df['date']<=yesterday]
    df_ab = df_til_yesterday.groupby(['workingday', 'hour'])['total_kW_sum'].describe(percentiles={0.95, 0.97725}).reset_index()\
                [['workingday','hour','95%','97.7%']].rename(columns={'95%':'warning_th', '97.7%':'danger_th'})

    df = df.merge(df_ab, how='left', on=['workingday', 'hour'])
    df['warning_yn'] = np.where(df['total_kW_sum'] > df['warning_th'], 1, 0)
    df['danger_yn'] = np.where(df['total_kW_sum'] > df['danger_th'], 1, 0)

    return df

# Layout Lv.1
def layout_lv1(df_n):

    col1_1, col1_2, col1_3, col1_4 = st.columns((1,1,1,1))

    WD_daily_consumption = round(df_n[df_n['workingday']==1].groupby('date')['total_kW_sum'].sum().mean(),2)
    WE_daily_consumption = round(df_n[df_n['workingday']==0].groupby('date')['total_kW_sum'].sum().mean(),2)

    with col1_1:
        st.metric(label='주중 일평균 전력소비량', value= f'{WD_daily_consumption} kWh'
                #   , delta= "+6%"
                )

    with col1_2:
        st.metric(label='주말 일평균 전력소비량', value= f'{WE_daily_consumption} kWh'
                #   , delta= "-8%"
                )

    warning_ratio = round(df_n.warning_yn.value_counts(normalize=True)[1] * 100, 2)
    danger_ratio = round(df_n.danger_yn.value_counts(normalize=True)[1] * 100, 2)

    with col1_3:
        st.metric(label='전력소비 경고 감지율', value= f'{warning_ratio} %')

    with col1_4:
        st.metric(label='전력소비 위험 감지율', value= f'{danger_ratio} %')

# Layout Lv.2

def layout_lv2(df_n):
    col2_1, col2_2 = st.columns((1,1))

    # bar chart
    bar_chart = alt.Chart(df_n).mark_bar().encode(
        x='date', y='total_kW_sum', tooltip=['date','total_kW_sum'],
        color=alt.condition(
            alt.datum.workingday == 1, alt.value('#44EE08'), alt.value('#194EFF')
        )
    ).interactive()

    bar_chart = bar_chart.configure_axis(
        labelFontSize=12, titleFontSize=12
    ).configure_title(fontSize=24)

    with col2_1:
        st.altair_chart(bar_chart, use_container_width=True)

    daily_anomaly = df_n.groupby('date')[['total_kW_sum','warning_yn','danger_yn']].sum().reset_index()\
                    .rename(columns={'total_kW_sum':'total_consumption','warning_yn':'warning', 'danger_yn':'danger'})
    daily_anomaly_melt = pd.melt(daily_anomaly, id_vars=['date'], value_vars=['warning', 'danger'])
    daily_anomaly_melt.columns = ['date','anomaly_type','detected_count']

    # line chart
    line_chart = alt.Chart(daily_anomaly_melt).mark_line().encode(
        x='date:T',
        y='detected_count:Q',
        tooltip=['date','anomaly_type','detected_count'],
        color=alt.Color('anomaly_type:N',
                        scale=alt.Scale(domain=['warning','danger'],
                                        range=['orange','red']))
    ).interactive()

    with col2_2:
        st.altair_chart(line_chart, use_container_width=True)

# Layout Lv.3

def layout_lv3(df_n):
    col3_1 = st.container()

    date_list = sorted(df_n['date'].unique())

    with col3_1:
        selected_date = st.selectbox('일자별/시간대별 상세 현황',options=date_list)
        df_day = df_n[df_n['date']==selected_date]

        fig = go.Figure()  
        fig.add_trace(go.Scatter(x=df_day['hour'], y=df_day['total_kW_sum'],
                                mode='lines+markers',
                                line=dict(color='#44EE08', width=4),
                                name='전력소비량'))
        fig.add_trace(go.Scatter(x=df_day['hour'], y=df_day['warning_th'],
                                mode='lines', 
                                line=dict(color='orange', width=1, dash='dot'),
                                name='경고 감지선'))
        fig.add_trace(go.Scatter(x=df_day['hour'], y=df_day['danger_th'],
                                mode='lines', 
                                line=dict(color='red', width=1, dash='dot'),
                                name='위험 감지선'))
        fig.update_layout(
            width=600,
            height=400,
            margin=dict(t=0, b=0, r=0, l=0),
            xaxis_title='시간', yaxis_title='전력소비량(kWh)'
        )

        st.plotly_chart(fig, use_container_width=True)

        table = df_day[['hour','total_kW_sum','warning_yn','danger_yn']]
        table.set_index('hour',inplace=True)
        table.index.name = '시간'
        table.columns = ['전력소비량','경고','위험']
        st.dataframe(table.T, use_container_width=True)

        floor_or_zone = st.radio(
            "해당 일자의 Floor / Zone 상세 조회",
            ('Floor', 'Zone'))

        if floor_or_zone == 'Floor':
            floor_options = st.multiselect(
            'Floor를 선택하세요.',
            ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7'],
            ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7'])
            fig = go.Figure()  
            for floor in floor_options:
                fig.add_trace(go.Scatter(x=df_day['hour'], y=df_day[floor],
                                        mode='lines',
                                        # line=dict(color='red', width=1),
                                        name=floor))
            fig.update_layout(
                width=600,
                height=400,
                margin=dict(t=0, b=0, r=0, l=0),
                xaxis_title='시간', yaxis_title='전력소비량(kWh)'
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            zone_options = st.multiselect(
            'Zone을 선택하세요.',
            ['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5'],
            ['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5'])
            fig = go.Figure()  
            for zone in zone_options:
                fig.add_trace(go.Scatter(x=df_day['hour'], y=df_day[zone],
                                        mode='lines',
                                        # line=dict(color='red', width=1),
                                        name=zone))
            fig.update_layout(
                width=600,
                height=400,
                margin=dict(t=0, b=0, r=0, l=0),
                xaxis_title='시간', yaxis_title='전력소비량(kWh)'
            )
            st.plotly_chart(fig, use_container_width=True)



# Download buttion for raw data 

def download_button(df, label, file_name):
    
    df_csv = df.to_csv(index=False).encode('utf-8')

    st.sidebar.download_button(
    label=label,
    data=df_csv,
    file_name=file_name
    )
