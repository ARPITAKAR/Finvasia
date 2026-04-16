# file: spot_enum.py

from enum import Enum, auto, unique

@unique
class Spot(Enum):

    # Function: _generate_next_value_
    # Purpose: Automatically assign uppercase string values
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()

    # SPOT indices
    NIFTY = auto()
    NIFTYNXT50 = auto()
    FINNIFTY = auto()
    BANKNIFTY = auto()
    MIDCPNIFTY = auto()


# Function: main (execution demo)
if __name__ == "__main__":
    print(list(Spot))