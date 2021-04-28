# System imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Third-party imports
from pathlib import Path
import yfinance as yf

# Local imports
from portfolio.transactions import Trades
import datehandler


class Portfolio:
    def __init__(self):
        '''View portfolio data and returns
        '''
        # Dates and file paths
        self.today = datetime.today()
        self.save_dir = Path(__file__).parents[1] / 'data'
        self.portfolio_csv_name = f'portfolio_holdings.csv'
        self.portfolio_csv_path = self.save_dir / self.portfolio_csv_name
        
        # Initialise trade transaction data
        self.t = Trades()
        self.trades = self.t.all

        # Create portfolio from trades
        self.holdings = self.build()

    def build(self):
        '''Builds portfolio holdings from transaction data
        
        Returns:
            Dataframe -- (Date, Ticker): [Volume, Close]
        '''        

        # Construct range of dates over portfolio period
        p_inception = self.trades.index[0][0]
        p_dates = datehandler.date_list(p_inception, self.today)

        # Create base dataframe
        df_base_dates = pd.DataFrame(index=p_dates)
        df_base_dates.index.name = 'Date'

        df_pfolio = pd.DataFrame()  # Initialise the main portfolio df as empty

        # Build list of tickers seen throughout investment period
        tickers = list(sorted(set(self.trades.reset_index().Ticker.to_list())))

        # Use yfinance to get close prices
        lookup_tickers = [f'{ticker}.AX' for ticker in tickers]  # Only supports ASX stocks
        lookup_tickers = ' '.join(lookup_tickers)

        prices = yf.download(lookup_tickers, start=p_dates[0], end=p_dates[-1])
        close = prices['Adj Close'] # Using Adj Close instead of Close to account for stocksplits, dividends
        close.columns = tickers

        # Step through transactions dataframe, ticker by ticker
        for ticker in tickers:
            vol_df = self.t.by_ticker(ticker)['Volume']  # Get volumes

            # Merge with base_dates_df and cumulative sum the volumes
            ticker_df = pd.merge_ordered(vol_df, df_base_dates, on='Date').set_index('Date')
            ticker_df = ticker_df.cumsum().ffill()
            ticker_df = ticker_df[ticker_df['Volume'].isna() == False]

            # Update volumes based on stocksplits
            ticker_df = self.stocksplits(ticker_df,ticker)

            # Merge with close prices
            ticker_df = pd.merge_ordered(ticker_df, close[ticker], on='Date').set_index('Date')
            ticker_df.rename({ticker: 'Close'}, axis=1, inplace=True)
            
            # Merge ticker_df with portfolio_df
            ticker_df['Ticker'] = ticker # create ticker column for later indexing
            df_pfolio = pd.concat([df_pfolio, ticker_df])

        df_pfolio = df_pfolio.reset_index().set_index(['Date','Ticker']).sort_index()  # Finalise portfolio
        df_pfolio = df_pfolio.assign(Value = lambda x: x['Volume'] * x['Close'])  # Calculate portfolio value
        print('\nPortfolio successfully built')

        return df_pfolio

    def stocksplits(self, df, ticker):
        '''Adjusts volumes according to historical stocksplits
        
        Arguments:
            df {DataFrame} -- Dataframe with date (index) and volume (series) data
            ticker {String} -- Ticker to explore. Only ASX securities supported
        
        Returns:
            DataFrame -- Returns dataframe, but with volume scaled by the cumulative stocksplits
        '''
        # Terminal output
        print(f'\rChecking {ticker}', end='', flush=True)

        try:  # Dividends and stock splits
            stock = yf.Ticker(f'{ticker}.AX')
            df_actions = stock.actions
        except TypeError:
            print(f'\rSomething went wrong!',flush=True)
            return df
        
        # Add stocksplits column
        if len(df_actions[df_actions['Stock Splits'] > 0]) > 0:
            df['Stock Splits'] = df_actions['Stock Splits'].replace(0,np.nan)

            # Set all dates with 0 holdings to have np.nan holdings
            df['Volume'] = df['Volume'].replace(0,np.nan)

            stocksplit_cumulative = df.loc[df['Volume'].first_valid_index():]['Stock Splits'].cumprod()
            stocksplit_cumulative = stocksplit_cumulative.fillna(method='ffill').fillna(1)


            # Update holding volume
            df['Volume'] *= stocksplit_cumulative
            df['Volume'] = np.ceil(df['Volume'])
            
            # Update vwap
            # df['Vwap'] /= stocksplit_cumulative

            df = df.drop(columns='Stock Splits')  # Finalise dataframe to return by removing excess columns

        return df

    def plot(self, view='default'):
        # Portfolio value
        value_df = self.holdings.groupby('Date').sum()['Value']
        value_df = value_df[value_df > 0]

        # The portfolio cost for equity
        cost_df = self.trades.assign(Value = lambda x: x['Volume'] * x['EffectivePrice'])
        cost_df = cost_df.groupby('Date').sum()['Value'].cumsum()

        plot_df = pd.merge_ordered(value_df, cost_df, on='Date', fill_method='ffill').set_index('Date')
        plot_df.columns = ['Value', 'Cost']
        plot_df = plot_df.assign(pl_line = lambda x: x['Value'] - x['Cost'])
        plot_df = plot_df.assign(pl_pct = lambda x: x['pl_line']/x['Cost'])

        if view == 'default':
            cols = ['Value','Cost']
        elif view == 'pl':
            cols = ['pl_line']
        elif view == 'pl_pct':
            cols = ['pl_pct']
        
        plot_df[cols].plot()

        return plot_df