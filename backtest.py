import os
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams

rcParams['axes.unicode_minus'] = False

class Backtest:
    def __init__(self, strategy):
        self.strategy = strategy
        self.daily_actions = []
        self.initial_cash = strategy.cash

    def run_backtest(self, df):
        """
        Executes the backtest: applies the strategy on the historical data provided and records daily actions.
        :param df: A DataFrame containing historical data, including Bitcoin price (btc_price) and ahr999 indicator.
        """
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')

        for i in range(len(df)):
            date = df.iloc[i]['Date']
            btc_price = df.iloc[i]['btc_price']
            ahr999_value = df.iloc[i]['ahr999']

            action, operation_amount = self.strategy.executeStrategy(btc_price, ahr999_value)

            current_value = self.calculate_portfolio_value(self.strategy.position, btc_price, self.strategy.cash)
            self.record_action(date, btc_price, ahr999_value, action, operation_amount, current_value)

        self.generate_charts(df)

    def record_action(self, date, btc_price, ahr999_value, action, operation_amount, current_value):
        """
        Records the action taken on each day.
        """
        self.daily_actions.append({
            'Date': date,
            'Bitcoin_Price': round(btc_price, 1),
            'ahr999': round(ahr999_value, 3),
            'Cash_Holdings': round(self.strategy.cash, 1),
            'Bitcoin_Quantity': round(self.strategy.position, 5),
            'Action': action,
            'Operation_Amount': round(operation_amount, 1),
            'Portfolio_Value': round(current_value, 1)
        })

    def calculate_portfolio_value(self, position, btc_price, cash):
        """
        Calculates the total value of the current portfolio.
        :param position: The current quantity of Bitcoin held.
        :param btc_price: The current price of Bitcoin.
        :param cash: The current cash balance.
        :return: The total value of the portfolio.
        """
        return cash + (position * btc_price)

    def generate_charts(self, df):
        """
        Generates charts to visualize the backtest process.
        """
        
        if not os.path.exists('imgs'):
            os.makedirs('imgs')
        
        actions_df = pd.DataFrame(self.daily_actions)

        # Chart 1: Cash and Bitcoin holdings over time
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.stackplot(actions_df['Date'], actions_df['Cash_Holdings'], labels=['Cash Holdings'], colors=['lightgreen'])
        ax1.set_xlabel('Date')
        ax1.set_ylabel('USDT Holdings')
        ax1.tick_params(axis='y', labelcolor='darkgreen')
        ax1.legend(loc='upper left')
        plt.xticks(rotation=45)
        ax2 = ax1.twinx()
        ax2.plot(actions_df['Date'], actions_df['Bitcoin_Quantity'], color='purple', label='Bitcoin Quantity')
        ax2.set_ylabel('Bitcoin Quantity')
        ax2.tick_params(axis='y', labelcolor='purple')
        ax2.legend(loc='upper right')
        plt.title('Cash and Bitcoin Holdings Over Time')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('imgs/cash_and_bitcoin_holdings_with_darker_color.png')
        plt.close()

        # Chart 2: Cumulative Investment vs Portfolio Value
        print(self.initial_cash)
        
        cumulative_investment = []
        current_investment = self.initial_cash

        for idx, row in actions_df.iterrows():
            if row['Action'] == 'Buy':
                current_investment += row['Operation_Amount']
            
            cumulative_investment.append(current_investment)

        actions_df['Cumulative_Investment'] = pd.Series(cumulative_investment)

        plt.figure(figsize=(10, 6))
        plt.plot(actions_df['Date'], actions_df['Cumulative_Investment'], label='Cumulative Investment', color='blue', linestyle='--')
        plt.plot(actions_df['Date'], actions_df['Portfolio_Value'], label='Portfolio Value', color='red')
        last_date = actions_df['Date'].iloc[-1]
        last_cumulative_investment = actions_df['Cumulative_Investment'].iloc[-1]
        plt.text(last_date, last_cumulative_investment, f'{last_cumulative_investment:.2f}', color='blue', ha='left', va='bottom')
        last_portfolio_value = actions_df['Portfolio_Value'].iloc[-1]
        plt.text(last_date, last_portfolio_value, f'{last_portfolio_value:.2f}', color='red', ha='left', va='bottom')
        plt.title('Cumulative Investment vs Portfolio Value')
        plt.xlabel('Date')
        plt.ylabel('Amount (USDT)')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig('imgs/cumulative_investment_vs_portfolio_value_with_last_value.png')
        plt.close()


        # Chart 3: Bitcoin price and buy/sell signals
        stop_investing = 1.10
        sell_threshold = 1.85
        buy_accumulated = 0.6
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.plot(actions_df['Date'], actions_df['Bitcoin_Price'], label='Bitcoin Price', color='blue')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Bitcoin Price', color='blue')
        ax1.set_ylim(30000, 85000)
        ax1.tick_params(axis='y', labelcolor='blue')
        buy_points = actions_df[actions_df['Action'] == 'Buy']
        plt.scatter(buy_points['Date'], buy_points['Bitcoin_Price'], color='green', label='Buy Points', marker='^', s=100)
        sell_points = actions_df[actions_df['Action'] == 'Sell']
        plt.scatter(sell_points['Date'], sell_points['Bitcoin_Price'], color='red', label='Sell Points', marker='v', s=100)
        plt.xticks(rotation=45)
        ax2 = ax1.twinx()
        ax2.bar(actions_df['Date'], actions_df['ahr999'], label='ahr999 Indicator', color='green', alpha=0.3)
        max_ahr999 = actions_df['ahr999'].max()
        ax2.set_ylim(0, max_ahr999 * 4)
        ax2.set_ylabel('ahr999 Indicator', color='green')
        ax2.tick_params(axis='y', labelcolor='green')
        ax2.axhline(y=stop_investing, color='red', linestyle='--', label='Stop Investing Line (1.10)')
        ax2.axhline(y=sell_threshold, color='orange', linestyle='--', label='Sell Line (1.85)')
        ax2.axhline(y=buy_accumulated, color='purple', linestyle='--', label='Buy Accumulated Line (0.6)')
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        plt.title('Bitcoin Price and Buy/Sell Signals')
        plt.tight_layout()
        plt.savefig('imgs/bitcoin_price_with_buy_sell_thresholds.png')
        plt.close()

    def save_results(self, filename='backtest_daily_actions.csv'):
        """
        Saves the backtest results to a CSV file.
        :param filename: The name of the file to save the results to.
        """
        actions_df = pd.DataFrame(self.daily_actions)
        actions_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Backtest completed. Results saved to '{filename}'.")
