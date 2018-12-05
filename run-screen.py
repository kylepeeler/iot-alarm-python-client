#!/usr/bin/env python
from MatrixBase import MatrixBase
from rgbmatrix import graphics
from pymongo import MongoClient
import RPi.GPIO as GPIO
import pyowm
import time
import datetime
import os
import urllib
import pymongo
import pprint
import sched
import math
import pygame

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

owm = pyowm.OWM('412a6516f506201b00a7bc576cdd287a')
client = MongoClient()
db = client.iotAlarmClock

pygame.mixer.init(44100, -16,2,2048)
pygame.mixer.music.load('alarm.mp3')

class Alarm():
    def __init__(self, *args, **kwargs):
        self.currentTime = datetime.datetime.now()
        self.enabledAlarms = {} 
        self.alarmActive = False

    def checkAlarmsMatchesTime(self):
        for id, enabledAlarm in self.enabledAlarms.iteritems():
            now = datetime.datetime.now()
            alarmTime = now.replace(hour=enabledAlarm["hour"], minute=enabledAlarm["min"], second=0)
            if (now == alarmTime):
                self.alarmActive = True

    def getNextAlarmTime(self):
        minDiff = 86401
        nextAlarmDate = None
        for id, enabledAlarm in self.enabledAlarms.iteritems():
            now = datetime.datetime.now()
            alarmTime = now.replace(hour=enabledAlarm["hour"], minute=enabledAlarm["min"], second=0)
            if (now < alarmTime):
                if ((alarmTime - now).total_seconds() < minDiff):
                    minDiff = (alarmTime-now).total_seconds()
                    nextAlarmDate = alarmTime
        return nextAlarmDate;

            

class Weather():
    def __init__(self, *args, **kwargs):
        self.weatherString = "Fetching weather..."
        
    def updateWeatherStatus(self, city):
        try:
            self.currentWeather = owm.weather_at_place(city).get_weather()
            weatherStatus = self.currentWeather.get_status()
            weatherTemp = int(self.currentWeather.get_temperature('fahrenheit')['temp'])
            self.weatherString = "Temp: " + str(weatherTemp) + "F " + weatherStatus.lower() + " in " + city
        except:
            self.weatherString = "Failed to load weather"
        print("Updated weather")

class Database():
      def updateDB(self, alarms):
        pprint.pprint("Refreshing MongoDB values...")
        self.text_record = db.texts.find_one({"context": "text"})
        self.weather_record = db.weathers.find_one({"context": "weather"})
        self.nextalarm_record = db.nextalarms.find_one({"context": "nextalarm"})
        self.date_record = db.dates.find_one({"context": "date"})
        self.time_record = db.times.find_one({"context": "time"})
        self.text_red = self.text_record["color"]["r"]
        self.text_green = self.text_record["color"]["g"]
        self.text_blue = self.text_record["color"]["b"]
        self.weather_red = self.weather_record["color"]["r"]
        self.weather_green = self.weather_record["color"]["g"]
        self.weather_blue = self.weather_record["color"]["b"]
        self.nextalarm_red = self.nextalarm_record["color"]["r"]
        self.nextalarm_green = self.nextalarm_record["color"]["g"]
        self.nextalarm_blue = self.nextalarm_record["color"]["b"]
        self.date_red = self.date_record["color"]["r"]
        self.date_green = self.date_record["color"]["g"]
        self.date_blue = self.date_record["color"]["b"]
        self.time_red = self.time_record["color"]["r"]
        self.time_green = self.time_record["color"]["g"]
        self.time_blue = self.time_record["color"]["b"]
        for alarm in db.alarms.find({"enabled": True}):
            #pprint.pprint(alarm)
            if (alarm["days"][datetime.datetime.now().strftime("%A").lower()]):
                alarms[alarm["_id"]] = alarm
        

