from enum import Enum,auto,unique

class Exchange(Enum):

    def _generate_next_value_(name, start, count, last_values):
        return name.upper()
    NSE= auto()
    NFO= auto()
    BSE= auto()
    CDS= auto()
    MCX= auto()
    
    
print(list(Exchange))