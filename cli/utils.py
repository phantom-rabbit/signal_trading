import os.path
import sys

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
            # 存储结果
            results_list.append({
                **params,
                'final_value': final_value,
            })
    for row in results_list:
        print(f"{row}")
    results_df = pd.DataFrame(results_list)
    if opt:
        strategy_name = str.replace(strategy_name, " ", "_")
        save_path = f"{strategy_name}.xlsx"
        results_df.to_excel(save_path, index=False)
        logger.info(f"save to {save_path}")
