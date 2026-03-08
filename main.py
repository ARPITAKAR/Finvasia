# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 19:53:57 2026

@author: Arpit
"""
import TradingEngine as te

if __name__=='__main__':
    handler= te.TradingEngine()
    handler.MasterSymbolDownload()
    handler.ConnectBroker(broker_name="finvasia")
    handler.StartEngine()
    