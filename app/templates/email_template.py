COMPANY_LOGO = "https://res.cloudinary.com/dgh76k5vn/image/upload/v1769602666/app_logo_ibnykm.png"
COMPANY_NAME = "PocketPay"
COMPANY_ADDRESS = "Bogura, Bangladesh"
COMPANY_CONTACT  = "poketpay@gmail.com"


class EmailTemplate:
    # Welcome Email
    @staticmethod
    def welcome_email_template(name: str):
        return f"""
    <html>
        <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
            <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
              
                <!-- Header -->
                <tr>
                    <td style="background-color:#1E88E5; padding:25px; text-align:center;">
                        <img src="{COMPANY_LOGO}" alt="{COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
                    </td>
                </tr>

                <!-- Body -->
                <tr>
                    <td style="padding:35px; text-align:center;">
                        <h2 style="color:#333333; margin-bottom:15px;">Welcome, {name}!</h2>
                        
                        <p style="color:#555555; font-size:16px; line-height:1.5;">
                            Thank you for joining <strong>{COMPANY_NAME}</strong>! We're excited to have you on board.
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

                <!-- Footer -->
                <tr>
                  <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
                    {COMPANY_NAME} | {COMPANY_ADDRESS} | {COMPANY_CONTACT}<br>
                    &copy; {COMPANY_NAME} {2026}
                  </td>
                </tr>

            </table>
        </body>
    </html>
    """

    # Otp Email
    @staticmethod
    def otp_template(name: str, otp: str):
        return f"""
    <html>
      <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
        <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
          <!-- Header with Company Logo -->
          <tr>
            <td style="background-color:#1E88E5; padding:25px; text-align:center;">
              <img src="{COMPANY_LOGO}" alt="{COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:35px; text-align:center;">
              <h2 style="color:#333333; margin-bottom:15px;">Welcome, {name}!</h2>
              <p style="color:#555555; font-size:16px; line-height:1.5;">
                You're almost ready to start using <strong>{COMPANY_NAME}</strong>.  
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
                Thank you for choosing {COMPANY_NAME}. Let's get started!
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
              {COMPANY_NAME} | {COMPANY_ADDRESS} | {COMPANY_CONTACT}<br>
              &copy; {COMPANY_NAME} {2026}
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    # Reset Password Email
    @staticmethod
    def reset_password_template(name: str, email: str, reset_link: str):
        return f"""
    <html>
      <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
        <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background-color:#1E88E5; padding:25px; text-align:center;">
              <img src="{COMPANY_LOGO}" alt="{COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
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
                Thank you for using {COMPANY_NAME}. Stay secure!
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
              {COMPANY_NAME} | {COMPANY_ADDRESS} | {COMPANY_CONTACT}<br>
              &copy; {COMPANY_NAME} {2026}
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    # Money Sent Email
    @staticmethod
    def money_sent_template(user_name: str, recipient: str, amount: float, txn_id: str, date: str):
        return f"""
    <html>
      <body style="margin:0; padding:0; font-family:'Helvetica Neue',Arial,sans-serif; background-color:#f5f6fa;">
        <table align="center" width="100%" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:10px; overflow:hidden; box-shadow:0 0 15px rgba(0,0,0,0.1);">
          
          <!-- Header -->
          <tr>
            <td style="background-color:#1E88E5; padding:25px; text-align:center;">
              <img src="{COMPANY_LOGO}" alt="{COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
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
                Thank you for using {COMPANY_NAME}. Your security is our top priority.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
              {COMPANY_NAME} | {COMPANY_ADDRESS} | {COMPANY_CONTACT}<br>
              &copy; {COMPANY_NAME} {2026}
            </td>
          </tr>

        </table>
      </body>
    </html>
    """

    # General Notification Email
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
          <img src="{COMPANY_LOGO}" alt="{COMPANY_NAME} Logo" width="120" style="display:block; margin:auto;">
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
            This is an automated notification from {COMPANY_NAME}. Please do not reply directly to this email.
          </p>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background-color:#f1f2f6; padding:20px; text-align:center; font-size:12px; color:#777777;">
          {COMPANY_NAME} | {COMPANY_ADDRESS} | {COMPANY_CONTACT}<br>
          &copy; {COMPANY_NAME} {2026}
        </td>
      </tr>

    </table>
  </body>
</html>
"""
