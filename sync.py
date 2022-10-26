#!/usr/bin/env python3

from amazonMusic import *
from database import *
import passwords
from youtube import *
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

def getMappingsFromDB(dbName, tableName):
    con = createConnection(dbName);
    mapping = dict(searchRows('*', 'amazonSongId LIKE "%%"', tableName, con))
    closeConnection(con)
    return mapping

def writeMappingToDB(mapping, dbName, tableName):
    con = createConnection(dbName)
    for item in mapping:
        insertRowInTable((item, mapping[item]), tableName, con)
    closeConnection(con)

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
            playlistItemId = youtube.getPlaylistItemId(songs[songId], playlistId);
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
    print('Starting sync')
    os.chdir('/home/vaskar/Documents')
    parser = argparse.ArgumentParser(description = 'Process arguments');
    parser.add_argument('--email', help='Amazon email', default='vasgorai09@gmail.com');
    parser.add_argument('--token', help='Token for authenticating with google', default='token.json');
    parser.add_argument('--auth', help='Auth File for authentication');
    parser.add_argument('--playlist', help='amazon music playlist to be synced', default = '');
    parser.add_argument('--db', help='Database Name', default = 'songs.db');
    args = parser.parse_args(sys.argv[1:]);

    amazon = AmazonMusic();
    password = passwords.AMAZON_MUSIC_PASSWORD
    amazon.login(args.email, password);
    if not args.playlist:
        youtubePlaylist = 'amazon music'
        tableName = 'saved_songs'
    else:
        tableName = amazon.searchForPlaylist(args.playlist).split('/')[-1]
        youtubePlaylist = args.playlist + '_amazon'

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
        playlistId = youtube.getPlaylist(youtubePlaylist)
        if playlistId == None:
            message = 'This playlist is maintained by a automated program. Please don\'t change the contents manually';
            playlistId = youtube.insertPlaylist(youtubePlaylist, message);
    except Exception as e:
        amazon.closeDriver();
        sys.stderr.write(str(e)+'\n');
        exit(1);

    amazonSongsSet = getSongsFromAmazon(amazon, args.playlist)
    print(f'found {len(amazonSongsSet)} songs')
    mapping = getMappingsFromDB(args.db, tableName);
    addition, deletion = getAdditionAndDeletion(amazonSongsSet, mapping)

    added, errorCode = addSongsToYoutubePlaylist(youtube, playlistId, addition);
    if len(added) > 0:
        sys.stdout.write(f'Added {len(added)} songs\n')
    mapping.update(added);
    if errorCode != 0:
        writeMappingToDB(mapping, args.db, tableName)
        amazon.closeDriver();
        exit(errorCode);

    deleted, errorCode = deleteSongsFromYoutubePlaylist(youtube, playlistId, deletion);
    if len(deleted) > 0:
        sys.stdout.write(f'Deleted {len(deleted)} songs\n')
    for songId in deleted:
        mapping.pop(songId)
    writeMappingToDB(mapping, args.db, tableName)
    amazon.closeDriver();
    exit(errorCode);


if __name__ == "__main__":
    main();
