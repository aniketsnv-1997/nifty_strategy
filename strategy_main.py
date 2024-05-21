import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st


def date_convert(date):
    format = '%d %b %Y'    

    return datetime.strptime(date, format)

def get_weekday(date):
    
    weekDaysMapping = (
        "Monday",
        "Tuesday", 
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    )
    
    return date.date().weekday()
# , weekDaysMapping[date.date().weekday()]

@st.cache_data
def long_strategy(df, dma_period, pc):

    df['dma'] = df['Close'].rolling(dma_period).mean()

    df.drop(index=df.index[:dma_period], inplace=True)
    # df.drop(index=df[df['weekday'].isin([5, 6])].index, inplace=True)

    print("DMA calculation Succesful")

    fri_indx = df[df['weekday'].isin([4])].index.tolist()
    thur_indx = [f+1 for f in fri_indx]
    fri_indx.sort(reverse=True), thur_indx.sort(reverse=True)


    thu = df[df.index.isin(thur_indx)]
    fri = df[df.index.isin(fri_indx)]

    print("Thursday and Friday df calculaion succesful")

    thu['rank'] = thu['date'].rank(ascending=True, method='first')
    fri['rank'] = fri['date'].rank(ascending=True, method='first')

    thu.rename(columns={'Close':'thu_close', 'date':'thu_date', 'dma':'thu_dma'}, inplace=True)
    fri.rename(columns={'Close':'fri_close', 'date':'fri_date', 'dma':'fri_dma'}, inplace=True)

    total = pd.merge(thu, fri[['rank', 'fri_close', 'fri_date', 'fri_dma']], on='rank', how='left')
    # total.isna().sum()

    print("Thursday and Friday merging succesful")

    total['dma_flag'] = 0
    # total.at[total[total['fri_close'] > total['thu_dma']].index, 'dma_flag'] = 1

    total.loc[total[total['fri_close'] > total['thu_dma']].index, 'dma_flag'] = 1
    # total.dma_flag.value_counts()

    total['thu_flag'] = 0
    total.loc[total[total['fri_close'] > (total['thu_close'] + total['thu_close'] * (pc * 0.01))].index, 'thu_flag'] = 1
    # total.thu_flag.value_counts()

    total['trade_flag'] = 0
    total.loc[total[(total['dma_flag'] == 1) & (total['thu_flag'] == 1)].index, 'trade_flag'] = 1
    # total.trade_flag.value_counts()

    total['%_change'] = round((total['fri_close'] - total['thu_close']) * 100 / total['thu_close'], 2)
    trade_list_index = df[df['date'].isin(total[total['trade_flag'] == 1]['fri_date'].to_list())].index.tolist()

    print("Trade identification succesful")

    mon_indx = [f-1 for f in trade_list_index]

    mon = df[df.index.isin(mon_indx)]

    mon.rename(columns={'Close':'mon_close', 'date':'mon_date'}, inplace=True)
    mon.drop(columns=['weekday', 'dma'], inplace=True)
    mon.drop(index=[1], inplace=True)
    mon['rank'] = mon['mon_date'].rank(ascending=True, method='first')

    print("Monday dataframe collection succesful")

    trade_data = total[total['trade_flag'] == 1]

    # trade_data.drop(columns=['weekday', 'thu_dma', 'rank', 'fri_dma', 'dma_flag', 'thu_flag', '%_change'], inplace=True)
    trade_data['rank'] = trade_data['fri_date'].rank(ascending=True, method='first')

    final = pd.merge(mon, trade_data[['thu_close', 'thu_date', 'fri_close', 'fri_date', 'trade_flag', 'rank']], on='rank', how='left')
    final['abs_returns'] = round(final['mon_close'] - final['fri_close'], 2)
    final['%_returns'] = round((final['mon_close'] - final['fri_close']) * 100 / final['fri_close'], 2)
    final['gains_flag'] = 0

    final['gains_flag'] = np.where(final['%_returns'] > 0, 1, 0)
    # final['gains_flag'].value_counts()

    print("Streak calculation succesful")

    final['shifted'] = final['gains_flag'].shift(fill_value=1)
    final['streak_flag'] = 22
    final['streak_flag'] = np.where(final['gains_flag'] == final['shifted'], 0, 1)
    final['streak_id'] = final['streak_flag'].cumsum()
    final['streak_count'] = final.groupby(['streak_id']).cumcount() + 1

    return final

def get_performance(final):
    met_dict = {
        '#_total_trades': final.shape[0],
        '#_total_winning_trades': final[final['gains_flag'] == 1].shape[0],
        '%_win_rate': round((final[final['gains_flag'] == 1].shape[0] * 100) / final.shape[0], 2),
        '%_loss_rate': round((final[final['gains_flag'] == 0].shape[0] * 100) / final.shape[0], 2),
        'avg_points': round(final['abs_returns'].mean(), 2),
        'median_points': round(final['abs_returns'].median(), 2),
        'total_win_points': round(final[final['gains_flag'] == 1]['abs_returns'].sum(), 2),
        'total_loss_points': round((final[final['gains_flag'] == 0]['abs_returns'].sum()) * -1, 2),
        'max_win_points': final[final['gains_flag'] == 1]['abs_returns'].max(),
        'profit_factor': round(final[final['gains_flag'] == 1]['abs_returns'].sum() / ((final[final['gains_flag'] == 0]['abs_returns'].sum()) * -1), 2),
        'oapf': round((final[final['gains_flag'] == 1]['abs_returns'].sum() - final[final['gains_flag'] == 1]['abs_returns'].max())/ ((final[final['gains_flag'] == 0]['abs_returns'].sum()) * -1), 2),
        'winning_streak': final[final['gains_flag'] == 1]['streak_count'].max(),
        'losing_streak': final[final['gains_flag'] == 0]['streak_count'].max()        
    }

    met_df = pd.DataFrame(met_dict, index=[0])
    return met_df



