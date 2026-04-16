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

    def __init__(self, df_fno_master):
        try:
            print("Reading Trading Strategy")
            self.df_fno_master = df_fno_master
            col=[StrategyHeader.STRATEGYNAME,StrategyHeader.SPOT,StrategyHeader.EXPIRYDATE,StrategyHeader.STRIKEPRICE,
                 StrategyHeader.OPTIONTYPE,StrategyHeader.QUANTITY,StrategyHeader.ATMITMOTM,StrategyHeader.EXCHANGE]
            self.__df= pd.DataFrame(columns=col)
            
            
        except Exception as e:
            print(f"Error Generated while init.. trading engine{e}")
    # Static--Strategy--Spot--OptionType--Qty--AtmItmOtm
    # Dynamic--StrikePrice--ExpiryDate
    def read_input(self,symbol,Strikeprice):
        df = self.df_fno_master[
            (self.df_fno_master['Symbol']==symbol) &
            (self.df_fno_master['StrikePrice']==Strikeprice)
        ]
        print(df)
        strategies_deployed=[
            ['Bull Call Spread',Spot.NIFTY.value,'19-MAR-2026','25000','PE',100,'ATM',Exchange.NFO.value],
            ['Bull Call Spread',Spot.NIFTY.value,'19-MAR-2026','24000','PE',-100,'ITM',Exchange.NFO.value]
        ]
        for strategy in strategies_deployed:
            self.__df.loc[len(self.__df)]= strategy
    
    def get_trading_strategy(self):
        return self.__df