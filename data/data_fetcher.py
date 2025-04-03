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
from .dataHelper.data_processor import DataProcessor

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
        self.processor = DataProcessor(self.pro)

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
        _etf_data = self.processor.get_etf_price(ts_code, start_date, end_date)

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
        _etf_data = self.processor.get_etf_price(ts_code_etf, start_date, end_date)
        # 通过etf数据 获取实际交易日
        trade_dates= _etf_data['trade_date'].dt.strftime('%Y%m%d').tolist()

        # 获取基础期权数据
        opt_basic_data = self.processor.get_opt_basic(exchange=exchange, start_date=start_date, end_date=end_date)

        # 基础数据中筛选出指定的期权
        opt_specific_data = self.processor.get_opt_specific(opt_basic_data, trade_dates, option_type=etf_type, exchange=exchange)
        return opt_specific_data

        # 期权日数据获取
        opt_merge_data = self.processor.get_opt_merge_data(opt_specific_data, trade_dates, option_type=etf_type, exchange=exchange)

        return opt_merge_data



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
