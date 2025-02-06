# -*- coding: utf-8 -*-
"""
Created on Tue May 16 20:31:45 2023

@author: 61721
"""

from scripts.ticket import denoised_corr
import pandas as pd
import NCO_weights
from datetime import timedelta
import numpy as np
import matplotlib.pylab as plt

plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def time(data, col):
    times = data[col].astype(str)
    formatStr = '%Y-%m-%d'
    data.index = pd.to_datetime(times, format=formatStr)
    data = data.drop(columns=[col])
    return data


if __name__ == '__main__':
    df_1 = pd.read_csv('C:\\jupyter_work\\port_mana\\FOF_20221208.csv', encoding='gbk', index_col=0)
    df_1.index = pd.to_datetime(df_1.index)

    start = '2021-9-28'
    # end = '2023-5-12'
    # cor = denoised_corr.cal_corr(df_1,start,end)[0]
    # cov = denoised_corr.cal_corr(df_1,start,end)[1]
    # annual_rtns = denoised_corr.cal_corr(df_1,start,end)[2]

    # w = NCO_weights.nco_weights(cov,cor,annual_rtns)[2]
    # w1 = NCO_weights.nco_weights(cov,cor,annual_rtns)[0]['NCO']

    ### get rebalance date
    adjustment_date = pd.read_csv('C:\\jupyter_work\VIX计算\\etf_300calllist.csv').sort_values('delist_date')
    adjustment_date = time(adjustment_date, col='delist_date')
    adjustment_date_list = adjustment_date.index.drop_duplicates().to_list()


    weight_list = []
    rebalance_list = []

    test_df = df_1['2022-09-28':]

    for idx, row in test_df.iterrows():
        if idx in adjustment_date_list:
            end = (idx - timedelta(days=1)).strftime('%Y-%m-%d')
            print(end)
            cor = denoised_corr.cal_corr(df_1, start, end)[0]
            cov = denoised_corr.cal_corr(df_1, start, end)[1]
            annual_rtns = denoised_corr.cal_corr(df_1, start, end)[2]
            weight_list.append(NCO_weights.nco_weights(cov, cor, annual_rtns)[0]['NCO'])
            rebalance_list.append(idx.strftime('%Y-%m-%d'))
        else:
            pass

#P&L
test = df_1['2022-09-28':].pct_change().dropna()
port = []
nav = []
data = []
for i in range(len(rebalance_list)):
    print(i)
    if i < len(rebalance_list)-1 :
        port.append(test[rebalance_list[i]:rebalance_list[i+1]])
    else:
        port.append(test[rebalance_list[i]:])
    

## reorder the columns
for i in range(len(port)):
    for j in range(len(weight_list[0].index)):
        nav.append(port[i][weight_list[0].index[j]])
    w = pd.DataFrame(nav,index=weight_list[0].index).T
    data.append(w)
    nav = []
## calculate day return
net_asset_value = []
for i in range(len(data)):
    ret = np.dot(data[i],weight_list[i])
    net_asset_value.append(ret)
    
dret = []
for i in range(len(net_asset_value)):
    if i < len(net_asset_value) -1 :
        ret_list = net_asset_value[i].tolist()[:-1]
        dret = dret + ret_list
    else:
        dret = dret + net_asset_value[i].tolist()
        
df3 = pd.DataFrame(dret,index=test.index)
df3[[0]].cumsum().apply(np.exp).plot(figsize=(11, 6))

df3.to_csv('nav.csv')
