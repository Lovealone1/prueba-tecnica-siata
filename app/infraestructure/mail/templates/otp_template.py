def get_otp_email_template(otp: str, intent: str) -> str:
    is_register = intent == 'REGISTER'
    main_title = 'Confirm your email address' if is_register else 'Verify your login attempt'
    description = (
        'Use the code below to verify your email and complete your registration for PT SIATA.'
        if is_register
        else 'Use the code below to verify your identity and complete your login to PT SIATA.'
    )

    # Format the OTP to have spaces between digits for better readability (e.g. "8 5 0 9 7 1")
    formatted_otp = ' '.join(list(str(otp)))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PT SIATA - OTP</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #f4f4f5;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    .wrapper {{
      width: 100%;
      table-layout: fixed;
      background-color: #f4f4f5;
      padding-top: 40px;
      padding-bottom: 40px;
    }}
    .main-container {{
      max-width: 600px;
      margin: 0 auto;
      background-color: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}
    .header {{
      background-color: #3f3f46;
      color: #ffffff;
      text-align: center;
      padding: 32px 20px;
    }}
    .header h1 {{
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.025em;
    }}
    .header p {{
      margin: 8px 0 0 0;
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #a1a1aa;
    }}
    .content {{
      padding: 40px 32px;
      text-align: center;
    }}
    .content h2 {{
      margin: 0 0 16px 0;
      color: #18181b;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.025em;
    }}
    .content p.description {{
      margin: 0 0 40px 0;
      color: #52525b;
      font-size: 15px;
      line-height: 1.6;
    }}
    .code-container {{
      background-color: #fafafa;
      border: 1px solid #e4e4e7;
      border-radius: 12px;
      padding: 32px 10px;
      margin: 0 auto;
    }}
    .code-container .label {{
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #a1a1aa;
      margin: 0 0 12px 0;
    }}
    .code-container .code {{
      font-size: 32px;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: #18181b;
      margin: 0 0 12px 0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }}
    .code-container .expires {{
      font-size: 13px;
      color: #a1a1aa;
      margin: 0;
    }}
    .footer {{
      padding: 0 32px 32px 32px;
      text-align: center;
      color: #a1a1aa;
      font-size: 12px;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="main-container">
      <div class="header">
        <h1>PT SIATA Auth</h1>
        <p>Security OTP</p>
      </div>
      <div class="content">
        <h2>{main_title}</h2>
        <p class="description">{description}</p>
        
        <div class="code-container">
          <p class="label">VERIFICATION CODE</p>
          <p class="code">{formatted_otp}</p>
          <p class="expires">Expires in 1 minute</p>
        </div>
      </div>
      <div class="footer">
        If you didn't request this code, you can safely ignore this email.
      </div>
    </div>
  </div>
</body>
</html>""".strip()
