#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测引擎：用于运行中证500ETF期权策略回测
"""

import backtrader as bt
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
from strategies.monthly_atm_call import MonthlySellATMCall


class BacktestEngine:
    """
    回测引擎类：负责加载数据、运行策略回测并输出结果
    """
    
    def __init__(self, cash=100000.0, commission=0.0003):
        """
        初始化回测引擎
        
        参数:
            cash (float): 初始资金
            commission (float): 佣金率
        """
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(cash)
        self.cerebro.broker.setcommission(commission=commission)
        self.data_loaded = False
        
    def load_data(self, etf_data_file, option_data_file):
        """
        加载回测数据
        
        参数:
            etf_data_file (str): ETF数据文件路径
            option_data_file (str): 期权数据文件路径
        
        返回:
            bool: 数据加载是否成功
        """
        try:
            # 加载ETF数据
            etf_df = pd.read_csv(etf_data_file)
            etf_df['trade_date'] = pd.to_datetime(etf_df['trade_date'])
            
            # 创建ETF数据源
            etf_data = bt.feeds.PandasData(
                dataname=etf_df,
                datetime='trade_date',
                open='open',
                high='high',
                low='low',
                close='close',
                volume='vol',
                openinterest=-1,
                name='510500.SH'
            )
            
            # 添加ETF数据到回测引擎
            self.cerebro.adddata(etf_data)
            
            # 加载期权数据
            option_df = pd.read_csv(option_data_file)
            option_df['trade_date'] = pd.to_datetime(option_df['trade_date'])
            option_df['expire_date'] = pd.to_datetime(option_df['expire_date'])
            
            # 按期权代码分组，为每个期权创建数据源
            for ts_code, group in option_df.groupby('ts_code'):
                group = group.sort_values('trade_date')
                
                # 创建期权数据源
                option_data = bt.feeds.PandasData(
                    dataname=group,
                    datetime='trade_date',
                    open='open',
                    high='high',
                    low='low',
                    close='close',
                    volume='vol',
                    openinterest=-1,
                    name=ts_code
                )
                
                # 添加期权属性
                option_data.strike = group['exercise_price'].iloc[0]
                option_data.opttype = 'call' if group['call_put'].iloc[0] == 'C' else 'put'
                option_data.expiry = group['expire_date'].iloc[0].to_pydatetime()
                
                # 添加期权数据到回测引擎
                self.cerebro.adddata(option_data)
            
            self.data_loaded = True
            return True
            
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False
    
    def add_strategy(self, strategy_class=MonthlySellATMCall, **kwargs):
        """
        添加策略到回测引擎
        
        参数:
            strategy_class: 策略类
            **kwargs: 策略参数
        """
        self.cerebro.addstrategy(strategy_class, **kwargs)
    
    def run(self):
        """
        运行回测
        
        返回:
            dict: 回测结果
        """
        if not self.data_loaded:
            print("请先加载数据")
            return None
        
        # 记录初始资金
        initial_cash = self.cerebro.broker.getvalue()
        
        # 运行回测
        results = self.cerebro.run()
        strategy = results[0]
        
        # 计算最终资金
        final_cash = self.cerebro.broker.getvalue()
        
        # 计算收益率
        returns = (final_cash - initial_cash) / initial_cash * 100
        
        # 收集回测结果
        backtest_results = {
            'initial_cash': initial_cash,
            'final_cash': final_cash,
            'returns': returns,
            'trades': strategy.trades if hasattr(strategy, 'trades') else [],
            'monthly_returns': strategy.monthly_returns if hasattr(strategy, 'monthly_returns') else {}
        }
        
        return backtest_results
    
    def plot(self, filename=None):
        """
        绘制回测结果图表
        
        参数:
            filename (str): 保存图表的文件路径，如果为None则显示图表
        """
        plt.figure(figsize=(12, 8))
        self.cerebro.plot(style='candlestick')
        
        if filename:
            plt.savefig(filename)
        else:
            plt.show()


def run_backtest(etf_data_file='data/stock_data.csv', option_data_file='data/option_data.csv', cash=100000.0, commission=0.0003, days_before_expiry=7, printlog=True):
    """
    运行中证500ETF期权策略回测的便捷函数
    
    参数:
        etf_data_file (str): ETF数据文件路径
        option_data_file (str): 期权数据文件路径
        cash (float): 初始资金
        commission (float): 佣金率
        days_before_expiry (int): 到期前多少天展期
        printlog (bool): 是否打印日志
        
    返回:
        dict: 回测结果
    """
    # 创建回测引擎
    engine = BacktestEngine(cash=cash, commission=commission)
    
    # 加载数据
    if not engine.load_data(etf_data_file, option_data_file):
        return None
    
    # 添加策略
    engine.add_strategy(MonthlySellATMCall, days_before_expiry=days_before_expiry, printlog=printlog)
    
    # 运行回测
    results = engine.run()
    
    # 绘制结果
    engine.plot()
    
    return results


if __name__ == '__main__':
    # 测试代码
    print("运行中证500ETF期权策略回测...")
    
    results = run_backtest()
    
    if results:
        print(f"初始资金: {results['initial_cash']:.2f}")
        print(f"最终资金: {results['final_cash']:.2f}")
        print(f"总收益率: {results['returns']:.2f}%")
        print(f"总交易次数: {len(results['trades'])}")