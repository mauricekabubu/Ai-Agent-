import africastalking 
import os
from dotenv import load_dotenv

load_dotenv()

africastalking.initialize(
    username=os.getenv("AFRICAS_TALKING_USERNAME"),
    api_key=os.getenv("SMS_API_KEY")
)

sms = africastalking.SMS

def welcome():
    recipients = ["+254716540107"]
    message = "Hi there this our message from Farmhub."
    sender = os.getenv("SENDER_ID")
    
    try:
        response = sms.send(message, recipients, sender)
        print(response)
    except Exception as e:
        print(f"Maurice there is a problem in {str(e)}")
        