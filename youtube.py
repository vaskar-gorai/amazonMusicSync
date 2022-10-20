#!/usr/bin/env python3
import os, json

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

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
    def fromAuthFile(cls, authFile = 'client-secret.json'):
        flow = InstalledAppFlow.from_client_secrets_file(authFile, cls.SCOPES);
        credentials = flow.run_console();
        YouTube.client = build(cls.API_SERVICE_NAME, cls.API_VERSION, credentials = credentials)
        return YouTube();

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
