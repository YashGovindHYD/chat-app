from fastapi import FastAPI , HTTPException   #type :FastApi (from fastapi import APIRouter,... )    
from config.config import get_settings
import resend
resend_api_key = get_settings().resend_api_key
resend_from_email = get_settings().resend_from_email
resend.api_key = resend_api_key



async def send_otp_email(email:str,otp:str):
    try:
        result = await resend.Emails.send_async({
            "from": resend_from_email ,   # type : str (Your email id from which you want otp sent )   
            "to":email,
            "subject":"OTP Verification",   # type : str (Subject of the email )   
            "html":f'Your OTP is :  {otp}'
        }) 
    except Exception as e:
        print(str(e))
        raise HTTPException (status_code = 409 , detail = f"failed to Send Email{e}" ) 