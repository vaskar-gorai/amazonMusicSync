#!/usr/bin/env python3
import os, json
import requests;
import oauthlib.oauth2
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build

class YouTubeError(Exception):
    INVALID_SECRET_CODE = 1;
    FILE_NOT_FOUND = 2;
    INVALID_TOKEN = 3;

    def __init__(self, message = '', errorCode = 1):
        self.message = message;
        self.errorCode = errorCode;

    def __str__(self):
        return self.message;

class YouTube:
    SCOPES = ['https://www.googleapis.com/auth/youtube']
    API_SERVICE_NAME = 'youtube';
    API_VERSION = 'v3';
    client = None;

    @classmethod
    def fromAuthFile(cls, authFile):
        try:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(authFile, cls.SCOPES);
            credentials = flow.run_console();
            YouTube.client = build(cls.API_SERVICE_NAME, cls.API_VERSION, credentials = credentials)
            return YouTube();
        except FileNotFoundError:
            raise YouTubeError(f'file {authFile} not found', YouTubeError.FILE_NOT_FOUND);
        except oauthlib.oauth2.rfc6749.errors.InvalidClientError:
            raise YouTubeError('Invalid secert client code', YouTubeError.INVALID_SECRET_CODE);
        return YouTube();

    @classmethod
    def fromToken(cls, token):
        try:
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(token);
            if not credentials.valid or credentials.expired:
                credentials = YouTube.refreshCredentials(credentials);
            if not credentials.valid or credentials.expired:
                raise YouTubeError('Token invalid! Please generate new token via authFile', YouTubeError.INVALID_TOKEN);
            YouTube.client = build(cls.API_SERVICE_NAME, cls.API_VERSION, credentials = credentials)
        except FileNotFoundError:
            raise YouTubeError(f'file {token} not found', YouTubeError.FILE_NOT_FOUND);
        except oauthlib.oauth2.rfc6749.errors.InvalidClientError:
            raise YouTubeError('Invalid secert client code', YouTubeError.INVALID_SECRET_CODE);
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

    def getResponse(self, request):
        try:
            response = request.execute();
        except Exception as e:
            error = json.loads(e.content.decode('UTF-8'));
            raise YouTubeError(error['error']['message']);
        return response

    def getPlaylist(self, playlistTitle):
        request = YouTube.client.playlists().list(
            part="snippet",
            maxResults=15,
            mine=True
        );

        response = self.getResponse(request);

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
        self.getResponse(request);

    def searchForVideo(self, title):
        request = YouTube.client.search().list(
            part = 'id',
            q = title,
            maxResults = 25,
            safeSearch = 'none',
            type = 'video'
        );

        response = self.getResponse(requeset);
        return list(map(lambda a: a['id']['videoId'], response['items']));


    def getVideoIDsInPlaylist(self, playlistId):
        playlistItems = [];
        requestBody = dict(
            part = 'contentDetails',
            playlistId = playlistId,
            maxResults = 50,
        )
        while True:
            request = YouTube.client.playlistItems().list(**requestBody);
            response = self.getResponse(request)
            playlistItems.extend((map(lambda a: a['contentDetails']['videoId'], response['items'])))

            if 'nextPageToken' in response:
                requestBody['pageToken'] = response['nextPageToken']
            else:
                return playlistItems

    def getPlaylistItemId(self, videoId, playlistId):
        request = YouTube.client.playlistItems().list(
            part = 'id',
            playlistId = playlistId,
            videoId = videoId
        )

        response = self.getResponse(request);
        return response['items'][0]['id'] if len(response['items']) > 0 else '';

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
        self.getResponse(request);

    def deleteVideoInPlaylist(self, playlistItemId):
        request = YouTube.client.playlistItems().delete(
            id = playlistItemId
        );

        self.getResponse(request);
