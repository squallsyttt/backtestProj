#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据处理辅助模块：包含期权数据的处理和筛选逻辑
"""

import pandas as pd
import os

class DataProcessor:
    """
    数据处理辅助类：包含期权数据的处理和筛选逻辑
    """
    
    OPTION_MAP = {
        '500': '500ETF',
        '1000': '1000ETF'
    }

    def __init__(self, pro_api):
        """
        初始化
        
        参数:
            pro_api: Tushare pro_api 实例
        """
        self.pro = pro_api

    def get_opt_basic(self, exchange='SSE', start_date='20240101', end_date='20240105'):
        ts_data = self.pro.opt_basic(
            exchange=exchange,
            fields='ts_code,name,opt_code,opt_type,call_put,exercise_price,maturity_date,list_date,delist_date'
        )
        # 获取后存到文件中
        curret_script_path = os.path.abspath(__file__)
        data_dir = os.path.dirname(curret_script_path)
        folder_path = os.path.join(data_dir, 'opt_basic',exchange)
        file_name = 'opt_basic_SSE.csv'
        opt_basic_file = os.path.join(folder_path, file_name)

        if not os.path.exists(opt_basic_file):
            self.save_csv_data_simple(ts_data, folder_path, file_name)
        else:
            print(f"文件{opt_basic_file}已存在")
        return ts_data

    def get_opt_specific(self, opt_basic_data, trade_date, option_type='500', exchange='SSE'):
        keyword_option = self.OPTION_MAP.get(option_type, '500ETF')
        opt_500etf = opt_basic_data.loc[opt_basic_data['name'].str.contains(keyword_option)]
        current_script_path = os.path.abspath(__file__)
        data_dir = os.path.dirname(current_script_path)
        folder_path = os.path.join(data_dir, 'opt_specific', exchange)
        file_name = 'opt_specific_500etf.csv'
        opt_specific_file = os.path.join(folder_path, file_name)
        if not os.path.exists(opt_specific_file):
            self.save_csv_data_simple(opt_500etf, folder_path, file_name)
        else:
            print(f"文件{opt_specific_file}已存在")
        return opt_500etf

    def save_csv_data_simple(self, data, folder_path, file_name):
        """
        保存数据到CSV文件
        参数:
            data (pandas.DataFrame): 要保存的数据
            folder_path (str): 文件夹路径
            file_name (str): 文件名称
        """

        print(f"尝试保存到: {folder_path+file_name}")
        print(f"目录是否存在: {os.path.exists(folder_path)}")
        print(f"写入权限: {os.access(folder_path, os.W_OK)}")

        # 确保文件夹存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, file_name)
        # 保存数据到CSV文件
        data.to_csv(file_path, index=False)
        print(f"数据已保存至 {file_path}")
        return 1
    
    def get_etf_price(self, ts_code, start_date, end_date):
        """
        获取指定ETF的价格数据

        参数:
            ts_code (str): ETF的代码，如 '510500.SH' 或 '512100.SH'
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD

        返回:
            pandas.DataFrame: 指定ETF的价格数据
        """
        # 获取指定ETF的日线数据
        df = self.pro.fund_daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            fields='ts_code,trade_date,open,high,low,close,vol,amount'
        )

        # 按日期升序排序
        df = df.sort_values('trade_date')

        # 将日期列转换为datetime格式
        df['trade_date'] = pd.to_datetime(df['trade_date'])

        return df
