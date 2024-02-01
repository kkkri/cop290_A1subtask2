import sys
from datetime import date
from datetime import datetime, timedelta
import time
import pandas as pd
from jugaad_data.nse import bhavcopy_save, bhavcopy_fo_save
import pyarrow.parquet as pq
import os
import matplotlib.pyplot as plt
import pyarrow as pa

def download_stock_data(symbol, years):
    current_date = datetime.now().date()
    date_n_years_ago = current_date - timedelta(days=years * 365)
    
    
    from jugaad_data.nse import stock_df
    df = stock_df(symbol, from_date=date_n_years_ago,
            to_date=current_date, series="EQ")
    
    selected_columns = ['DATE', 'OPEN', 'CLOSE', 'HIGH',
                         'LOW', 'LTP', 'VOLUME', 'VALUE', 'NO OF TRADES']

    df = df[selected_columns]
    return df

def write_to_csv(data, filename):
    return data.to_csv(filename, index=False)

def main(symbol, years):

    stock_data = download_stock_data(symbol, years)
    write_to_csv(stock_data, f"{symbol}.csv")

if __name__ == "__main__":
    symbol = sys.argv[1]
    years = int(sys.argv[2])  
    main(symbol, years)
