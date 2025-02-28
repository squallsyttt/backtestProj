#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
中证500ETF期权策略：每月初卖出平值看涨期权，到期前7天展期
"""

import backtrader as bt
import datetime
import pandas as pd
import numpy as np


class MonthlySellATMCall(bt.Strategy):
    """
    每月初卖出中证500ETF平值看涨期权，到期前7天展期的策略
    """
    
    params = (
        ('printlog', False),  # 是否打印日志
        ('days_before_expiry', 7),  # 到期前多少天展期
    )
    
    def __init__(self):
        # 保存当前持有的期权合约
        self.current_option = None
        # 当前合约的到期日
        self.current_expiry = None
        # 当前月份，用于判断是否需要开始新的交易
        self.current_month = None
        # 记录交易
        self.trades = []
        # 记录每月的收益
        self.monthly_returns = {}
        
    def next(self):
        # 获取当前日期
        current_date = self.datas[0].datetime.date(0)
        current_month = current_date.month
        
        # 如果是新的一个月且没有持仓，则卖出平值看涨期权
        if self.current_month != current_month and not self.current_option:
            self.current_month = current_month
            self.sell_atm_call(current_date)
        
        # 如果有持仓，检查是否需要展期（到期前7天）
        if self.current_option and self.current_expiry:
            days_to_expiry = (self.current_expiry - current_date).days
            if days_to_expiry <= self.p.days_before_expiry:
                self.roll_option(current_date)
    
    def sell_atm_call(self, date):
        """
        卖出平值看涨期权
        """
        # 获取当前中证500ETF价格
        etf_price = self.get_etf_price(date)
        
        # 获取最接近平值的看涨期权合约
        option_contract = self.get_atm_call_option(etf_price, date)
        
        if option_contract:
            # 卖出期权
            self.sell(data=option_contract, size=1)
            self.current_option = option_contract
            self.current_expiry = self.get_option_expiry(option_contract)
            
            self.log(f'卖出平值看涨期权: {option_contract._name}, 行权价: {option_contract.strike}, 到期日: {self.current_expiry}')
    
    def roll_option(self, date):
        """
        展期期权合约
        """
        if self.current_option:
            # 买回当前期权合约
            self.buy(data=self.current_option, size=1)
            self.log(f'买回期权: {self.current_option._name}, 距离到期: {(self.current_expiry - date).days}天')
            
            # 记录交易结果
            trade_result = {
                'entry_date': self.current_option.entry_date,
                'exit_date': date,
                'days_held': (date - self.current_option.entry_date).days,
                'profit_loss': self.current_option.pnl,
            }
            self.trades.append(trade_result)
            
            # 重置当前持仓
            self.current_option = None
            self.current_expiry = None
            
            # 卖出新的平值看涨期权
            self.sell_atm_call(date)
    
    def get_etf_price(self, date):
        """
        获取中证500ETF当前价格
        """
        # 这里应该从数据源获取ETF价格
        # 在实际实现中，可以从self.datas中获取
        for data in self.datas:
            if data._name == '510500.SH':  # 中证500ETF的代码
                return data.close[0]
        
        # 如果没有找到，可以使用其他方式获取
        return None
    
    def get_atm_call_option(self, etf_price, date):
        """
        获取最接近平值的看涨期权合约
        """
        # 在实际实现中，需要从数据源中筛选出合适的期权合约
        # 这里简化处理，假设self.datas中包含了所有期权合约
        
        closest_option = None
        min_diff = float('inf')
        
        for data in self.datas:
            # 跳过非期权数据
            if not hasattr(data, 'strike') or not hasattr(data, 'opttype'):
                continue
            
            # 只考虑看涨期权
            if data.opttype != 'call':
                continue
            
            # 计算行权价与当前价格的差距
            diff = abs(data.strike - etf_price)
            
            # 找到最接近平值的期权
            if diff < min_diff:
                # 检查期权到期日是否在下个月
                expiry = self.get_option_expiry(data)
                if expiry and expiry.month != date.month:
                    closest_option = data
                    min_diff = diff
        
        return closest_option
    
    def get_option_expiry(self, option_data):
        """
        获取期权到期日
        """
        # 在实际实现中，应该从期权合约信息中获取到期日
        # 这里简化处理，假设期权数据中包含expiry属性
        if hasattr(option_data, 'expiry'):
            return option_data.expiry
        
        # 如果没有expiry属性，可以通过其他方式获取
        # 例如从合约名称中解析
        return None
    
    def stop(self):
        """
        策略结束时的处理
        """
        # 计算策略总收益
        total_pnl = sum(trade['profit_loss'] for trade in self.trades)
        
        self.log(f'策略结束，总收益: {total_pnl:.2f}')
        self.log(f'总交易次数: {len(self.trades)}')
        
        if self.trades:
            avg_days_held = sum(trade['days_held'] for trade in self.trades) / len(self.trades)
            self.log(f'平均持仓天数: {avg_days_held:.2f}')
    
    def log(self, txt, dt=None):
        """
        日志函数
        """
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')


if __name__ == '__main__':
    # 测试代码
    print("中证500ETF期权策略：每月初卖出平值看涨期权，到期前7天展期")