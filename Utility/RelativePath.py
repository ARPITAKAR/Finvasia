import os


class Path:
    
    @staticmethod
    def relative_path():
        try:
            abs_path= os.getcwd()
            return abs_path
        except Exception as e:
            print(f"Error getting relative path: {e}")
            return None