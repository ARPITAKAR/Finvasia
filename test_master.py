from Master.MasterFinvasia.MasterSymbolFinvasia import MasterSymbolFinvasia
from Utility.RelativePath import Path
from Master.MasterFinvasia.MasterSymbolFinvasia import MasterTypevar

if __name__ == "__main__":
    path = Path.relative_path()
    obj = MasterSymbolFinvasia(path)
    obj.ReadMasterTextFile(MasterTypevar.With_Cash)