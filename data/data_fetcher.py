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

    def prepare_backtest_data_origin(self, start_date, end_date, etf_type='500', exchange='SSE'):


        ts_code_etf = self.ETF_MAP.get(etf_type, '510500.SH')
        _etf_data = self.processor.get_etf_price(ts_code_etf, start_date, end_date)
        # 通过etf数据 获取实际交易日
        trade_dates= _etf_data['trade_date'].dt.strftime('%Y%m%d').tolist()

        # 获取基础期权数据
        opt_basic_data = self.processor.get_opt_basic(exchange=exchange, start_date=start_date, end_date=end_date)

        # 基础数据中筛选出指定的期权
        opt_specific_data = self.processor.get_opt_specific(opt_basic_data, trade_dates, option_type=etf_type, exchange=exchange, start_date=start_date, end_date=end_date)
        # return opt_specific_data

        # 期权日数据获取
        opt_merge_data = self.processor.get_opt_merge_data(opt_specific_data, trade_dates, option_type=etf_type, exchange=exchange, start_date=start_date, end_date=end_date)

        return _etf_data, opt_merge_data

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
