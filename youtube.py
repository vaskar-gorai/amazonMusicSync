#!/usr/bin/env python3
import os, json
import requests;
import oauthlib.oauth2
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build

class YouTubeError(Exception):
    def __init__(self, message = ''):
        self.message = message;

    def __str__(self):
        return self.message;

class YouTube:
    SCOPES = ['https://www.googleapis.com/auth/youtube']
    API_SERVICE_NAME = 'youtube';
    API_VERSION = 'v3';
    client = None;

    @classmethod
    def fromToken(cls, token):
        try:
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(token);
            if not credentials.valid or credentials.expired:
                credentials = YouTube.refreshCredentials(credentials);
            if not credentials.valid:
                sys.stderr.write('Failed to get valid credentials\n');
            YouTube.client = build(cls.API_SERVICE_NAME, cls.API_VERSION, credentials = credentials)
        except FileNotFoundError:
            raise YouTubeError(f'file {token} not found');
        except oauthlib.oauth2.rfc6749.errors.InvalidClientError:
            raise YouTubeError('Invalid secert client code');
        return YouTube();

    @classmethod
    def refreshCredentials(cls, credentials):
        authUrl = credentials.token_uri;
        body = dict(
            client_id = credentials.client_id,
            client_secret = credentials.client_secret,
            refresh_token = credentials.refresh_token,
            grant_type = 'refresh_token'
        );

        try:
            response = requests.post(authUrl, data = body, timeout = 10);
            response.raise_for_status();
            inJson = response.json();
            credentials = google.oauth2.credentials.Credentials(
                inJson['access_token'],
                scopes = credentials.scopes
            );
        except requests.exceptions.ConnectionError:
            sys.stderr.write('Failed to refresh token\n');
        except requests.exceptions.Timeout:
            sys.stderr.write('Request timed out\n');
        except requests.exceptions.HTTPError:
            sys.stderr.write('Bad response received\n');
        return credentials;

    def getPlaylist(self, playlistTitle):
        request = YouTube.client.playlists().list(
            part="snippet",
            maxResults=15,
            mine=True
        );

        try:
            response = request.execute();
        except Exception as e:
            error = json.loads(e.content.decode('UTF-8'));
            raise YouTubeError(error['error']['message']);

        for item in response['items']:
            if item['snippet']['title'] == playlistTitle:
                return item['id'];
        return None;

    def insertPlaylist(self, playlistTitle, description = ''):

        requestBody = dict(
            snippet = dict(
                title = playlistTitle,
                description = description
            ),
            status = dict(
                privacyStatus = 'private'
            )
        );
        request = YouTube.client.playlists().insert(
            part = 'snippet,status',
            body = requestBody
        );

        try:
            response = request.execute();
            return response['id'];
        except Exception as e:
            error = json.loads(e.content.decode('UTF-8'));
            raise YouTubeError(error['error']['message']);

    def searchForVideo(self, title):
        request = YouTube.client.search().list(
            part = 'id',
            q = title,
            maxResults = 25,
            safeSearch = 'none',
            type = 'video'
        );

        try:
            response = request.execute();
            return list(map(lambda a: a['id']['videoId'], response['items']));
        except Exception as e:
            error = json.loads(e.content.decode('UTF-8'));
            raise YouTubeError(error['error']['message']);


    def getVideoIDsInPlaylist(self, playlistId):
        request = YouTube.client.playlistItems().list(
            part = 'snippet',
            playlistId = playlistId
        );

        try:
            response = request.execute();
            return list(map(lambda a: a['id'], response['items']))
        except Exception as e:
            error = json.loads(e.content.decode('UTF-8'));
            raise YouTubeError(error['error']['message']);

    def insertVideoInPlaylist(self, videoId, playlistId):
        requestBody = dict(
            snippet = dict(
                playlistId = playlistId,
                resourceId = dict(
                    kind = 'youtube#video',
                    videoId = videoId
                )
            )
        );
        request = YouTube.client.playlistItems().insert(
            part = 'snippet',
            body = requestBody
        );

        try:
            response = request.execute();
        except Exception as e:
            error = json.loads(e.content.decode('UTF-8'));
            raise YouTubeError(error['error']['message']);
