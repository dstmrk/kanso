import os
from dotenv import load_dotenv

def load_env(key: str) -> str:
    load_dotenv()
    return os.getenv(key)

def parse_money(moneyvalue: str) -> float:
    moneyvalue = moneyvalue.replace("€","").replace(" ","").replace(".","").replace(",",".")
    try:
        return float(moneyvalue)
    except(ValueError, TypeError):
        return 0.0