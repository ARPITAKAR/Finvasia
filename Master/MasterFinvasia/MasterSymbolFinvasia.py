import os
import urllib.request
import zipfile
import pandas as pd


class MasterTypevar:
    With_Cash= "1"
    With_FNO= "2"
    With_Cash_Fno= "3"
    With_Curr= "4"
    With_Comm= "5"



class MasterSymbolFinvasia:
    # Function1: Constructor 
    def __init__(self,pathcwd):
        print("Accessing Master Symbol Finvasia...")
        self.__pathcwd= pathcwd
        self.__INIT()
        self.PrepareUrl()
        
    # Function2: Prepare the URL for downloading master symbol file
    def PrepareUrl(self):
        self.__NSE= "https://api.shoonya.com/NSE_symbols.txt.zip"
        self.__NFO= "https://api.shoonya.com/NFO_symbols.txt.zip"
        self.__CURR= "https://api.shoonya.com/CDS_symbols.txt.zip"
        self.__COMM= "https://api.shoonya.com/MCX_symbols.txt.zip"

    
    # Function3: Engine for master downloader and Unzip with dynamic in nature
    
    def __DownloadMasterFileUsingUrl(self,urladdress):
        try:
            print("End Point:", urladdress)
            folder_ext= self.GetFileExtension(urladdress)   
            
            outpath= self.__actual_path
            outpath+= "\\" + folder_ext
            print(f"Output path: {outpath}")
            
            with urllib.request.urlopen(urladdress) as response:
                data = response.read()
                with open(outpath, 'wb') as f:
                    f.write(data)

            unzip_path=self.__UnzipMasterFile(outpath)
            return unzip_path
                    
        except Exception as e:
            print(f"Error downloading master symbol file: {e}")
            
    # Function 4: Knowledge about the writing directory      
    def __INIT(self):
        self.__INITFolder= "INIT"
        self.__DestFolder= "MasterFinvasia"
        # C:\Users\Arpit\Desktop\Algorythm\AT_Exec\INIT\MasterFinvasia
        
        self.__actual_path= self.__pathcwd+ "\\" + self.__INITFolder + "\\" + self.__DestFolder
        print(f"Actual path: {self.__actual_path}")
        # Store the actual path for future use
        self.__pathCash= None
        self.__pathFNO= None
        self.__df_cash= pd.DataFrame()
        self.__df_fno= pd.DataFrame()

    # Function 5: Get file extension from URL
    def GetFileExtension(self,url):
        try:
            filename = url.split("/")[-1]
            return filename
        except Exception as e:
            print(f"Error getting file extension: {e}")
            return None
        
    # Function 6: Internally handling the different URL for downloading master symbol file
    def DownloadMaster(self,signal:str):
        try:
            print("Processing master symbol file...")
            print("Please wait while the master symbol file is being downloaded...")
            if signal== MasterTypevar.With_Cash:
                print("Downloading master symbol file for Cash segment...")
                self.__pathCash=self.__DownloadMasterFileUsingUrl(self.__NSE)
            elif signal== MasterTypevar.With_FNO:
                print("Downloading master symbol file for FNO segment...")
                self.__pathFNO=self.__DownloadMasterFileUsingUrl(self.__NFO)

            elif signal== MasterTypevar.With_Cash_Fno:
                print("Downloading master symbol file for Cash and FNO segment...")
                self.__pathCash=self.__DownloadMasterFileUsingUrl(self.__NSE)
                self.__pathFNO=self.__DownloadMasterFileUsingUrl(self.__NFO)

            elif signal== MasterTypevar.With_Curr:
                print("Downloading master symbol file for Currency segment...")
                self.__DownloadMasterFileUsingUrl(self.__CURR)

            elif signal== MasterTypevar.With_Comm:
                print("Downloading master symbol file for Commodity segment...")
                self.__DownloadMasterFileUsingUrl(self.__COMM)

            else:
                return
            
        except Exception as e:
            print(f"Error downloading master symbol file: {e}")

    # Function 7: Unzip the downloaded master symbol file


    def __UnzipMasterFile(self, zipfilepath: str):
        path= None
        try:
            print(f"Unzipping master symbol file: {zipfilepath}")

            # Get file name without .zip
            filename = os.path.basename(zipfilepath)
            folder_name = filename.replace(".txt.zip", "") # NSE_symbols.txt.zip -> NSE_symbols
            # Create full extraction path
            extract_path = os.path.join(self.__actual_path, folder_name)

            # Create folder if not exists
            os.makedirs(extract_path, exist_ok=True)

            # Extract inside that folder
            with zipfile.ZipFile(zipfilepath, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            print(f"Unzipping completed successfully, path: {extract_path}")
            path= extract_path
        except Exception as e:
            print(f"Error unzipping master symbol file: {e}")
        return path
    
    # Function 8: Read the master symbol text file and print the content

    def ReadMasterTextFile(self,signal:str):
        
        try:
            if signal == MasterTypevar.With_Cash:
                if self.__pathCash!= None:
                    print("--Reading Cash Master -- ")
                    self.__CashMasterOnly()
            elif signal == MasterTypevar.With_FNO:
                if self.__pathFNO!= None:
                    print("--Reading FNO Master -- ")
                    self.__FnoMasterOnly()
            elif signal == MasterTypevar.With_Cash_Fno:
                if self.__pathCash!= None:
                    print("--Reading Cash Master -- ")
                    self.__CashMasterOnly()
                if self.__pathFNO!= None:
                    print("--Reading FNO Master -- ")
                    self.__FnoMasterOnly()
                else:
                    print("Master symbol file for Cash or FNO segment is not available.")
            else:
                return
        except Exception as e:
            print(f"Error reading master symbol file: {e}")

    # Function 9: Read Cash master symbol file and print the content
    def __CashMasterOnly(self):
        try:
            path=os.path.join(self.__pathCash, "NSE_symbols.txt")
            print(f"Reading Cash master symbol file: {path}")
            self.__df_cash= pd.read_csv(path)
            self.__df_cash = self.__df_cash.loc[:, ~self.__df_cash.columns.str.contains('^Unnamed')]
            print("Rows in Cash Master:", len(self.__df_cash))
            print("Columns in Cash Master:", self.__df_cash.columns.tolist())
        except Exception as e:
            print(f"Error reading Cash master symbol file: {e}")
    
    # Function 10: Read FNO master symbol file and print the content

    def __FnoMasterOnly(self):
        try:
            path=os.path.join(self.__pathFNO, "NFO_symbols.txt")
            print(f"Reading FNO master symbol file: {path}")
            self.__df_fno= pd.read_csv(path)
            self.__df_fno = self.__df_fno.loc[:, ~self.__df_fno.columns.str.contains('^Unnamed')]
            print("Rows in FNO Master:", len(self.__df_fno))
            print("Columns in FNO Master:", self.__df_fno.columns.tolist())
        except Exception as e:
            print(f"Error reading FNO master symbol file: {e}")

    # Function 11: Get the master symbol dataframes for cash

    def GetCashMasterDataFrame(self):
        return self.__df_cash

    # Function 12: Get the master symbol dataframes for FNO
    def GetFnoMasterDataFrame(self):
        return self.__df_fno