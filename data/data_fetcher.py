#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据获取模块：从Tushare获取中证500ETF期权数据
"""

import tushare as ts
import pandas as pd
import datetime
import os
import numpy as np





class DataFetcher:
    """
    数据获取类：负责从Tushare获取中证500ETF期权数据
    """

    # 定义ETF和期权相关的常量映射
    ETF_MAP = {
        '500': '510500.SH',
        '1000': '512100.SH'
    }

    OPTION_MAP = {
        '500': '500ETF',
        '1000': '1000ETF'
    }
    def __init__(self, token=None):
        """
        初始化Tushare接口
        
        参数:
            token (str): Tushare API token，如果为None则尝试从环境变量获取
        """
        if token is None:
            token = os.environ.get('TUSHARE_TOKEN')

        if token is None:
            raise ValueError("请提供Tushare API token或设置TUSHARE_TOKEN环境变量")

        ts.set_token(token)
        self.pro = ts.pro_api()

    def prepare_backtest_data(self, start_date, end_date, etf_type='500'):
        """
        准备回测所需的数据

        参数:
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD
            etf_type (str): ETF类型，'500' 或 '1000', 默认500
        返回:
            tuple: (etf_data, option_data) 用于回测的ETF和期权数据
        """

        ts_code = self.ETF_MAP.get(etf_type, '510500.SH')

        # 获取ETF价格数据
        _etf_data = self.get_etf_price(ts_code, start_date, end_date)

        # 获取期间内的所有交易日
        trade_dates = _etf_data['trade_date'].dt.strftime('%Y%m%d').tolist()

        # 获取每个交易日的平值期权数据
        all_options = []
        for date in trade_dates:
            try:
                options = self.get_atm_call_options(date, etf_type=etf_type)
                if not options.empty:
                    all_options.append(options)
            except Exception as e:
                print(f"获取{date}的{etf_type}ETF期权数据失败: {e}")

        if all_options:
            option_data = pd.concat(all_options, ignore_index=True)
            return _etf_data, option_data
        else:
            return _etf_data, pd.DataFrame()

    def prepare_backtest_data_origin(self, start_date, end_date, etf_type='500', exchange='SSE'):


        ts_code_etf = self.ETF_MAP.get(etf_type, '510500.SH')
        _etf_data = self.get_etf_price(ts_code_etf, start_date, end_date)
        # 通过etf数据 获取实际交易日
        trade_dates= _etf_data['trade_date'].dt.strftime('%Y%m%d').tolist()
        # 测试用return
        # return trade_dates

        # 获取基础期权数据
        opt_basic_data = self.get_opt_basic(exchange=exchange, start_date=start_date, end_date=end_date)

        # 基础数据中筛选出指定的期权
        opt_specific_data = self.get_opt_specific(opt_basic_data, trade_dates, option_type=etf_type, exchange=exchange)

        return opt_specific_data
        # TODO 获取所有的日数据并且持久化到文件中
        all_options = []
        # for date in trade_dates:
        #     try:
        #         option = self

        

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

    def get_option_price(self, trade_date, etf_type='500'):
        # TODO
        return 1


    def get_atm_call_options(self, trade_date, etf_type):
        """
        获取指定交易日的平值看涨期权
        
        参数:
            trade_date (str): 交易日期，格式YYYYMMDD
            etf_type (str): ETF类型，'500' 或 '1000'
            
        返回:
            pandas.DataFrame: 平值期权数据
        """

        ts_code = self.ETF_MAP.get(etf_type)
        # 获取期权链
        option_chain = self.get_option_chain(trade_date, etf_type)

        # 获取当日中证500ETF价格 直接拿开盘价格
        etf_price = self.pro.fund_daily(
            ts_code=ts_code,
            trade_date=trade_date,
            fields='open'
        )

        if etf_price.empty:
            return pd.DataFrame()

        current_price = etf_price.iloc[0]['close']

        # 计算每个期权与平值的差距
        option_chain['price_diff'] = abs(option_chain['exercise_price'] - current_price)

        # 按到期日分组，找出每组中最接近平值的看涨期权
        result = []
        for expire_date, group in option_chain.groupby('expire_date'):
            # 只选择看涨期权
            calls = group[group['call_put'] == 'C']
            if not calls.empty:
                # 找出最接近平值的期权
                atm_call = calls.loc[calls['price_diff'].idxmin()]
                result.append(atm_call)

        return pd.DataFrame(result)

    def get_option_chain(self, trade_date, etf_type):
        """
        获取指定交易日的中证500ETF期权链

        参数:
            trade_date (str): 交易日期，格式YYYYMMDD

        返回:
            pandas.DataFrame: 期权链数据
        """
        # 获取期权基础信息
        ts_code = self.ETF_MAP.get(etf_type)

        opt_basic = self.pro.opt_basic(
            exchange='SSE',
            fields='ts_code,name,call_put,exercise_price,list_date,delist_date'
        )

        # 筛选出中证500ETF期权
        opt_500etf = opt_basic.loc[opt_basic['name'].str.contains('500ETF')]

        # 获取当日期权行情数据
        opt_daily = self.pro.opt_daily(
            trade_date=trade_date,
            exchange='SSE'
        )

        # 合并基础信息和行情数据
        merged_data = pd.merge(
            opt_500etf,
            opt_daily,
            on='ts_code',
            how='inner'
        )

        # 添加到期日期（天数）
        merged_data['expire_date'] = pd.to_datetime(merged_data['delist_date'])
        merged_data['trade_date'] = pd.to_datetime(trade_date)
        merged_data['days_to_expire'] = (merged_data['expire_date'] - merged_data['trade_date']).dt.days

        return merged_data

    def save_data(self, etf_data, option_data, etf_file='data/stock_data.csv', option_file='data/option_data.csv'):
        """
        保存数据到CSV文件

        参数:
            etf_data (pandas.DataFrame): ETF数据
            option_data (pandas.DataFrame): 期权数据
            etf_file (str): ETF数据保存路径
            option_file (str): 期权数据保存路径
        """
        etf_data.to_csv(etf_file, index=False)
        if not option_data.empty:
            option_data.to_csv(option_file, index=False)

        print(f"ETF数据已保存至 {etf_file}")
        print(f"期权数据已保存至 {option_file}")

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

if __name__ == '__main__':
    # 测试代码
    # 注意：运行前需要设置TUSHARE_TOKEN环境变量或在初始化时提供token
    try:
        fetcher = DataFetcher()

        # 获取2022年的数据
        start_date = '20220101'
        end_date = '20221231'

        print(f"正在获取{start_date}至{end_date}的数据...")
        print("数据获取完成!")
    except Exception as e:
        print(f"数据获取失败: {e}")
