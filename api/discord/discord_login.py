from requests_oauthlib import OAuth2Session
from flask import session, redirect, request
import os
from utils.config import config

# https://www.youtube.com/watch?v=JNSIo90ddkE

# Disable SSL requirement for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class DiscordLogin:
    def __init__(self, client_id, client_secret, redirect_uri, scope=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope or ['identify', 'email']
        self.base_discord_api_url = 'https://discordapp.com/api'
        self.token_url = config["DISCORD_TOKEN_URL"]
        self.authorize_url = config["DISCORD_AUTH_URL"]

    def get_login_url(self):
        oauth = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scope)
        login_url, state = oauth.authorization_url(self.authorize_url)
        session['state'] = state
        return login_url

    def fetch_token(self):
        discord = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            state=session['state'],
            scope=self.scope
        )
        token = discord.fetch_token(
            self.token_url,
            client_secret=self.client_secret,
            authorization_response=request.url
        )
        session['discord_token'] = token
        return token

    def get_user_info(self):
        discord = OAuth2Session(self.client_id, token=session['discord_token'])
        response = discord.get(self.base_discord_api_url + '/users/@me')
        user_info = response.json()
        return {
            'username': user_info['username'],
            'id': user_info['id'],
            'avatar': f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png"
        }
