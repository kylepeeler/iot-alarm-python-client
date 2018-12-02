#!/usr/bin/env python
from MatrixBase import MatrixBase
from rgbmatrix import graphics
from pymongo import MongoClient
import pyowm
import time
import datetime
import os
import urllib
import pymongo
import pprint
import sched

client = MongoClient()
db = client.iotAlarmClock

owm = pyowm.OWM('412a6516f506201b00a7bc576cdd287a')
weatherCity = 'Dubai'
currentWeather = owm.weather_at_place(weatherCity).get_weather()
weatherStatus = currentWeather.get_status()
weatherTemp = int(currentWeather.get_temperature('fahrenheit')['temp'])
weatherIconCode = currentWeather.get_weather_icon_name()
weatherString = "Temp: " + str(weatherTemp) + "F " + weatherStatus.lower() + " in " + weatherCity

class Database():
      def __init__(self, *args, **kwargs):
          client = MongoClient()
          self.db = client.iotAlarmClock
          self.updateDB()
      
      def updateDB(self):
        self.text_record = self.db.texts.find_one({"context": "text"})
        self.weather_record = self.db.weathers.find_one({"context": "weather"})
        self.nextalarm_record = self.db.nextalarms.find_one({"context": "nextalarm"})
        self.date_record = self.db.dates.find_one({"context": "date"})
        self.time_record = self.db.times.find_one({"context": "time"})
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
        pprint.pprint("Refreshed db values...")

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

    def scroll(self, secInd, length):
        if (secInd >= 0 and secInd <= 3 and length > 32):
            scrollPos = getattr(self, "scrollPos" + str(secInd))
            setattr(self, "scrollPos" + str(secInd), scrollPos - 1) 
            if (scrollPos - 1 + length < 0):
               setattr(self, "scrollPos" + str(secInd), 32)
        elif (secInd >= 0 and secInd <= 3 and length <= 32):
            setattr(self, "scrollPos" + str(secInd), 0)

    def checkWeather(self):
        pprint.pprint("Update weather here")

    def drawScreen(self):
        canvas = self.matrix.CreateFrameCanvas()
        canvas.Clear()
        self.displayClock(canvas, graphics.Color(self.alarmDB.time_red, self.alarmDB.time_green, self.alarmDB.time_blue), self.alarmDB.time_record["position"])
        self.displayWeather(canvas, graphics.Color(self.alarmDB.weather_red, self.alarmDB.weather_green, self.alarmDB.weather_blue), self.alarmDB.weather_record["position"])
        self.displayText(canvas, self.alarmDB.text_record["text"], graphics.Color(self.alarmDB.text_red, self.alarmDB.text_green, self.alarmDB.text_blue), 3, self.alarmDB.text_record["position"])
        self.displayDate(canvas, graphics.Color(self.alarmDB.date_red, self.alarmDB.date_green, self.alarmDB.date_blue), self.alarmDB.date_record["position"])
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

    def displayWeather(self, canvas, color, secInd):
        self.displayText(canvas, weatherString, color, 0, secInd)
            
    def displayClock(self, canvas, color, secInd):
        self.displayText(canvas, self.time.strftime("%I:%M%p"), color, 2, secInd)

    def run(self):
        self.alarmDB.updateDB();
        updateDbValues = 10 #How many seconds between calls
        updateWeather = 30
        updateDisplay = 0.05

        tdb = time.time() #db initial timer
        tw = time.time() #weather timer
        tdisp = time.time() #display initial timer

        while True:
            self.time = datetime.datetime.now()
            t1 = time.time()
            if t1 - tw >= updateWeather:
                self.checkWeather()
                tw = time.time()

            if t1 - tdb >= updateDbValues:
                self.alarmDB.updateDB()
                tdb = time.time()

            if t1 - tdisp >= updateDisplay:
                self.drawScreen()
                tdisp = time.time()
                    

# Main function
if __name__ == "__main__":
    run_screen = RunScreen()
    # if (not run_screen.process()):
    #     run_screen.print_help()
