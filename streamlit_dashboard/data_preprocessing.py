import pandas as pd
import numpy as np

# load dataset
df = pd.read_parquet('streamlit/data/power_consumption_dataset.parquet')

df = df.loc[:, df.columns.str.contains('kW')]

df['total_kW_sum'] = df.sum(axis=1)
df['F1'] = df.loc[:, df.columns.str.contains('Floor1')].sum(axis=1)
df['F2'] = df.loc[:, df.columns.str.contains('Floor2')].sum(axis=1)
df['F3'] = df.loc[:, df.columns.str.contains('Floor3')].sum(axis=1)
df['F4'] = df.loc[:, df.columns.str.contains('Floor4')].sum(axis=1)
df['F5'] = df.loc[:, df.columns.str.contains('Floor5')].sum(axis=1)
df['F6'] = df.loc[:, df.columns.str.contains('Floor6')].sum(axis=1)
df['F7'] = df.loc[:, df.columns.str.contains('Floor7')].sum(axis=1)
df['Zone1'] = df.loc[:, df.columns.str.contains('z1')].sum(axis=1)
df['Zone2'] = df.loc[:, df.columns.str.contains('z2')].sum(axis=1)
df['Zone3'] = df.loc[:, df.columns.str.contains('z3')].sum(axis=1)
df['Zone4'] = df.loc[:, df.columns.str.contains('z4')].sum(axis=1)
df['Zone5'] = df.loc[:, df.columns.str.contains('z5')].sum(axis=1)

# df = df[['total_kW_sum']]
df = df[['total_kW_sum',
         'F1', 'F2', 'F3', 'F4', 'F5','F6', 'F7',
         'Zone1', 'Zone2','Zone3', 'Zone4', 'Zone5']]

df = pd.DataFrame(df.resample('H').sum()) # 1시간 단위의 총 소비 전력량 계산
df = df.rename_axis('ts').reset_index()
df = df[(df['ts']>='2019-01-01 00:00:00')&(df['ts']<='2019-12-31 23:00:00')] # 1년치만 분석

df['date'] = df['ts'].dt.date
df['weekday'] = df['ts'].dt.weekday
df['workingday'] = np.where(df['weekday']>4, 0, 1)
df['hour'] = df['ts'].dt.hour

df.shape

df.to_parquet('streamlit/data/power_consumption_2019_preprocessed.parquet')