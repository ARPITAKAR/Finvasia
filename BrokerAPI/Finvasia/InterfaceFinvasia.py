from BrokerAPI.Finvasia.api_helper import ShoonyaApiPy
from Credentials.credbrokers import CredentialFinvasia
import datetime as datetime
import time
import pandas as pd

# https://shoonya.com/api-documentation
# https://github.com/Shoonya-Dev/ShoonyaApi-py?tab=readme-ov-file#md-login


class InterfaceFinvasia:
    def __init__(self):
        print("Initializing Interface for Finvasia...")
        self.shoonyaApi = ShoonyaApiPy()
        self.isconnected= False
        self.__websocket_started= False
        self.__set_up_feed()
        self.SYMBOLDICT={}
    def login_panel(self):
        # User requested
        totp = self.get_totp() # Digit numeric
        if totp == -1:
            print("Login failed due to invalid TOTP.")
            return
        totp = str(totp)  # Convert to string if it's not already
        
        res = self.shoonyaApi.login(
            userid=CredentialFinvasia.Uid,
            password=CredentialFinvasia.password,
            twoFA=totp,
            vendor_code=CredentialFinvasia.VendorCode,
            imei=CredentialFinvasia.IMEI,
            api_secret=CredentialFinvasia.APIKEY
        )
        print(res)
        login_ok = res.get("stat", False)

        print(f"Login successful: {login_ok}")

        if login_ok:
            self.__succesfully_connected()
            print("Connection to Finvasia established successfully.")
        else:
            print("Login failed. Please check your credentials and TOTP.")
        
            
    # Getting totp for 2FA
    def get_totp(self):
        try:
            totp= int(input("Enter the TOTP for 2FA: "))
            print("TOTP for 2FA:", totp)
            return totp
        except Exception as e:
            print("Error getting TOTP:", e)
            return -1

    


    # Connection Establishment =='OK'
    def __succesfully_connected(self):
        try:
            self.isconnected = True
            print("Logged in to Finvasia successfully.")
        except Exception as e:
            print("Error logging in, establishing connection to Finvasia:", e)
            self.isconnected = False
            
    # Confirm client about connecttion status
    def connection_status(self):
        if self.isconnected:
            print("Connection to Finvasia is active.")
            return True
        else:
            print("Not connected to Finvasia. Please login first.")
            return False
        
            
    # Requesting data from broker servers through API
    def RequestToBroker(self):
        if self.connection_status():
            print("Requesting data from Finvasia...")
            # Implement your data request logic here
            print("Get Historical Data")
            current_date= datetime.datetime.today()
            previous_date= current_date - datetime.timedelta(days=1)
            uxEntryTime=int(previous_date.timestamp())
            print(f"Requesting historical data from {previous_date} to {current_date} (Unix time: {uxEntryTime})")
            return_ohlc= self.shoonyaApi.get_time_price_series(exchange="NSE", token="26000", starttime=str(uxEntryTime), endtime=None)
            if return_ohlc is None:
                print("Failed to fetch historical data.")
                return False
            else:
                print("Historical data fetched successfully.")
#                print(return_ohlc)  # Print the fetched historical data
                return return_ohlc   # 👈 THIS is the key line
        else:
            print("Cannot request data. Please connect to Finvasia first.")
    
    # Finvasia API Documentation: https://cdn.sanity.io/files/3n8bfe6i/production/ff63049ecd3370926c77fca0ed82f1e960273367.pdf
    # Finvasia Python SDK: https://github.com/Shoonya-Dev/ShoonyaApi-py/tree/master/tests
    # Transmiiting data to broker order management system through API
    # File: InterfaceFinvasia.py
