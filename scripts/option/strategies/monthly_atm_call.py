import pandas as pd
from datetime import timedelta


class MonthlyATMCallStrategy:
    """
    每月卖出平值看涨策略原生实现
    """

    def __init__(self, etf_data, option_data, initial_capital=1000000):
        """
        初始化策略
        :param etf_data: ETF历史数据 (DataFrame)
        :param option_data: 期权历史数据 (DataFrame)
        :param initial_capital: 初始资金
        """
        self.etf = etf_data.set_index('trade_date')
        self.options = option_data
        self.capital = initial_capital
        self.positions = {}  # 当前持仓
        self.trade_log = []  # 交易记录

        # 预处理期权数据
        self._preprocess_data()

    def _preprocess_data(self):
        """数据预处理"""
        # 转换日期格式
        self.options['trade_date'] = pd.to_datetime(self.options['trade_date'])
        self.options['expire_date'] = pd.to_datetime(self.options['expire_date'])

        # 筛选看涨期权
        self.options = self.options[self.options['call_put'] == 'C']

        # 创建多层索引 (交易日期, 期权代码)
        self.options.set_index(['trade_date', 'ts_code'], inplace=True)

    def _get_month_start_trade_dates(self):
        """获取每月首个交易日"""
        return self.etf.resample('MS').first().index

    def _find_atm_option(self, trade_date):
        """
        寻找平值期权
        :return: (ts_code, option_data)
        """
        # 获取当日ETF价格
        etf_price = self.etf.loc[trade_date, 'close']

        # 筛选当月到期期权
        valid_options = self.options.loc[trade_date]
        valid_options = valid_options[
            (valid_options['exercise_price'] >= etf_price * 0.98) &
            (valid_options['exercise_price'] <= etf_price * 1.02)
            ]

        if not valid_options.empty:
            # 取行权价最接近的
            return valid_options.nsmallest(1, 'price_diff').iloc[0]
        return None

    def run_backtest(self):
        """运行回测"""
        # 获取所有调仓日期
        rebalance_dates = self._get_month_start_trade_dates()

        for date in self.etf.index:
            # 检查是否需要展期
            self._check_expiration(date)

            # 每月首个交易日开仓
            if date in rebalance_dates:
                self._open_position(date)

            # 更新每日净值
            self._update_value(date)

    def _open_position(self, trade_date):
        """开仓操作"""
        # 寻找平值期权
        option = self._find_atm_option(trade_date)

        if option and self.capital > 0:
            # 计算保证金 (假设保证金为期权价值的15%)
            margin = option['close'] * 10000 * 0.15  # 假设合约乘数10000

            if margin < self.capital:
                # 记录交易
                self.positions[option.name] = {
                    'entry_date': trade_date,
                    'entry_price': option['close'],
                    'margin': margin,
                    'expire_date': option['expire_date']
                }

                # 更新资金
                self.capital -= margin
                self.trade_log.append({
                    'date': trade_date,
                    'type': 'sell',
                    'price': option['close'],
                    'contract': option.name,
                    'margin': margin
                })

    def _check_expiration(self, current_date):
        """检查持仓到期"""
        to_close = []
        for contract, pos in self.positions.items():
            # 到期前7天平仓
            if (pos['expire_date'] - current_date).days <= 7:
                to_close.append(contract)

        for contract in to_close:
            # 释放保证金
            self.capital += pos['margin']

            # 记录平仓
            self.trade_log.append({
                'date': current_date,
                'type': 'close',
                'price': self.options.loc[(current_date, contract), 'close'],
                'contract': contract,
                'margin': pos['margin']
            })

            del self.positions[contract]

    def _update_value(self, date):
        """更新每日净值"""
        # 实现市值计算逻辑
        pass

    def get_results(self):
        """获取回测结果"""
        # 实现绩效分析逻辑
        return {
            'nav': self._calculate_net_value(),
            'metrics': self._calculate_metrics()
        }