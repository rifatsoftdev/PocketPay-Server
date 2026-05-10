from fastapi import BackgroundTasks

from app.constants.colors import AnsiColor

from app.dependencies.email_serivce import EmailSent
from app.templates import EmailTemplate, SMSTemplate, PushTemplate



email_manager = EmailSent()
# sms_manager = SMSSent()




def send_otp_email(email, otp):
    try:
        status = email_manager.send_email(
            to_email=email, 
            subject="Your Verification Code on PocketPay", 
            body=EmailTemplate.otp_template(
                name=email,
                otp=otp
            )
        )
        return status
    
    except Exception as e:
        print(f"{AnsiColor.RED}INFO{AnsiColor.RESET}:     {e}")
        return False 

def send_welcome_email(email):
    status = email_manager.send_email(
        to_email=email,
        subject="Welcome to PocketPay",
        body=EmailTemplate.welcome_email_template(email)
    )
    return status

def send_reset_password_email(name, email, otp_token):
    status = email_manager.send_email(
        to_email=email, 
        subject="Reset Password",
        body=EmailTemplate.reset_password_template(
            name=name,
            email=email,
            reset_link=otp_token
        )
    )
    return status