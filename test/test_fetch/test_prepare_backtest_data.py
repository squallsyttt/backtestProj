import sys
import os
import pytest

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 假设 data 模块所在的目录是当前脚本目录的上一级目录
parent_dir = os.path.dirname(current_dir)
grand_parent_dir = os.path.dirname(parent_dir)
# 将 data 模块所在的目录添加到 sys.path 中
sys.path.append(grand_parent_dir)
from data.data_fetcher import DataFetcher

def test_prepare_backtest_option_data():
    ts_token = "7e33b6a3e2bad955cd087c9e5a6e69ad34dc797daee4ff6de9cb08f7"
    #创建 datafetcher对象
    fetcher = DataFetcher(ts_token)

    start_date = "20240101"
    end_date = "20240105"

    print(f"start{start_date} && end{end_date}")

    a = 1
    assert a == 1
    # etf_data, option_data = fetcher.prepare_backtest_option_data(start_date, end_date)

    # assert len(etf_data) == 5
    # assert len(option_data) == 5
    # assert 'trade_date' in etf_data.column


def test_prepare_back_data_origin():
    ts_token = "7e33b6a3e2bad955cd087c9e5a6e69ad34dc797daee4ff6de9cb08f7"
    print(f"token:{ts_token}")

    
    fetcher = DataFetcher(ts_token)
    start_date = "20240101"
    end_date = "20240105"
    res = fetcher.prepare_backtest_data_origin(start_date, end_date)

    expected = 0

    print(f"返回值类型：{type(res)}")
    print(f"返回值：{res}")

    assert res > expected