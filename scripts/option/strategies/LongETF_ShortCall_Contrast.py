import pandas as pd

class LongETFShortCallContrastStrategy:
    """
    Long ETF + Short Call Contrast Ratio 策略
    """

    def __init__(self, etf_data, option_data, initial_stock_capital=1000000,initial_option_capital=200000):
        """
        初始化策略
        :param etf_data: ETF历史数据 (DataFrame)
        :param option_data: 期权历史数据 (DataFrame)
        """
        self.etf = etf_data.set_index('trade_date')
        self.options = option_data.set_index('trade_date')
        self.stock_capital = initial_stock_capital
        self.option_capital = initial_option_capital
        self.sum_capital = initial_stock_capital + initial_option_capital
        self.stock_positions = {}  # 当前持仓
        self.option_positions = {}
        self.stock_trade_log = []
        self.option_trade_log = []
        self.trade_log = []  # 交易记录

        # 预处理期权数据
        self._preprocess_data()

    def _preprocess_data(self):
        # handle etf data
        self.etf['trade_date'] = pd.to_datetime(self.etf['trade_date'])

    