# Function: TransmitToBroker

    def TransmitToBroker(self, buy_or_sell, product_type, exchange, tradingsymbol,
                        quantity, discloseqty, price_type, price, trigger_price,
                        retention, remarks, bookloss_price, bookprofit_price,
                        trail_price, amo):

        try:
            print("Sending order to broker OMS...")

            ORDER_MESSAGE = self.shoonyaApi.place_order(
                buy_or_sell=buy_or_sell,
                product_type=product_type,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                quantity=int(quantity),
                discloseqty=int(discloseqty),
                price_type=price_type,
                price=float(price),
                trigger_price=trigger_price,
                retention=retention,
                amo=amo,
                remarks=remarks
            )

            print("Order response:", ORDER_MESSAGE)

            if ORDER_MESSAGE.get("stat") == "Ok":
                print("Order placed successfully.")
                return int(ORDER_MESSAGE['norenordno'])
            else:
                print("Order failed:", ORDER_MESSAGE)
                return -1

        except Exception as e:
            print(f"Error transmitting order: {e}")
            return -1
    
    
    # Connection forcefully closing : Logout from broker server
    def CloseConnection(self):
        try:
            if not self.isconnected:
                print("Already logged out from Finvasia.")
                return
            print("Logging out from Finvasia...")
            logout_response = self.shoonyaApi.logout()
            if logout_response.get("stat", False)=="Ok":
                self.isconnected = False
                print("Successfully logged out from Finvasia.")
            else:
                print("Logout failed. Please try again.")
        except Exception as e:
            print(f"Error logging out from Finvasia: {e}")
            
            
    #Critical callbacks-- Heart of the engine
    # Client(Trading Engine) --> No permission to use
    # Ownership--> Trading Venue | Finvasia
    # Run on Thread pool
    # Active Feed dataframe
    def __set_up_feed(self):
        self.df_feed = pd.DataFrame({
                'Token': pd.Series(dtype='str'),
                'TradingSymbol': pd.Series(dtype='str'),
                'LTP': pd.Series(dtype='float'),
                'Open': pd.Series(dtype='float'),
                'High': pd.Series(dtype='float'),
                'Low': pd.Series(dtype='float'),
                'Close': pd.Series(dtype='float'),
                'Vol': pd.Series(dtype='float'),
                'LastUpdated': pd.Series(dtype='datetime64[ns]')
            })

        # O(1) lookup structure
        self.token_index = {}
        # Update this part to recieve data
    
    # Function 9 -- Critical|Client not permitted|Ownership of Finvasia|Runs on WebSocket thread pool
    def __event_handler_order_update(self,message):
        print("order event: " + str(message))


    
    # Tick by tick data feed from broker server through WebSocket streaming
    # Function 10 -- Critical|Client not permitted|Ownership of Finvasia|Runs on WebSocket thread pool
    def __event_handler_quote_update(self, message):

        ltp, open_p, high, low, close, volume = 0,0,0,0,0,0

        try:

            token = message['tk']
            # print("Incoming Token",token)
            if 'lp' in message:
                ltp = float(message['lp'])

            if 'o' in message:
                open_p = float(message['o'])

            if 'h' in message:
                high = float(message['h'])

            if 'l' in message:
                low = float(message['l'])

            if 'c' in message:
                close = float(message['c'])

            if 'v' in message:
                volume = float(message['v'])


            # -----------------------------
            # NEW TOKEN ARRIVED
            # -----------------------------
            if token not in self.token_index:
                # print("ADDING NEW TOKEN TO FEED:", token)
                idx = len(self.df_feed)

                new_record = {
                    'Token': token,
                    'TradingSymbol': self.SYMBOLDICT.get(token, 'NA'),
                    'LTP': ltp,
                    'Open': open_p,
                    'High': high,
                    'Low': low,
                    'Close': close,
                    'Vol': volume,
                    'LastUpdated': pd.Timestamp.now()
                }

                self.df_feed.loc[idx] = new_record

                # store index for O(1) lookup
                self.token_index[token] = idx
                

            # -----------------------------
            # EXISTING TOKEN UPDATE
            # -----------------------------
            else:

                idx = self.token_index[token]

                if ltp > 0:
                    self.df_feed.at[idx,'LTP'] = ltp

                if open_p > 0:
                    self.df_feed.at[idx,'Open'] = open_p

                if high > 0:
                    self.df_feed.at[idx,'High'] = high

                if low > 0:
                    self.df_feed.at[idx,'Low'] = low

                if close > 0:
                    self.df_feed.at[idx,'Close'] = close

                if volume > 0:
                    self.df_feed.at[idx,'Vol'] = volume
                self.df_feed.at[idx, 'LastUpdated'] = pd.Timestamp.now()
               
            print(self.df_feed.tail())

        except Exception as e:
            print("Quote handler error:", e)
        '''Multi-Cursor with Mouse Windows / Linux: Alt + Click
        Select All Occurrences Instantly Windows / Linux: Ctrl + Shift + L\
        Select Next Occurrence Windows / Linux: Ctrl + D'''
        
      

                # self.df_feed = pd.concat(
                #     [self.df_feed, pd.DataFrame([new_record])],
                #     ignore_index=True
                # )
                # ADD NEW RECORD TO DF
        # try:
        #     if 'lp' in message:
        #         ltp = float(message['lp'])
        #     if 'o' in message:
        #         open = float(message['o'])
        #     if 'h' in message:
        #         high = float(message['h'])
        #     if 'l' in message:
        #         low = float(message['l'])
        #     if 'c' in message:
        #         close = float(message['c'])
        #     if 'v' in message:
        #         volume = float(message['v'])
        #     if ltp > open and ltp - (open+high+low+close)/4 > 10:
        #         print("token satisfied:",message.get('e','Exchange Fucked'),ltp,(open+high+low+close)/4, message.get('tk', 'Unknown Token'))
        # except Exception as e:
        #     print(f"Error processing quote update message: {e}")
