import streamlit as st
import pandas as pd
import time
from strategy_main import date_convert, get_weekday, long_strategy, get_performance

st.set_page_config(layout="wide")

if 'but_click_1' not in st.session_state:
    st.session_state.but_click_1 = False

if 'but_click_2' not in st.session_state:
    st.session_state.but_click_2 = False

def data_read():
    df = pd.read_csv("nifty_historical.csv")
    df.drop(columns=['Index Name'], inplace=True)

    df['date'] = df['Date'].apply(date_convert)
    df.drop(columns='Date', inplace=True)

    df['weekday'] = df['date'].apply(get_weekday)

    df.sort_values(by='date', ascending=True, inplace=True)
    df.drop(columns=['Open', 'High', 'Low'], inplace=True)

    return df

def click_backtest_1():
    st.session_state.but_click_1 = True

def click_backtest_2():
    st.session_state.but_click_2 = True

@st.cache_data
def display_df(df):
    st.dataframe(df.T, use_container_width=True, height=510)

@st.cache_data
def convert_df(data):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return data.to_csv().encode("utf-8")

@st.experimental_fragment
def show_download_button(result, filename, key_name):
    st.download_button(
        label="Download trade log",
        data=result,
        file_name=filename,
        mime="text/csv",
        type='primary',
        key=key_name
    )



def main():
    df = data_read()

    st.title('NIFTY Weekend Backtesting :dollar: :chart:' )

    strategy = '''
        This app allows you to backtest an ***over the weekend*** strategy for the end user. The rules for the strategy are as follows

        1. Download the NIFTY50 hisstorical data from this [link](https://www.niftyindices.com/reports/historical-data) for a timeframe on which you want to test the strategy upon
        2. For every Fridat, check the following two conditions
            1. The closing value of the Friday should be **greater** than the ***200 DMA*** before that respective Friday
            2. The closing value of the Friday should be **greater** than the ***closing value of the previous trading day by 0.15%***
        3. If the above two conditions are met, go long on the NIFTY value and hold it till the close of the next trading day after that Friday
        
        ***Note:*** 1. 200 DMA should be calculated using the data upto the previous day before Friday
    '''
    st.markdown(strategy)

    st.subheader('Strategy backtesting simulator :hammer_and_wrench:', divider='rainbow')
    st.markdown("You can backtest the strategy on the data starting from Apr 30, 2014 up to May 7, 2024 in a ***side-by-side*** comparative view")

    col1, col2 = st.columns(2, gap="large")

    with col1:

        st.subheader("Combination 1")
        dma_period = st.select_slider(
            "DMA lookback period",
            options=[252, 200, 100, 50, 20],
            key="com1"
        )
        
        pc_change = st.number_input("% change", min_value=0, max_value=100, key="com_numb_1")
        
        run_1 = st.button("Run backtest", key='b1', on_click=click_backtest_1)
        if run_1 or st.session_state.but_click_1:

            if st.session_state.but_click_2 == True:
                click_backtest_2()

            result = long_strategy(df, dma_period, pc_change)
            metrics = get_performance(result)
            
            # logic to display and add the functionality to the download button
            display_df(metrics)
            result_df = convert_df(result)
            filename = "trade_log_" + str(dma_period) + "_" + str(pc_change) + ".csv"
            show_download_button(result_df, filename, "dl_1")
            

            # st.write(st.session_state)
        
            # with st.spinner("Waiting for 3 seconds"):
            #     time.sleep(3)
    

    with col2:

        st.subheader("Combination 2")
        dma_period = st.select_slider(
            "DMA lookback period",
            options=[252, 200, 100, 50, 20],
            key="com2"
        )
        
        pc_change = st.number_input("% change", min_value=0, max_value=100, key="com_numb_2")
        
        run_2 = st.button("Run backtest", key='b2', on_click=click_backtest_2)
        if run_2 or st.session_state.but_click_2:

            if st.session_state.but_click_1 == True:
                click_backtest_1()
            
            result = long_strategy(df, dma_period, pc_change)
            metrics = get_performance(result)
            display_df(metrics)
            
            result_df = convert_df(result)
            filename = "trade_log_" + str(dma_period) + "_" + str(pc_change) + ".csv"

            show_download_button(result_df, filename, "dl_2")

            
main()

