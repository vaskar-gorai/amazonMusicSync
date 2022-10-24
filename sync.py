#!/usr/bin/env python3

from amazonMusic import *
from youtube import *
import keyring;
import argparse;
import sys;

def getSongsFromAmazon(client, playlist):
    if playlist:
        songsSet = client.getSongsFromPlaylist(playlist);
    else:
        songsSet = client.getAllSavedSongs();
    return songsSet;

def getAdditionAndDeletion(songs, mapping):
    reverseMapping = {}
    for song in songs:
        reverseMapping[song.id] = song

    addition = set(filter(lambda song: song.id not in mapping, songs))
    deletion = {}
    for songId in filter(lambda songId: songId not in reverseMapping, mapping):
        deletion[songId] = mapping[songId]

    return addition, deletion;

def getMappingsFromFile(fileName):
    mapping = {};
    try:
        with open(fileName, 'r') as f:
            mapping = json.load(f);
    except IOError:
        pass
    finally:
        return mapping;

def writeMappingsToFile(fileName, mapping):
    try:
        with open(fileName, 'w') as f:
            f.write(json.dumps(mapping));
            f.flush();
    except IOError:
        sys.stderr.write('write failed\n');

def addSongsToYoutubePlaylist(youtube, playlistId, songs):
    mapping = {}
    for song in songs:
        try:
            videoId = youtube.searchForVideo(song.name + ' by ' + song.artist)[0];
            youtube.insertVideoInPlaylist(videoId, playlistId);
            mapping[song.id] = videoId;
        except YouTubeError as e:
            if e.errorDetail == 'quotaExceeded':
                return (mapping, 1);
        except Exception as e:
            sys.stderr.write(str(e)+'\n');
            return (mapping, 1);
    return (mapping, 0);

def deleteSongsFromYoutubePlaylist(youtube, playlistId, songs):
    deleted = [];
    for songId in songs:
        try:
            playlistItemId = youtube.getPlaylistItemId(mapping[songId], playlistId);
            youtube.deleteVideoInPlaylist(playlistItemId);
            deleted.append(songId);
        except YouTubeError as e:
            if e.errorDetail == 'quotaExceeded':
                return (deleted, 1)
        except Exception as e:
            sys.stderr.write(str(e)+'\n');
            return (deleted, 1)

    return (deleted, 0)

def main():
    APP_NAME = 'AMAZON_MUSIC_APP'
    parser = argparse.ArgumentParser(description = 'Process arguments');
    parser.add_argument('--email', help='Amazon email', default='vasgorai09@gmail.com');
    parser.add_argument('--token', help='Token for authenticating with google');
    parser.add_argument('--auth', help='Auth File for authentication');
    parser.add_argument('--playlist', help='amazon music playlist to be synced', default = '');
    args = parser.parse_args(sys.argv[1:]);

    amazon = AmazonMusic();
    password = keyring.get_password(APP_NAME, args.email)
    playlistId = keyring.get_password(APP_NAME, args.playlist)
    amazon.login(args.email, password);
    if not args.playlist:
        youtubePlaylist = 'amazon music'
        jsonFile = '.songs.json'
    else:
        youtubePlaylist = args.playlist + '_amazon'
        jsonFile = '.' + args.playlist + '.json'

    try:
        assert (not args.playlist or amazon.searchForPlaylist(args.playlist)), "Playlist not found"
        assert (args.token or args.auth), 'Must provide auth or token'
    except Exception as e:
        amazon.closeDriver();
        sys.stderr.write(str(e)+'\n');
        exit(1);

    try:
        if args.token:
            youtube = YouTube.fromToken(args.token);
        else:
            youtube = YouTube.fromAuthFile(args.auth);
        if playlistId == None:
            message = 'This playlist is maintained by a automated program. Please don\'t change the contents manually';
            playlistId = youtube.insertPlaylist(youtubePlaylist, message);
            keyring.set_password(APP_NAME, str(args.playlist), str(playlistId))
    except Exception as e:
        amazon.closeDriver();
        sys.stderr.write(str(e)+'\n');
        exit(1);

    amazonSongsSet = getSongsFromAmazon(amazon, args.playlist)
    mapping = getMappingsFromFile(jsonFile);
    addition, deletion = getAdditionAndDeletion(amazonSongsSet, mapping)

    mapped, errorCode = addSongsToYoutubePlaylist(youtube, playlistId, addition);
    mapping.update(mapped);
    if errorCode != 0:
        writeMappingsToFile(jsonFile, mapping);
        amazon.closeDriver();
        exit(errorCode);

    deleted, errorCode = deleteSongsFromYoutubePlaylist(youtube, playlistId, deletion);
    for songId in deleted:
        mapping.pop(songId)
    writeMappingsToFile(jsonFile, mapping);
    amazon.closeDriver();
    exit(errorCode);


if __name__ == "__main__":
    main();