class RunScreen(MatrixBase):
    def __init__(self, *args, **kwargs):
        super(RunScreen, self).__init__(*args, **kwargs)
        self.scrollPos0 = 32
        self.scrollPos1 = 32
        self.scrollPos2 = 32
        self.scrollPos3 = 32
        self.font = graphics.Font()
        self.font.LoadFont('rpi-rgb-led-matrix/fonts/tom-thumb.bdf')
        self.time = datetime.datetime.now()
        self.alarmDB = Database()
        self.weather = Weather()
        self.alarmInstance = Alarm()
        self.alarmDB.updateDB(self.alarmInstance.enabledAlarms)

    def scroll(self, secInd, length):
        if (secInd >= 0 and secInd <= 3 and length > 32):
            scrollPos = getattr(self, "scrollPos" + str(secInd))
            setattr(self, "scrollPos" + str(secInd), scrollPos - 1) 
            if (scrollPos - 1 + length < 0):
               setattr(self, "scrollPos" + str(secInd), 32)
        elif (secInd >= 0 and secInd <= 3 and length <= 32):
            setattr(self, "scrollPos" + str(secInd), 0)

    def drawScreen(self):
        canvas = self.matrix.CreateFrameCanvas()
        if not (self.alarmInstance.alarmActive):
            canvas.Clear()
            self.displayClock(canvas, graphics.Color(self.alarmDB.time_red, self.alarmDB.time_green, self.alarmDB.time_blue), self.alarmDB.time_record["position"])
            self.displayWeather(canvas, self.weather.weatherString, graphics.Color(self.alarmDB.weather_red, self.alarmDB.weather_green, self.alarmDB.weather_blue), self.alarmDB.weather_record["position"])
            self.displayText(canvas, self.alarmDB.text_record["text"], graphics.Color(self.alarmDB.text_red, self.alarmDB.text_green, self.alarmDB.text_blue), 3, self.alarmDB.text_record["position"])
            self.displayDate(canvas, graphics.Color(self.alarmDB.date_red, self.alarmDB.date_green, self.alarmDB.date_blue), self.alarmDB.date_record["position"])
            self.displayNextAlarmTime(canvas, graphics.Color(self.alarmDB.nextalarm_red, self.alarmDB.nextalarm_green, self.alarmDB.nextalarm_blue), self.alarmDB.nextalarm_record["position"])
        else:
            self.matrix.Fill(255,0,0)
        canvas = self.matrix.SwapOnVSync(canvas)
            
    def getSectionHeight(self, sectionIndex):
        if (sectionIndex == 0):
            return 9
        elif (sectionIndex == 1):
            return 16
        elif (sectionIndex == 2):
            return 23
        elif (sectionIndex == 3):
            return 30
        else:
            return 32
    
    def displayText(self, canvas, text, color, xOffset, secInd):
        if (secInd >= 0 and secInd <= 3):
            height = self.getSectionHeight(secInd)
            self.scroll(secInd, graphics.DrawText(canvas, self.font, xOffset + getattr(self, "scrollPos" + str(secInd)), height, color, text))
    
    def displayDate(self, canvas, color, secInd):
        self.displayText(canvas, self.time.strftime("%x"), color, 0, secInd)

    def displayWeather(self, canvas, weatherString, color, secInd):
        self.displayText(canvas, weatherString, color, 0, secInd)
            
    def displayClock(self, canvas, color, secInd):
        self.displayText(canvas, self.time.strftime("%I:%M%p"), color, 2, secInd)

    def displayNextAlarmTime(self, canvas, color, secInd):
        nextAlarm = self.alarmInstance.getNextAlarmTime()
        if (self.alarmDB.nextalarm_record["displayAsCountdown"] and nextAlarm is not None):
            now = datetime.datetime.now()
            diffInSec = (nextAlarm-now).total_seconds()
            hours = int((diffInSec%(24*3600))/3600)
            minutes = math.ceil(((diffInSec%(24*3600*3600))/60)) - (60*hours)
            self.displayText(canvas, (str(int(hours)) +"h "+str(int(minutes))+"m until next alarm"), color, 0, secInd)
        elif (nextAlarm is None):
            self.displayText(canvas, "No alarms set", color, 0, secInd) 
        else:
            self.displayText(canvas, "Next alarm at " + nextAlarm.strftime("%I:%M%p"), color, 0, secInd) 

    def run(self):
        self.alarmDB.updateDB(self.alarmInstance.enabledAlarms);
        self.weather.updateWeatherStatus(self.alarmDB.weather_record["city"])
        updateDbValues = 10 #How many seconds between calls
        updateWeather = 120
        updateDisplay = 0.04
        updateAlarm = 1

        tac = time.time()
        tdb = time.time() #db initial timer
        tw = time.time() #weather timer
        tdisp = time.time() #display initial timer
        
        print self.alarmInstance.getNextAlarmTime()

        while True:
            self.time = datetime.datetime.now()
            t1 = time.time()
            if t1 - tw >= updateWeather:
                self.weather.updateWeatherStatus(self.alarmDB.weather_record["city"])
                tw = time.time()

            if t1 - tdb >= updateDbValues:
                self.alarmDB.updateDB(self.alarmInstance.enabledAlarms)
                tdb = time.time()

            if t1 - tac >= updateAlarm:
                self.alarmInstance.checkAlarmsMatchesTime()
                tac = time.time()

            if not self.alarmInstance.alarmActive and t1 - tdisp >= updateDisplay:
                self.drawScreen()
                tdisp = time.time()

            if self.alarmInstance.alarmActive and t1 - tdisp >= .2:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
                input_state = GPIO.input(18)
                if input_state == False:
                    pygame.mixer.music.stop()
                    self.alarmInstance.alarmActive = False
                self.drawScreen()
                tdisp = time.time()
                    

# Main function
if __name__ == "__main__":
    run_screen = RunScreen()
    if (not run_screen.process()):
        run_screen.print_help()
