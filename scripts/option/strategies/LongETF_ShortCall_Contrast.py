import pandas as pd

class LongETFShortCallContrastStrategy:
    """
    Long ETF + Short Call Contrast Ratio 策略
    """

    def __init__(self, etf_data, option_data, initial_stock_capital=1000000, initial_option_capital=200000):
        """
        初始化策略
        :param etf_data: ETF历史数据 (DataFrame)
        :param option_data: 期权历史数据 (DataFrame)
        """
        self.etf = etf_data.set_index('trade_date',drop=False)
        self.options = option_data.set_index('trade_date',drop=False)
        self.stock_capital = initial_stock_capital
        self.stock_shares = 0
        self.option_capital = initial_option_capital
        self.option_shares = 0
        self.sum_capital = initial_stock_capital + initial_option_capital
        # 合并持仓信息
        self.positions = {'stock': {}, 'option': {}}  # {'stock': {...}, 'option': {...}}
        # 合并交易日志
        self.trade_log = []  # [{'type': 'stock'/'option', ...}, ...]
        # 预处理期权数据
        self._preprocess_data()

    def _preprocess_data(self):
        # handle etf data
        self.etf['trade_date'] = pd.to_datetime(self.etf['trade_date'])

    def buy_etf(self, buy_date, principal=None):
        """
        以指定本金在 buy_date 买入ETF，记录买入价格、份额和剩余现金
        :param buy_date: 买入日期 (str 或 datetime)
        :param principal: 买入本金，默认使用初始化时的 initial_stock_capital
        """
        if principal is None:
            principal = self.stock_capital
        if isinstance(buy_date, str):
            buy_date = pd.to_datetime(buy_date)
        row = self.etf.loc[self.etf['trade_date'] == buy_date]
        if row.empty:
            raise ValueError(f"买入日期 {buy_date} 不在ETF数据中")
        buy_price = row.iloc[0]['close']
        shares = principal // buy_price  # 整除，买入整数份额
        invested = shares * buy_price
        cash_left = principal - invested
        self.etf_buy_date = buy_date
        self.etf_buy_price = buy_price
        self.etf_shares = shares
        self.etf_principal = principal
        self.etf_invested = invested
        self.etf_cash = cash_left  # 新增：记录剩余现金
        return {
            'buy_date': buy_date,
            'buy_price': buy_price,
            'shares': shares,
            'invested': invested,
            'cash_left': cash_left
        }

    def get_etf_value(self, query_date):
        """
        查询指定日期ETF市值和收益
        :param query_date: 查询日期 (str 或 datetime)
        :return: dict，包括 market_value, profit, profit_rate
        """
        if not hasattr(self, 'etf_shares'):
            raise Exception("请先调用 buy_etf 方法进行买入")
        if isinstance(query_date, str):
            query_date = pd.to_datetime(query_date)
        row = self.etf.loc[self.etf['trade_date'] == query_date]
        if row.empty:
            raise ValueError(f"查询日期 {query_date} 不在ETF数据中")
        price = row.iloc[0]['close']
        value = self.etf_shares * price
        profit = value - self.etf_invested
        profit_rate = profit / self.etf_invested
        return {'market_value': value, 'profit': profit, 'profit_rate': profit_rate}

    def run_backtest(self, buy_date=None):
        """
        只回测ETF部分，不开期权仓位。
        :param buy_date: 可选，买入日期（str 或 datetime），不传则为第一个交易日
        """
        results = []
        if buy_date is None:
            buy_date = self.etf.index[0]
        self.buy_etf(buy_date)
        for date in self.etf.index:
            if date < buy_date:
                continue  # 买入前不计入回测
            daily = self.get_etf_value(date)
            results.append({
                'date': date,
                'market_value': daily['market_value'],
                'profit': daily['profit'],
                'profit_rate': daily['profit_rate'],
                'cash': self.etf_cash
            })
        self.backtest_results = results
        return results