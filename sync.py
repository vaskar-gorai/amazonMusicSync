#!/usr/bin/env python3

from amazonMusic import *
from youtube import *
import keyring;

def main():
    amazonMusic = AmazonMusic();
    email = 'vasgorai09@gmail.com';
    amazonMusic.login(email, keyring.get_password('AMAZON_MUSIC_APP', email));
    songs = amazonMusic.getAllSavedSongs();
    amazonMusic.closeDriver();
    youtube = YouTube.fromAuthFile();
    playlistId = youtube.getPlaylist('amazon music test');
    if playlistId == None:
        playlistId = youtube.insertPlaylist('amazon music test');

    maxLen = 30;
    i = 0;
    for songName, artistName in songs:
        i = i+1;
        if i > maxLen:
            break;
        videoId = youtube.searchForVideo(songName+artistName)[0];
        youtube.insertVideoInPlaylist(videoId, playlistId);

main();

