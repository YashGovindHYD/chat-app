import random
from pwdlib import PasswordHash
from config.config import get_settings
settings = get_settings()

pwd_context = PasswordHash.recommended()


def hash_otp(code:str)->str:
    return pwd_context.hash(code)

def verify_otp_hash(code:str,hashed_code:str)->bool:
    return pwd_context.verify(code,hashed_code)
    
def generate_otp(length:int=4)->str:
    code = ""
    for _ in range(length):  
        code+=str(random.choice('0123456789'))
    return str(code)

