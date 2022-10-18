#!/usr/bin/env python3
import sys, getpass, time;
try:
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import *
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("selenium not found!")
    exit(1);

class atleast_n_elements_are_loaded:
    def __init__(self, locator, n):
        self.locator = locator;
        self.least_number = n;

    def __call__(self, driver):
        if len(driver.find_elements(*self.locator)) < self.least_number :
            return False;
        return True;

class AmazonMusic:
    amazonMusicUrl='https://music.amazon.in/';
    signInPath='forceSignIn';
    HTML_EMAIL_ID='ap_email'
    HTML_PASSWORD_ID='ap_password'
    HTML_MFA_OTP_SUBMIT_BTN='auth-signin-button'
    HTML_MFA_OTP_ID='auth-mfa-otpcode'
    HTML_AMAZON_SIGNIN_BTN='signInSubmit'
    songsPath='my/songs'
    AMAZON_EMAIL='vasgorai09@gmail.com';
    HTML_MUSIC_DIV='music-image-row'
    HTML_ATTRIBUTE_FOR_SONG_NAME='primary-text'
    PERCENTAGE_TO_BE_LOADED=0.9

    def __init__(self):
        try:
            options = Options();
            #options.add_argument('--headless');
            self.driver = webdriver.Firefox(options=options);
            self.loadUrl(self.amazonMusicUrl + self.signInPath);
        except:
            sys.stderr.write("Firefox not initialized!");
            exit(1);

    def login(self, password):
        try:
            self.findElementByIdAndSendKeys(self.HTML_EMAIL_ID, self.AMAZON_EMAIL);
            self.findElementByIdAndSendKeys(self.HTML_PASSWORD_ID, password);
            self.findAndClickButton(self.HTML_AMAZON_SIGNIN_BTN);
            if self.checkForErrorAlert():
                sys.stderr.write('The password entered is wrong\n');
            self.handle2FA();
        except Exception as e:
            print(e);
            self.cleanupDriverAndExit();

    def handle2FA(self):
        while True:
            otp = self.getValidOTPOrQuit();
            self.findElementByIdAndSendKeys(self.HTML_MFA_OTP_ID, otp);
            self.findAndClickButton(self.HTML_MFA_OTP_SUBMIT_BTN);
            if self.checkForErrorAlert():
                sys.stderr.write('The OTP you entered is invalid!\n');
            else:
                break;

    def getAllSavedSongs(self):
        songsSet = set();
        self.loadUrl(self.amazonMusicUrl + self.songsPath);
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, self.HTML_MUSIC_DIV))
        );
        html = self.driver.find_element(By.TAG_NAME, 'html');
        while True:
            gotUnReferencedError = False;
            songsDivs = self.driver.find_elements(By.TAG_NAME, self.HTML_MUSIC_DIV);
            num_elements = len(songsDivs)*self.PERCENTAGE_TO_BE_LOADED;
            for songDiv in songsDivs:
                try:
                    songName = songDiv.get_attribute(self.HTML_ATTRIBUTE_FOR_SONG_NAME);
                    songsSet.add(songName);
                except:
                    gotUnReferencedError = True;
            html.send_keys(Keys.PAGE_DOWN);
            try:
                WebDriverWait(self.driver, 5).until(
                    atleast_n_elements_are_loaded((By.TAG_NAME, self.HTML_MUSIC_DIV), num_elements)
                );
            except TimeoutException:
                return songsSet;

    def findElementByIdAndSendKeys(self, elementId, keys):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, elementId))
            ).send_keys(keys);
        except NoSuchElementException:
            sys.stderr.write(f"no element found with {elementId}\n");
            self.cleanupDriverAndExit();
        except WebDriverException:
            self.cleanupDriverAndExit();

    def findAndClickButton(self, buttonId):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, buttonId))
            ).click();
        except NoSuchElementException:
            sys.stderr.write(f"no element found with {elementId}\n");
            self.cleanupDriverAndExit();
        except WebDriverException:
            self.cleanupDriverAndExit();

    def checkForErrorAlert(self):
        try:
            error = self.driver.find_element(By.ID, 'auth-error-message-box');
        except NoSuchElementException:
            return 0;
        except WebDriverException:
            self.cleanupDriverAndExit();
        return 1;

    def loadUrl(self, url):
        try:
            self.driver.get(url);
        except WebDriverException:
            sys.stderr.write(f"{url} not found\n");
            self.cleanupDriverAndExit(self.driver);

    def cleanupDriverAndExit(self):
        self.closeDriver(self.driver);
        exit();

    def closeDriver(self):
        try:
            self.driver.close();
        except:
            pass

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
