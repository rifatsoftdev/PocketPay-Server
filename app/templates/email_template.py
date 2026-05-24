from app.constants import String


def main_structure(body: str):
    return f"""
<html>
  <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
      <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
        
          <!-- Header -->
          <tr>
              <td style="background-color:#1E88E5; padding:25px; text-align:center;">
                  <img src="{String.COMPANY_LOGO}" alt="{String.COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
              </td>
          </tr>

          <!-- Body -->
          {body}

          <!-- Footer -->
          <tr>
            <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
              {String.COMPANY_NAME} | {String.COMPANY_ADDRESS} | {String.COMPANY_CONTACT}<br>
              &copy; {String.COMPANY_NAME} {2026}
            </td>
          </tr>

      </table>
  </body>
</html>
"""


class EmailTemplate:
    @staticmethod
    def welcome_email_template(name: str):
        return {
            "title": "Welcome to PocketPay!",
            "body": main_structure("""
              <tr>
                  <td style="padding:35px; text-align:center;">
                      <h2 style="color:#333333; margin-bottom:15px;">Welcome, {name}!</h2>
                      
                      <p style="color:#555555; font-size:16px; line-height:1.5;">
                          Thank you for joining <strong>{String.COMPANY_NAME}</strong>! We're excited to have you on board.
                      </p>

                      <p style="color:#555555; font-size:16px; line-height:1.5;">
                          Get ready to explore our services and enjoy seamless experiences with your new account.
                      </p>

                      <p style="color:#555555; font-size:16px; line-height:1.5; margin-top:25px;">
                          If you have any questions, our support team is always here to help.
                      </p>

                      <div style="text-align:center; margin-top:30px;">
                          <a href="" style="display:inline-block; background-color:#1E88E5; color:#ffffff; text-decoration:none; padding:14px 28px; border-radius:6px; font-size:16px; font-weight:bold;">Get Started</a>
                      </div>
                  </td>
              </tr>
              """
            )
        }

    @staticmethod
    def otp_email_template(name: str, email: str, otp: str):
        return {
            "title": "Your OTP Code for PocketPay",
            "body": main_structure("""
              <!-- Body -->
              <tr>
                <td style="padding:35px; text-align:center;">
                  <h2 style="color:#333333; margin-bottom:15px;">Welcome, {name}!</h2>
                  <p style="color:#555555; font-size:16px; line-height:1.5;">
                    You're almost ready to start using <strong>{String.COMPANY_NAME}</strong>.  
                    Please use the verification code below to confirm your email address.
                  </p>

                  <div style="margin:25px 0;">
                    <span style="display:inline-block; font-size:36px; font-weight:bold; color:#1E88E5; padding:15px 30px; border:2px dashed #1E88E5; border-radius:8px;">{otp}</span>
                  </div>

                  <p style="color:#555555; font-size:15px; line-height:1.5;">
                    This code is valid for the next 5 minutes.  
                    If you did not request this, please ignore this email.
                  </p>

                  <p style="color:#999999; font-size:13px; margin-top:30px;">
                    Thank you for choosing {String.COMPANY_NAME}. Let's get started!
                  </p>
                </td>
              </tr>
            """
          )
        }

    @staticmethod
    def login_alert_email_template(name: str, ip_address: str):
        return {
            "title": "New Login Detected 🔐",
            "body": f"""
    <html>
      <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
        <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background-color:#1E88E5; padding:25px; text-align:center;">
              <img src="{String.COMPANY_LOGO}" alt="{String.COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:35px; text-align:center;">
              <h2 style="color:#333333; margin-bottom:15px;">Hi {name},</h2>
              <p style="color:#555555; font-size:16px; line-height:1.5;">
                We detected a new login to your <strong>{String.COMPANY_NAME}</strong> account.
              </p>

              <div style="background-color:#f1f2f6; padding:18px; border-radius:8px; margin:20px 0; text-align:left; font-size:14px; color:#333333;">
                <p style="margin:6px 0;"><strong>IP Address:</strong> {ip_address}</p>
                <p style="margin:6px 0;"><strong>Location:</strong> Unknown</p>
                <p style="margin:6px 0;"><strong>Time:</strong> Just now</p>
              </div>

              <p style="color:#555555; font-size:15px; line-height:1.5;">
                If this was you, you can safely ignore this message. If you did not sign in, please secure your account immediately by resetting your password and reviewing recent activity.
              </p>

              <div style="text-align:center; margin-top:25px;">
                <a href="" style="display:inline-block; background-color:#E53935; color:#ffffff; text-decoration:none; padding:12px 24px; border-radius:6px; font-size:15px; font-weight:bold;">Secure Account</a>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
              {String.COMPANY_NAME} | {String.COMPANY_ADDRESS} | {String.COMPANY_CONTACT}<br>
              &copy; {String.COMPANY_NAME} {2026}
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
        }

    @staticmethod
    def kyc_update_email_template(name: str, status: str):
        return {
            "title": "KYC Verification Update",
            "body": f"""
    <html>
      <body style="margin:0; padding:0; font-family:'Helvetica Neue',
            """
        }







    @staticmethod
    def reset_password_template(name: str, email: str, reset_link: str):
        return f"""
    <html>
      <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
        <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background-color:#1E88E5; padding:25px; text-align:center;">
              <img src="{String.COMPANY_LOGO}" alt="{String.COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:35px; text-align:center;">
              <h2 style="color:#333333; margin-bottom:15px;">Hello, {name}</h2>
              <p style="color:#555555; font-size:16px; line-height:1.5;">
                We received a request to reset the password for your account <strong>{email}</strong>.  
                Click the button below to set a new password securely.
              </p>

              <a href="http://192.168.1.100:8000/auth/reset-password/{reset_link}" style="display:inline-block; background-color:#1E88E5; color:#ffffff; text-decoration:none; padding:15px 30px; border-radius:5px; font-size:16px; margin:25px 0;">Reset Password</a>

              <p style="color:#555555; font-size:15px; line-height:1.5;">
                This link is valid for the next 15 minutes.  
                If you did not request a password reset, you can safely ignore this email — your account is safe.
              </p>

              <p style="color:#999999; font-size:13px; margin-top:30px;">
                Thank you for using {String.COMPANY_NAME}. Stay secure!
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
              {String.COMPANY_NAME} | {String.COMPANY_ADDRESS} | {String.COMPANY_CONTACT}<br>
              &copy; {String.COMPANY_NAME} {2026}
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    @staticmethod
    def money_sent_template(user_name: str, recipient: str, amount: float, txn_id: str, date: str):
        return f"""
    <html>
      <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
        <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
          
          <!-- Header -->
          <tr>
            <td style="background-color:#1E88E5; padding:25px; text-align:center;">
              <img src="{String.COMPANY_LOGO}" alt="{String.COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:35px;">
              <h2 style="color:#333333; text-align:center; margin-bottom:20px;">Payment Sent Successfully</h2>
              
              <p style="color:#555555; font-size:16px; line-height:1.5;">Hi {user_name},</p>
              
              <p style="color:#555555; font-size:16px; line-height:1.5;">
                Your payment of <strong>${amount}</strong> has been successfully sent to <strong>{recipient}</strong>.
              </p>
              
              <div style="background-color:#f1f2f6; padding:15px; border-radius:8px; margin:20px 0; text-align:left; font-size:14px; color:#333333;">
                <p><strong>Transaction ID:</strong> {txn_id}</p>
                <p><strong>Date:</strong> {date}</p>
              </div>

              <p style="color:#555555; font-size:15px; line-height:1.5;">
                If you did not authorize this transaction, please contact our support team immediately.
              </p>

              <p style="color:#999999; font-size:13px; margin-top:25px; text-align:center;">
                Thank you for using {String.COMPANY_NAME}. Your security is our top priority.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
              {String.COMPANY_NAME} | {String.COMPANY_ADDRESS} | {String.COMPANY_CONTACT}<br>
              &copy; {String.COMPANY_NAME} {2026}
            </td>
          </tr>

        </table>
      </body>
    </html>
    """

    @staticmethod
    def general_notification_template(name: str, title: str, message: str, button_text: str = None, button_link: str = None):
      button_html = f'''
    <div style="text-align:center; margin:25px 0;">
      <a href="{button_link}" style="display:inline-block; background-color:#1E88E5; color:#ffffff; text-decoration:none; padding:14px 28px; border-radius:6px; font-size:16px; font-weight:bold;">{button_text}</a>
    </div>
    ''' if button_link else ""

      return f"""
<html>
  <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
    <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
      
      <!-- Header -->
      <tr>
        <td style="background-color:#1E88E5; padding:25px; text-align:center;">
          <img src="{String.COMPANY_LOGO}" alt="{String.COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
        </td>
      </tr>

      <!-- Body -->
      <tr>
        <td style="padding:35px; text-align:center;">
          <h2 style="color:#333333; margin-bottom:15px;">Hello, {name}</h2>
          <h3 style="color:#333333; font-size:20px; margin-bottom:20px;">{title}</h3>
          <p style="color:#555555; font-size:16px; line-height:1.5;">{message}</p>
          {button_html}
          <p style="color:#999999; font-size:13px; margin-top:25px;">
            This is an automated notification from {String.COMPANY_NAME}. Please do not reply directly to this email.
          </p>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
          {String.COMPANY_NAME} | {String.COMPANY_ADDRESS} | {String.COMPANY_CONTACT}<br>
          &copy; {String.COMPANY_NAME} {2026}
        </td>
      </tr>

    </table>
  </body>
</html>
"""

