import os.path
import sys

import click
from loguru import logger
import pandas as pd



def result_handler(results, strategy_name, opt):
    # 准备存储结果的列表
    results_list = []

    # 打印优化结果并存储在列表中
    for result in results:
        for strategy in result:
            # 获取策略参数
            params = {k: v for k, v in strategy.params.__dict__.items() if not k.startswith('_')}

            # 获取最终投资组合值
            final_value = strategy.broker.getvalue()
            commission = strategy.commission
            # 存储结果
            results_list.append({
                **params,
                'final_value': final_value,
                "commission": commission
            })
    for row in results_list:
        print(f"{row}")
    results_df = pd.DataFrame(results_list)
    if opt:
        strategy_name = str.replace(strategy_name, " ", "_")
        save_path = f"{strategy_name}.xlsx"
        results_df.to_excel(save_path, index=False)
        logger.info(f"save to {save_path}")

class CommaSeparatedList(click.ParamType):
    name = "comma_separated_list"

    def convert(self, value, param, ctx):
        try:
            return [float(x) for x in value.split(",")]
        except ValueError:
            self.fail(f"{value} is not a valid comma-separated list", param, ctx)

class CommaSeparatedListInt(click.ParamType):
    name = "comma_separated_list"

    def convert(self, value, param, ctx):
        try:
            return [int(x) for x in value.split(",")]
        except ValueError:
            self.fail(f"{value} is not a valid comma-separated list", param, ctx)



COMMA_SEPARATED_LIST = CommaSeparatedList()
COMMA_SEPARATED_LIST_INT = CommaSeparatedListInt()

