#!/usr/bin/env python3
import os, json, sys
import requests;
import oauthlib.oauth2
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.errors
from googleapiclient.discovery import build

class YouTubeError(Exception):
    FILE_NOT_FOUND = 'fileNotFound'
    INVALID_SECRET_CODE = 'invalidSecretCode'
    INVALID_TOKEN = 'invalidToken'
    UNKNOWN_ERROR = 'unknownError'
    def __init__(self, errorDetail, message):
        self.errorDetail = errorDetail
        self.message = message

    def __str__(self):
        return str(self.errorDetail) + ':' + str(self.message);

class YouTube:
    SCOPES = ['https://www.googleapis.com/auth/youtube']
    API_SERVICE_NAME = 'youtube';
    API_VERSION = 'v3'

    @classmethod
    def fromAuthFile(cls, authFile):
        try:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(authFile, cls.SCOPES);
            credentials = flow.run_console();
            return YouTube(build(cls.API_SERVICE_NAME, cls.API_VERSION, credentials = credentials))
        except FileNotFoundError:
            raise YouTubeError(YouTubeError.FILE_NOT_FOUND, f'File {authFile} not found');
        except oauthlib.oauth2.rfc6749.errors.InvalidClientError:
            raise YouTubeError(YouTubeError.INVALID_SECRET_CODE, 'Invalid secert client code');
        except Exception as e:
            print(e)
            sys.stderr.write('Failed to create youtube client from authFile\n')

    @classmethod
    def fromToken(cls, token):
        try:
            credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(token);
            if not credentials.valid or credentials.expired:
                credentials = YouTube.refreshCredentials(credentials);
            if not credentials.valid or credentials.expired:
                raise YouTubeError(YouTubeError.INVALID_TOKEN, 'Token invalid! Please generate new token via authFile');
            return YouTube(build(cls.API_SERVICE_NAME, cls.API_VERSION, credentials = credentials))
        except FileNotFoundError:
            raise YouTubeError(YouTubeError.FILE_NOT_FOUND, f'File {token} not found');
        except oauthlib.oauth2.rfc6749.errors.InvalidClientError:
            raise YouTubeError(YouTubeError.INVALID_SECRET_CODE, 'Invalid secert client code');
        except Exception as e:
            print(e)
            sys.stderr.write('Failed to create youtube client from token\n')

    @classmethod
    def refreshCredentials(cls, credentials):
        try:
            authUrl = credentials.token_uri;
            body = dict(
                client_id = credentials.client_id,
                client_secret = credentials.client_secret,
                refresh_token = credentials.refresh_token,
                grant_type = 'refresh_token'
            );
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
        except KeyError:
            sys.stderr.write('Key ' + sys.exc_info()[1][0] + ' not Found\n');
        return credentials;

    def __init__(self, client):
        self.client = client;

    def getResponse(self, request):
        try:
            response = request.execute();
        except googleapiclient.errors.HttpError as e:
            error = json.loads(e.content.decode('UTF-8'));
            raise YouTubeError(error['error']['errors'][0]['reason'], error['error']['message']);
        except Exception as e:
            raise YouTubeError(YouTubeError.UNKNOWN_ERROR, str(e))
        return response

    def getPlaylist(self, playlistTitle):
        request = self.client.playlists().list(
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
        request = self.client.playlists().insert(
            part = 'snippet,status',
            body = requestBody
        );
        self.getResponse(request);

    def searchForVideo(self, title):
        request = self.client.search().list(
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
            request = self.client.playlistItems().list(**requestBody);
            response = self.getResponse(request)
            playlistItems.extend((map(lambda a: a['contentDetails']['videoId'], response['items'])))

            if 'nextPageToken' in response:
                requestBody['pageToken'] = response['nextPageToken']
            else:
                return playlistItems

    def getPlaylistItemId(self, videoId, playlistId):
        request = self.client.playlistItems().list(
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
        request = self.client.playlistItems().insert(
            part = 'snippet',
            body = requestBody
        );
        self.getResponse(request);

    def deleteVideoInPlaylist(self, playlistItemId):
        request = self.client.playlistItems().delete(
            id = playlistItemId
        );

        self.getResponse(request);
