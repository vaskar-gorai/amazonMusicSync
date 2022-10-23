#!/usr/bin/env python3

from amazonMusic import *
from youtube import *
import keyring;
import argparse;
import sys;

def getSongsFromAmazon(email, password):
    amazonMusic = AmazonMusic();
    amazonMusic.login(email, password);
    songsSet = amazonMusic.getAllSavedSongs();
    amazonMusic.closeDriver();
    return songsSet;

def getMappingsFromFile(fileName):
    mapping = {};
    try:
        with open(fileName, 'r') as f:
            mapping = json.load(f);
    except IOError:
        pass
    finally:
        return mapping;

def writeMapppingsToFile(fileName, mapping):
    try:
        with open(fileName, 'w') as f:
            f.write(json.dumps(mapping));
            f.flush();
            f.close();
    except IOError:
        print('write failed');

def main():
    parser = argparse.ArgumentParser(description = 'Process arguments');
    parser.add_argument('--email', help='Amazon email(default vasgorai09@gmail.com)', default='vasgorai09@gmail.com');
    parser.add_argument('--auth', help='client auth secret file for login to youtube api', default='client-secret.json');
    parser.add_argument('--json', help='json file with mapping from amazon song to youtube video', default='amazon-to-youtube.json');
    parser.add_argument('--playlist', help='youtube playlist to be updated', default='amazon music test');
    args = parser.parse_args(sys.argv[1:]);
    password = keyring.get_password('AMAZON_MUSIC_APP', args.email)
    songsSet = getSongsFromAmazon(args.email, password);
    mapping = getMappingsFromFile(args.json);

    try:
        youtube = YouTube.fromAuthFile(args.auth);
        playlistId = youtube.getPlaylist(args.playlist);
        if playlistId == None:
            playlistId = youtube.insertPlaylist(args.playlist);
    except YouTubeError as e:
        print(e);
        exit(1);


    for song in songsSet:
        if song.id in mapping:
            continue;
        try:
            videoId = youtube.searchForVideo(song.name + ' by ' + song.artist)[0];
            youtube.insertVideoInPlaylist(videoId, playlistId);
            mapping[song.id] = videoId;
        except YouTubeError as e:
            print(e);
            break;
        except:
            print('Something really bad happened! Writing file...');
            break;

    writeMapppingsToFile(args.json, mapping);


if __name__ == "__main__":
    main();

