#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据处理辅助模块：包含期权数据的处理和筛选逻辑
"""

import pandas as pd
import os
import time


class DataProcessor:
    """
    数据处理辅助类：包含期权数据的处理和筛选逻辑
    """
    ETF_TSCODE_MAP = {
        '510500.SH': '500ETF',
        '512100.SH': '1000ETF'
    }

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

    def get_opt_basic(self, exchange, start_date, end_date):
        # 获取后存到文件中
        current_script_path = os.path.abspath(__file__)
        data_dir = os.path.dirname(current_script_path)
        folder_path = os.path.join(data_dir, 'opt_basic', exchange)
        file_name = f'opt_basic_{exchange}_{start_date}_{end_date}.csv'  # 修改文件名格式
        opt_basic_file = os.path.join(folder_path, file_name)

        if not os.path.exists(opt_basic_file):
            ts_data = self.pro.opt_basic(
                exchange=exchange,
                fields='ts_code,name,opt_code,opt_type,call_put,exercise_price,maturity_date,list_date,delist_date'
            )

            ts_data = ts_data[
                (ts_data['list_date'] >= start_date) &
                (ts_data['delist_date'] <= end_date)
                ]
            self.save_csv_data_simple(ts_data, folder_path, file_name)
        else:
            print(f"文件{opt_basic_file}已存在")
            ts_data = pd.read_csv(opt_basic_file)
            # 确保日期字段是字符串类型（与Tushare返回格式一致）
            ts_data['list_date'] = ts_data['list_date'].astype(str)
            ts_data['delist_date'] = ts_data['delist_date'].astype(str)
        return ts_data

    def get_opt_specific(self, opt_basic_data, trade_dates, option_type, exchange, start_date, end_date):
        keyword_option = self.OPTION_MAP.get(option_type)
        opt_specific = opt_basic_data.loc[opt_basic_data['name'].str.contains(keyword_option)]
        current_script_path = os.path.abspath(__file__)
        data_dir = os.path.dirname(current_script_path)
        folder_path = os.path.join(data_dir, 'opt_specific', exchange)
        file_name = f'opt_specific_{keyword_option}_{exchange}_{start_date}_{end_date}.csv'  # 修改文件名格式
        opt_specific_file = os.path.join(folder_path, file_name)
        if not os.path.exists(opt_specific_file):
            # 按照list_date升序排序
            opt_specific = opt_specific.sort_values('ts_code')
            self.save_csv_data_simple(opt_specific, folder_path, file_name)
        else:
            print(f"文件{opt_specific_file}已存在")
            opt_specific = pd.read_csv(opt_specific_file)
            # 确保日期字段是字符串类型（与Tushare返回格式一致）
            opt_specific['list_date'] = opt_specific['list_date'].astype(str)
            opt_specific['delist_date'] = opt_specific['delist_date'].astype(str)
        return opt_specific

    @staticmethod
    def save_csv_data_simple(data, folder_path, file_name):
        """
        保存数据到CSV文件
        参数:
            data (pandas.DataFrame): 要保存的数据
            folder_path (str): 文件夹路径
            file_name (str): 文件名称
        """

        print(f"尝试保存到: {folder_path + file_name}")
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

    def get_opt_merge_data(self, opt_specific_data, trade_dates, option_type, exchange, start_date, end_date):
        """
        获取期权基础信息与日线数据的合并数据
        
        参数:
            opt_specific_data (DataFrame): 期权基础信息数据
            exchange (str): 交易所代码
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD
            
        返回:
            DataFrame: 合并后的数据
        """
        merged_data = pd.DataFrame()
        keyword_option = self.OPTION_MAP.get(option_type)

        current_script_path = os.path.abspath(__file__)
        data_dir = os.path.dirname(current_script_path)
        folder_path = os.path.join(data_dir, 'opt_merged', exchange)
        file_name = f'opt_merged_{keyword_option}_{exchange}_{start_date}_{end_date}.csv'
        opt_merged_file = os.path.join(folder_path, file_name)
        if not os.path.exists(opt_merged_file):
            for opt_specific_item in opt_specific_data.itertuples():
                # tushare 限制每分钟150次接口请求
                time.sleep(0.4)  # 避免请求过快
                
                # 合约的所有交易日数据
                opt_dailys = self.pro.opt_daily(
                    ts_code=opt_specific_item.ts_code,
                    fields='ts_code,trade_date,pre_settle,pre_close,open,high,low,close,settle,vol,amount'
                )
                
                if opt_dailys.empty:
                    print(f"合约 {opt_specific_item.ts_code} 没有交易数据")
                    continue
                    
                # 将期权基础信息添加到每一行日线数据中
                # for col in opt_specific_data.columns:
                #     if col != 'ts_code':  # ts_code已经在opt_dailys中
                #         opt_dailys[col] = opt_specific_item[col]

                # 或者使用 assign 方法一次性添加所有列 (解包)
                opt_dailys = opt_dailys.assign(**{col: getattr(opt_specific_item, col) for col in opt_specific_data.columns if col != 'ts_code'})
                
                # 将 opt_dailys 追加到 merged_data
                merged_data = pd.concat([merged_data, opt_dailys], ignore_index=True)
            merged_data = merged_data.sort_values(by=['ts_code', 'trade_date'])
            # 保存到CSV文件
            self.save_csv_data_simple(merged_data, folder_path, file_name)
        else:
            print(f"文件{opt_merged_file}已存在")
            merged_data = pd.read_csv(opt_merged_file)
            # 确保日期字段是字符串类型（与Tushare返回格式一致）
            merged_data['trade_date'] = merged_data['trade_date'].astype(str)

        # 如果没有数据，返回空DataFrame
        if merged_data.empty:
            print("没有找到任何合并数据")
        
        return merged_data

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

        # return df

        # 获取后存到文件中
        keyword_etf = self.ETF_TSCODE_MAP.get(ts_code)
        current_script_path = os.path.abspath(__file__)
        data_dir = os.path.dirname(current_script_path)
        folder_path = os.path.join(data_dir, 'etc_specific')
        file_name = f'etf_specific_{keyword_etf}_{start_date}_{end_date}.csv'
        etf_specific_file = os.path.join(folder_path, file_name)

        if not os.path.exists(etf_specific_file):
            ts_data = self.pro.fund_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,open,high,low,close,vol,amount'
            )

            ts_data = ts_data.sort_values('trade_date')
            self.save_csv_data_simple(ts_data, folder_path, file_name)
        else:
            print(f"文件{etf_specific_file}已存在")
            ts_data = pd.read_csv(etf_specific_file)
            # 确保日期字段是字符串类型（与Tushare返回格式一致）
            ts_data['trade_date'] = ts_data['trade_date'].astype(str)
        ts_data['trade_date'] = pd.to_datetime(ts_data['trade_date'])
        return ts_data
