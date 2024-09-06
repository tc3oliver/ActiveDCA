import requests
from math import log10
from datetime import datetime

class ActiveDCA:
    """
    ActiveDCA is a strategy class for executing dynamic cost averaging based on Bitcoin price movements and market indicators.
    This strategy adjusts the amount of investment dynamically according to the market's state, allowing for more intelligent decision-making in both bull and bear markets.
    
    Attributes:
        cash (float): The initial cash amount to start the strategy with. It is used to execute buys and dip-buys, and it accumulates when the market is not favorable for investment.
        
        stop_investing (float): This threshold is based on the DCA value. If the DCA value is below this threshold, the strategy will continue investing more into Bitcoin, recognizing that the market is potentially undervalued. The lower the DCA value, the larger the relative investment.
        
        sell_threshold (float): This threshold determines when the strategy will sell all held Bitcoin positions. When the DCA value exceeds this threshold, it indicates that the market might be overvalued, so the strategy exits the market by selling the entire position.
        
        dip_buy_threshold (float): When the market presents a significant dip, defined by a DCA value below this threshold, the strategy will utilize a percentage of the available cash to buy Bitcoin. This aims to capitalize on sudden drops in price, capturing potential recovery gains.
        
        invest_percentage (float): The percentage of the total available cash that will be used for the dip-buy when the dip-buy conditions are met. This ensures that the strategy only uses part of the cash for dip-buying, preserving liquidity for future dips or market conditions.
        
        daily_investment (float): A fixed daily amount to be invested under normal conditions. This follows a dollar-cost averaging (DCA) approach, where regular investments are made regardless of the price level to reduce the effect of volatility over time.
        
        weight_coefficient (float): A coefficient used to adjust the daily investment dynamically based on the current DCA value. If the market is below certain thresholds, this coefficient allows the strategy to scale the investment, making larger investments when the DCA value is lower.
        
        position (float): The number of Bitcoin units currently held in the portfolio. This reflects the total Bitcoin accumulated through various buys and dip-buys and is sold when the sell threshold is reached.
    
    Strategy Details:
        1. **Dynamic Investment**: 
            - The amount to be invested daily is not fixed but adjusted dynamically according to the DCA value. When the DCA value is low (indicating a potentially undervalued market), the strategy increases the investment amount. 
            - The investment is scaled using the `weight_coefficient`, which ensures that during high-risk periods (low DCA value), larger investments are made.
        
        2. **Dip Buying**:
            - If the market experiences a significant dip, defined by a DCA value lower than the `dip_buy_threshold`, the strategy takes advantage by allocating a portion of the available cash (determined by `invest_percentage`) to buy Bitcoin.
            - This allows the strategy to accumulate Bitcoin during temporary price drops, positioning it to benefit from future recoveries.
        
        3. **Exit Strategy**:
            - When the DCA value exceeds the `sell_threshold`, the strategy interprets this as a signal that the market is overvalued and sells the entire Bitcoin position.
            - The goal is to exit before significant market corrections while securing profits from previously accumulated Bitcoin.
        
        4. **Cash Accumulation**:
            - When the market is in a neutral state (DCA between `stop_investing` and `sell_threshold`), no Bitcoin is purchased. Instead, the daily investment is accumulated in cash.
            - This ensures that the strategy has liquidity available for future dip-buys or for reinvestment when the DCA value drops again.
        
        5. **Reinvestment**:
            - When the DCA value drops below the `stop_investing` threshold after cash accumulation, the strategy resumes regular buying, using both the accumulated cash and the daily investment.
            - This ensures that the strategy consistently allocates funds to Bitcoin while retaining flexibility to adjust based on market conditions.
    """

    
    def __init__(self, cash, stop_investing=1.10, sell_threshold=1.85, dip_buy_threshold=0.6, invest_percentage=0.7, daily_investment=100, weight_coefficient=1.0):
        self.stop_investing = stop_investing
        self.sell_threshold = sell_threshold
        self.dip_buy_threshold = dip_buy_threshold
        self.invest_percentage = invest_percentage
        self.daily_investment = daily_investment
        self.weight_coefficient = weight_coefficient
        self.position = 0
        self.cash = cash

    def calculateActiveDCA(self):
        """
        This method calculates the Active DCA value based on Bitcoin's historical data, target price, and its 200-day moving average.
        The algorithm is inspired by the AHR999 indicator, which multiplies the ratio of Bitcoin's current price to its fitted growth value 
        (logarithmic growth based on Bitcoin's age) by the ratio of Bitcoin's price to the 200-day moving average.
        This returns a combined indicator of whether the price is high or low relative to long-term trends.
        """
        birth_date = datetime(year=2009, month=1, day=3)
        today = datetime.now()
        age_days = (today - birth_date).days
        target_price = 10 ** (5.84 * log10(age_days) - 17.01)

        cur_price_url = 'https://api.coindesk.com/v1/bpi/currentprice/USD.json'
        try:
            response = requests.get(cur_price_url)
            cur_price = response.json()["bpi"]["USD"]["rate_float"]
        except Exception as e:
            print(f"Error fetching current price: {e}")
            return None, None

        history_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': '200'
        }
        try:
            res = requests.get(history_url, params=params)
            price_json = res.json()
            prices = [price[1] for price in price_json['prices']]
        except Exception as e:
            print(f"Error fetching historical prices: {e}")
            return None, None

        if len(prices) < 200:
            print("Not enough data points for 200-day average.")
            return None, None

        price_sum = sum(prices)
        average_200_day_price = price_sum / len(prices)
        p1 = cur_price / target_price
        p2 = cur_price / average_200_day_price
        p = p1 * p2

        return p, cur_price

    def executeStrategy(self, btc_price=None, ahr999_value=None):
        """
        Executes the investment strategy based on the provided or calculated active DCA value and market conditions.
        :param btc_price: Optional, the current price of Bitcoin.
        :param ahr999_value: Optional, the calculated ahr999 value.
        :returns: The action taken (buy, sell, hold, or dip-buy) and the corresponding amount of Bitcoin or cash involved.
        """
        if btc_price is None or ahr999_value is None:
            # Fallback to calculate the values if not provided
            ahr999_value, btc_price = self.calculateActiveDCA()
            if ahr999_value is None or btc_price is None:
                print("Error in fetching data, cannot execute strategy.")
                return None, None

        dynamic_investment = self.daily_investment * (self.weight_coefficient / ahr999_value)
        action = 'Hold'
        operation_amount = 0

        if ahr999_value < self.stop_investing:
            self.position += (dynamic_investment / btc_price)
            action = 'Buy'
            operation_amount = dynamic_investment
        elif self.stop_investing <= ahr999_value < self.sell_threshold:
            self.cash += self.daily_investment
            action = 'Hold'
        elif ahr999_value >= self.sell_threshold and self.position > 0:
            sell_amount = self.position * btc_price
            self.cash += sell_amount
            self.position = 0
            action = 'Sell'
            operation_amount = sell_amount

        if ahr999_value < self.dip_buy_threshold and self.cash > 0:
            invest_amount = self.cash * self.invest_percentage
            self.position += (invest_amount / btc_price)
            self.cash -= invest_amount
            action = 'DipBuy'
            operation_amount = invest_amount

        return action, operation_amount