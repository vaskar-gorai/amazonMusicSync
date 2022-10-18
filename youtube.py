import argparse
import os

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

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
            print(e.resp, e.content);
            exit(1);

        for item in response['items']:
            if item['snippet']['title'] == playlistTitle:
                return item['id'];

        description = f"{playlistTitle} synced from amazon music";
        return self.insertPlaylist(playlistTitle, description);

    def insertPlaylist(self, playlistTitle, description):

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
            print(e.resp);
            print(e.content);
            exit(1);

    def getVideoIDsInPlaylist(self, playlistId):
        request = YouTube.client.playlistItems().list(
            part = 'snippet',
            playlistId = playlistId
        );

        try:
            response = request.execute();
            return list(map(lambda a: a['id'], response['items']))
        except Exception as e:
            print(e.resp, e.content);
            exit(1);

    def insertVideoInPlaylist(self, videoId, playlistId):
        requestBody = dict(
            snippet = dict(
                playlistId = playlistId,
                resourceId = dict(
                    videoId = videoId
                )
            )
        );
        request = YouTube.client.playlistItems.insert(
            part = 'snippet',
            body = requestBody
        );

        try:
            response = request.execute();
        except Exception as e:
            print(e.resp, e.content);
            exit(1);


if __name__ == '__main__':
    youtube = YouTube.fromAuthFile();
    print(youtube.getSongsInPlaylist(youtube.getPlaylist('sciency stuff')));
