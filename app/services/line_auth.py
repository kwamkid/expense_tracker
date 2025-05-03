# app/services/line_auth.py
import requests
from flask import current_app


class LineAuth:
    def __init__(self):
        self.channel_id = current_app.config['LINE_CHANNEL_ID']
        self.channel_secret = current_app.config['LINE_CHANNEL_SECRET']
        self.redirect_uri = current_app.config['LINE_REDIRECT_URI']

        # ตรวจสอบว่ามีการตั้งค่า LINE config หรือไม่
        if not self.channel_id or not self.channel_secret:
            raise ValueError("LINE_CHANNEL_ID and LINE_CHANNEL_SECRET must be set in environment variables")

    def get_login_url(self, state):
        if not self.channel_id:
            raise ValueError("LINE_CHANNEL_ID is not configured")

        return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={self.channel_id}&redirect_uri={self.redirect_uri}&state={state}&scope=profile%20openid"

    def get_access_token(self, code):
        url = "https://api.line.me/oauth2/v2.1/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.channel_id,
            'client_secret': self.channel_secret
        }

        response = requests.post(url, headers=headers, data=data)
        return response.json()

    def get_user_profile(self, access_token):
        url = "https://api.line.me/v2/profile"
        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.get(url, headers=headers)
        return response.json()