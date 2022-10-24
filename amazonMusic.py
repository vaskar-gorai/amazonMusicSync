#!/usr/bin/env python3
import sys, getpass, time;
from collections import namedtuple
import subprocess, os;
import PIL;
from PIL import Image;
import urllib.request, urllib.error;
try:
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import *
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    sys.stderr.write("selenium not found!\n")
    exit(1);

class new_element_is_found:
    def __init__(self, locator, n):
        self.locator = locator;
        self.least_number = n;

    def __call__(self, driver):
        if driver.find_elements(*self.locator)[-1] == self.least_number :
            return False;
        return True;

Song = namedtuple('Song', ['id', 'name', 'artist']);

class AmazonMusic:
    amazonMusicUrl='https://music.amazon.in';
    signInPath='/forceSignIn';
    songsPath='/my/songs'
    playlistPath='/my/playlists';

    def __init__(self):
        try:
            options = Options();
            # options.add_argument('--headless');
            self.driver = webdriver.Firefox(options=options);
        except:
            sys.stderr.write("Firefox not initialized!\n");
            exit(1);

    def login(self, userName, password):
        try:
            self.loadUrl(self.amazonMusicUrl + self.signInPath);
            captcha = '';
            while True:
                EMAIL_ID = 'ap_email';
                PASSWORD_ID = 'ap_password'
                HTML_AMAZON_SIGNIN_BTN='signInSubmit'
                HTML_CAPTCHA_ID='auth-captcha-guess';
                self.findElementByIdAndSendKeys(EMAIL_ID, [Keys.CONTROL + 'a', Keys.DELETE]);
                self.findElementByIdAndSendKeys(EMAIL_ID, userName);
                if self.checkForWarningAlert():
                    self.findElementByIdAndSendKeys(HTML_CAPTCHA_ID, captcha);
                self.findElementByIdAndSendKeys(PASSWORD_ID, password);
                self.findAndClickButton(HTML_AMAZON_SIGNIN_BTN);
                if self.checkForWarningAlert() or self.checkForErrorAlert():
                    if self.checkForWarningAlert():
                        captcha = self.getCaptcha();
                    password = getpass.getpass('Enter amazon password');
                    continue;
                break;
            self.handle2FA();
        except Exception as e:
            sys.stderr.write(e+'\n');
            self.cleanupDriverAndExit();
        return 0;

    def getCaptcha(self):
        HTML_CAPTCHA_IMG_ID='auth-captcha-image';
        captchaDiv = self.findElementById(HTML_CAPTCHA_IMG_ID);
        imgSrcUrl = self.getAttribute(captchaDiv, 'src');
        return self.showImageFromUrlAndGetCaptcha(imgSrcUrl);

    def handle2FA(self):
        if 'Two-Step Verification' != self.driver.title:
            return;
        tries = 0;
        HTML_MFA_OTP_SUBMIT_BTN = 'auth-signin-button';
        HTML_MFA_OTP_ID='auth-mfa-otpcode'
        while True:
            if tries > 2:
                self.cleanupDriverAndExit();
            otp = self.getValidOTPOrQuit();
            self.findElementByIdAndSendKeys(HTML_MFA_OTP_ID, otp);
            self.findAndClickButton(HTML_MFA_OTP_SUBMIT_BTN);
            tries += 1;
            if self.checkForErrorAlert():
                sys.stderr.write('The OTP you entered is invalid!\n');
            else:
                break;

    def getAllSavedSongs(self, path = ''):
        HTML_MUSIC_DIV='music-image-row'
        PERCENTAGE_TO_BE_LOADED=0.9;
        songsSet = set();
        if not path:
            path = self.songsPath;
        self.loadUrl(self.amazonMusicUrl + path);
        locator = (By.TAG_NAME, HTML_MUSIC_DIV);
        if self.waitFor(EC.presence_of_element_located(locator)):
            return songsSet;
        html = self.driver.find_element(By.TAG_NAME, 'html');
        while True:
            songDivs = self.findElements(locator);
            num_elements = len(songDivs)*PERCENTAGE_TO_BE_LOADED;
            for songDiv in songDivs:
                song = self.getSongAttributes(songDiv);
                if song:
                    songsSet.add(song);
            html.send_keys(Keys.PAGE_DOWN);
            if self.waitFor(new_element_is_found((By.TAG_NAME, HTML_MUSIC_DIV), songDivs[-1])):
                return songsSet;

    def getSongsFromPlaylist(self, playlistName):
        playlistPath = self.searchForPlaylist(playlistName);
        if not playlistPath:
            sys.stderr.write(f'{playlistName} playlist not found\n');
            self.cleanupDriverAndExit();

        return self.getAllSavedSongs(playlistPath);

    def searchForPlaylist(self, playlistName):
        self.loadUrl(self.amazonMusicUrl + self.playlistPath);
        HTML_PLAYLIST_XPATH='//music-vertical-item';
        HTML_ATTRIBUTE_FOR_REF='primary-href';
        HTML_ATTRIBUTE_FOR_NAME='primary-text'
        locator = (By.XPATH, HTML_PLAYLIST_XPATH);
        if self.waitFor(EC.presence_of_element_located(locator)):
            return '';
        playlists = self.findElements(locator);
        for playlist in playlists:
            curName = self.getAttribute(playlist, HTML_ATTRIBUTE_FOR_NAME);
            curName = curName if curName else '';
            if playlistName == curName:
                playlistPath = self.getAttribute(playlist, HTML_ATTRIBUTE_FOR_REF);
                return playlistPath;
        return '';

    def showImageFromUrlAndGetCaptcha(self, url):
        try:
            process = subprocess.run(['mktemp'], capture_output = True);
            if process.returncode != 0:
                fileName = '.amazonCaptchaImage';
            else:
                fileName = process.stdout.decode('UTF-8').strip();
            response = urllib.request.urlopen(url);
            image = Image.open(response);
            image.save(fileName, format = 'jpeg');
            process = subprocess.Popen(['eog', os.path.abspath(fileName)]);
            captcha = input('Enter the characters shown:');
            process.kill();
            process = subprocess.run['rm', fileName];
            return captcha;
        except urllib.error.HTTPError as e:
            sys.stderr.write(f'HTTPError({e.code})' + str(e.reason) + '\n');
        except PIL.UnidentifiedImageError as e:
            sys.stderr.write('Failed to read image:' + str(e) + '\n');
        except subprocess.CalledProcessError as e:
            sys.stderr.write(str(e.cmd) + ' failed\n');
        except Exception as e:
            sys.stderr.write(str(e)+'\n');
        self.cleanupDriverAndExit();

    def getSongAttributes(self, songDiv):
        try:
            HTML_ATTRIBUTE_FOR_ARTIST_NAME='secondary-text-1'
            HTML_ATTRIBUTE_FOR_ALBUM='secondary-text-2'
            HTML_ATTRIBUTE_FOR_NAME='primary-text'
            songName = songDiv.get_attribute(HTML_ATTRIBUTE_FOR_NAME);
            artistName = songDiv.get_attribute(HTML_ATTRIBUTE_FOR_ARTIST_NAME);
            albumName = songDiv.get_attribute(HTML_ATTRIBUTE_FOR_ALBUM);
            songId = songName+artistName+albumName;
        except StaleElementReferenceException:
            return None;
        except NoSuchWindowException:
            self.cleanupDriverAndExit();
        except InvalidSessionIdException:
            self.cleanupDriverAndExit();
        return Song(songId, songName, artistName);

    def waitFor(self, waitCond):
        try:
            WebDriverWait(self.driver, 10).until(
                waitCond
            );
            return 0;
        except TimeoutException:
            return 1;
        except WebDriverException:
            self.cleanupDriverAndExit();

    def getAttribute(self, element, attribute):
        try:
            return element.get_attribute(attribute);
        except WebDriverException:
            self.cleanupDriverAndExit();

    def findElements(self, locator):
        try:
            return self.driver.find_elements(*locator);
        except NoSuchElementException:
            return [];
        except WebDriverException:
            self.cleanupDriverAndExit();

    def findElementById(self, elementId):
        try:
            element = self.driver.find_element(By.ID, elementId);
        except NoSuchElementException:
            return None;
        except WebDriverException:
            self.cleanupDriverAndExit();

        return element;

    def findElementByIdAndSendKeys(self, elementId, keys):
        element =  self.findElementById(elementId);
        if element:
            element.send_keys(keys);

    def findAndClickButton(self, buttonId):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, buttonId))
            ).click();
        except NoSuchElementException:
            sys.stderr.write(f"no element found with {buttonId}\n");
            self.cleanupDriverAndExit();
        except WebDriverException:
            self.cleanupDriverAndExit();

    def checkForErrorAlert(self):
        element = self.findElementById('auth-error-message-box');
        return 1 if element else 0;

    def checkForWarningAlert(self):
        element = self.findElementById('auth-warning-message-box');
        return 1 if element else 0;

    def loadUrl(self, url):
        try:
            self.driver.get(url);
        except WebDriverException:
            sys.stderr.write(f"{url} not found\n");
            self.cleanupDriverAndExit(self.driver);

    def getValidOTPOrQuit(self):
        while True:
            otp = input('Enter 2FA OTP(q to quit):');
            if otp == 'q':
                self.cleanupDriverAndExit();
            try:
                int(otp);
            except ValueError:
                sys.stderr.write('OTP can be an integer only\n');
                continue;
            break;
        return otp;

    def cleanupDriverAndExit(self):
        self.closeDriver();
        exit();

    def closeDriver(self):
        try:
            self.driver.close();
        except:
            pass
