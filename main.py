import pandas as pd
from active_dca_strategy import ActiveDCA
from backtest import Backtest

def main():
    # Load your historical data from a CSV file
    try:
        df = pd.read_csv('historical_data.csv', encoding='utf-8')
        print("Data successfully loaded.")
    except FileNotFoundError:
        print("Error: The historical data file 'historical_data.csv' was not found.")
        return

    # Initialize the ActiveDCA strategy
    initial_cash = 10000  # Starting with 10,000 USDT
    strategy = ActiveDCA(cash=initial_cash)

    # Initialize the Backtest module with the strategy
    backtest = Backtest(strategy)

    # Run the backtest on the loaded data
    print("Running the backtest...")
    backtest.run_backtest(df)

    # Save the backtest results to a CSV file
    print("Saving the results...")
    backtest.save_results('backtest_results.csv')

    print("Backtest completed and results saved.")

if __name__ == "__main__":
    main()
