import urllib.request



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
                    
        except Exception as e:
            print(f"Error downloading master symbol file: {e}")
            
    # Function 4: Knowledge about the writing directory      
    def __INIT(self):
        self.__INITFolder= "INIT"
        self.__DestFolder= "MasterFinvasia"
        # C:\Users\Arpit\Desktop\Algorythm\AT_Exec\INIT\MasterFinvasia
        
        self.__actual_path= self.__pathcwd+ "\\" + self.__INITFolder + "\\" + self.__DestFolder
        print(f"Actual path: {self.__actual_path}")
        
        
    # Function 5: Get file extension from URL
    def GetFileExtension(self,url):
        try:
            filename = url.split("/")[-1]
            return filename
        except Exception as e:
            print(f"Error getting file extension: {e}")
            return None
        
    # Function 6: Internally handling the different URL for downloading master symbol file
    def DownloadMaster(self):
        try:
            print("Processing master symbol file...")
            print("Please wait while the master symbol file is being downloaded...")
            
            self.__DownloadMasterFileUsingUrl(self.__NSE)
            self.__DownloadMasterFileUsingUrl(self.__NFO)
            
        except Exception as e:
            print(f"Error downloading master symbol file: {e}")