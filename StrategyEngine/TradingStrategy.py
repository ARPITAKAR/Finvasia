import pandas as pd
from Utility.exchange import Exchange
from Utility.trading_symbol import Spot
class StrategyHeader:
    STRATEGYNAME= "Strategy"
    SPOT= "Spot"
    EXPIRYDATE= "ExpiryDate"
    STRIKEPRICE= "StrikePrice"
    OPTIONTYPE= "OptionType"
    QUANTITY= "Qty"
    ATMITMOTM= "AtmItmOtm"
    EXCHANGE= "NseNfo"

class StrategyEngine:

    def __init__(self, df_fno_master=None,df_cash_master=None):
        try:
            print("Reading Trading Strategy")
            self.df_fno_master = df_fno_master
            self.df_cash_master= df_cash_master
            col=[StrategyHeader.STRATEGYNAME,StrategyHeader.SPOT,StrategyHeader.EXPIRYDATE,StrategyHeader.STRIKEPRICE,
                 StrategyHeader.OPTIONTYPE,StrategyHeader.QUANTITY,StrategyHeader.ATMITMOTM,StrategyHeader.EXCHANGE]
            self.__df= pd.DataFrame(columns=col)
            
            
        except Exception as e:
            print(f"Error Generated while init.. trading engine{e}")
    # Static--Strategy--Spot--OptionType--Qty--AtmItmOtm
    # Dynamic--StrikePrice--ExpiryDate
    def _load_fno_strategy(self, symbol, strike):
        df = self.df_fno_master[
            (self.df_fno_master['Symbol'] == symbol) &
            (self.df_fno_master['StrikePrice'] == strike)
        ]
        
        strategies_deployed = [
            ['Bull Call Spread', symbol, '19-MAR-2026', '25000', 'PE', 100, 'ATM', 'NFO'],
            ['Bull Call Spread', symbol, '19-MAR-2026', '24000', 'PE', -100, 'ITM', 'NFO']
        ]
        for strategy in strategies_deployed:
            self.__df.loc[len(self.__df)]= strategy
    def _load_cash_strategy(self,symbol):
        df= self.df_cash_master[
            self.df_cash_master['Symbol']==symbol
        ]
        
        if df.empty:
            print("Symbol not found in cash master")
            
        jhunjhun=[
            ['Momentum Buy','symbol',None,None,None,100,None,'NSE'],
            ['Mean Reversion call',symbol,None,None,None,-100,None,'NSE']
        ]
        
        for s in jhunjhun:
            self.__df.loc[len(self.__df)]=s
    
    def get_trading_strategy(self):
        return self.__df