#e   Exchange #tk  Token #lp  LTP #pc  Percentage change #v   volume #o   Open price #h   High price
#l   Low price #c   Close price #ap  Average trade price

# Function 11 -- Critical|Client not permitted|Ownership of Finvasia|Runs on WebSocket thread pool
    def __open_callback(self):
    
        print('app is connected')
        broker_tokens= ['NSE|33','NSE|69']  # Example tokens, replace with actual tokens you want to subscribe to
        # SubscribeTokenToBroker Crtical function| Client not permitted to use this function directly|Ownership of Finvasia|Runs on WebSocket thread pool
        self.__WebSocketConnectionStatus()  # Update WebSocket connection status when the connection is opened to True
        self.SubscribeTokenToBroker(tokenlist=broker_tokens)  # Subscribe to tokens when WebSocket connection is established
        #api.subscribe(['NSE|22', 'BSE|522032'])

    # Client requested to start streaming data using WebSocket    
    # Function 12 -- Client requested|Client permitted|Ownership of Finvasia|Runs on main thread   
    def StartStreamingUsingWebSocket(self)->None:
        try:
            if not self.isconnected:
                print("Cannot start streaming. Please connect to Broker first to Begin with streaming.")
                return None
            print("Starting WebSocket streaming from Finvasia...")
            # Implementing our WebSocket streaming logic here
            # here all arguments are optional, you can choose to implement only the ones you need
            '''subscribe_callback = None, 
                        order_update_callback = None,
                        socket_open_callback = None,
                        socket_close_callback = None,
                        socket_error_callback = None'''
            # api.start_websocket(order_update_callback=event_handler_order_update, subscribe_callback=event_handler_quote_update, socket_open_callback=open_callback)
            
            self.shoonyaApi.start_websocket(order_update_callback=self.__event_handler_order_update, subscribe_callback=self.__event_handler_quote_update, socket_open_callback=self.__open_callback,socket_close_callback=None, socket_error_callback=None)
            time.sleep(2)
            print("WebSocket streaming started successfully.")
        except Exception as e:
            print(f"Error starting WebSocket streaming from Finvasia: {e}")
            
    # Subscribing tokens dynamically to the WebSocket stream
    # Function 13 -- Client requested|Client permitted|Ownership of Finvasia|Runs on main thread
    def SubscribeTokenToBroker(self,tokenlist=None):
        try:
            if self.IsWebSocketConnectionOpened()==False:
                print("Error!! WebSocket connection Failure.")
                return # early exit if WebSocket connection is not open
            # Handle the function for list collection
            if isinstance(tokenlist, list) and len(tokenlist) > 0:
                print("Bulk subscribing to tokens:",len(tokenlist))
                self.shoonyaApi.subscribe(tokenlist)
            else:
                print("One on One subscribing to token:",tokenlist)
                self.shoonyaApi.subscribe(tokenlist)
            print("Dynamically subscribed to tokens successfully.")
        except Exception as e:
            print(f"Error subscribing to tokens dynamically: {e}")
            
    # Function14 : Webscoket connection is open or not <Price(H,MF) ,order update(MF), or any other event>
    def __WebSocketConnectionStatus(self):
        try:
            self.__websocket_started= True
            
        except Exception as e:
            print(f"Error checking WebSocket connection status: {e}")
    
    # Function 15: Allow client(Trading Engine) to check if WebSocket connection is active or not
    def IsWebSocketConnectionOpened(self):
        return self.__websocket_started
    
    # Function16: Get Complete Order Book from trading engine...
    def GetCompleteOrderBook(self):
        try:
            print("Client requested complete order book from Finvasia...")
            if not self.isconnected:
                print("Cannot fetch order book. Please connect to Finvasia first.")
                return None
            print("Fetching complete order book from Finvasia...")
            # Implement your logic to fetch complete order book here using Finvasia API
            getOrderBook= self.shoonyaApi.get_order_book()
            if getOrderBook is None:
                print("No packet received for order book request.")
                return
            
            # Example: order_book = self.shoonyaApi.get_order_book()
            print(f"Complete order book fetched successfully: {getOrderBook}")
            # return order_book
            for trade in getOrderBook:
                print(f"Order Book Entry: {trade}")
        except Exception as e:
            print(f"Error fetching complete order book from Finvasia: {e}")
            return None
        
    # Function 17: Get Executed Trade Book from trading Venue...   
    def GetExecutedTradeBookFromTradingVenue(self):
        try:
            print("Requesting executed trade book from Finvasia...")
            if not self.isconnected:
                print("Cannot fetch executed trade book. Please connect to Finvasia first.")
                return None
            
            getTradeBook= self.shoonyaApi.get_trade_book()
            if getTradeBook is None:
                print("No packet received for trade book request.")
                return
            # print(f"Executed trade book fetched successfully: {getTradeBook}")
            for trade in getTradeBook:
                print(f"Executed Trade Book Entry: {trade}")
            total_trades= len(getTradeBook)
            print(f"Total executed trades: {total_trades}")
        except Exception as e:
            print(f"Error fetching executed trade book from Finvasia: {e}")
            return None    
        
    # Function 18: Get Net Position from trading venue for a specific token
    def GetNetPositionForToken(self):
        try:
            print("Requesting net position for token from Finvasia...")
            if not self.isconnected:
                print("Cannot fetch net position. Please connect to Finvasia first.")
                return None
            # Implement your logic to fetch net position for a specific token here using Finvasia API
            getNetPosition= self.shoonyaApi.get_positions()
            if getNetPosition is None:
                print("No packet received for net position request.")
                return
            for position in getNetPosition:
                print(f"Net Position Entry: {position}")
            len_positions= len(getNetPosition)
            print(f"Total net position entries: {len_positions}")
        except Exception as e:
            print(f"Error fetching net position for token from Finvasia: {e}")
            return None
        
    # InterfaceFinvasia.py

    def LoadSymbolMap(self, token_symbol_map: dict):
        """
        Inject a pre-built {token_str -> TradingSymbol} dict.
        Called once by TradingEngine after masters are loaded.
        """
        self.SYMBOLDICT = token_symbol_map
        print(f"Symbol map loaded: {len(self.SYMBOLDICT)} tokens registered.")