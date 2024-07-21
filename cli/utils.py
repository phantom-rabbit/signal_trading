import os.path

from loguru import logger
import pandas as pd



def result_handler(result, strategy_name):
    data = []
    for run in result:
        for strategy in run:
            item = {}
            params = strategy.params._getkwargs()
            item["params"] = params
            periodstats = strategy.analyzers.getbyname("PeriodStats")
            # if periodstats not None:
            periodstats_analysis = periodstats.get_analysis()
            item["average"] = periodstats_analysis['average'],
            item["stddev"] = periodstats_analysis['stddev'],
            item["positive"] = periodstats_analysis['positive'],
            item["negative"] = periodstats_analysis['negative'],
            item["nochange"] = periodstats_analysis['nochange'],
            item["best"] = periodstats_analysis['best'],
            item["worst"] = periodstats_analysis['worst'],

            returns = strategy.analyzers.getbyname("Returns")
            returns_analysis = returns.get_analysis()
            item["rtot"] = returns_analysis['rtot'],
            item["ravg"] = returns_analysis['ravg'],
            item["rnorm"] = returns_analysis['rnorm'],
            item["rnorm100"] = returns_analysis['rnorm100'],


            drawdown = strategy.analyzers.getbyname("DrawDown")
            drawdown_analysis = drawdown.get_analysis()
            item["drawdown"] = drawdown_analysis["drawdown"],
            item["moneydown"] = drawdown_analysis["moneydown"],
            item["len"] = drawdown_analysis["len"],
            item["max_drawdown"] = drawdown_analysis['max']["drawdown"],
            item["max_moneydown"] = drawdown_analysis['max']["moneydown"],
            item["max_len"] = drawdown_analysis['max']["len"],


            position = strategy.analyzers.getbyname("Position")
            position_analysis = position.get_analysis()
            item['cash']= position_analysis['cash']
            item['value']= position_analysis['value']
            item['fundvalue']= position_analysis['fundvalue']
            data.append(item)

    df = pd.DataFrame(data)
    df.sort_values(by="fundvalue", ascending=False)
    strategy_name = str.replace(strategy_name, " ", "_")
    save_path = f"{strategy_name}.xlsx"
    df.to_excel(save_path, index=False)
    logger.info(f"save analyzer {save_path}")