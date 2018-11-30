#!/usr/bin/env python
# Display a runtext with double-buffering.
from samplebase import SampleBase
from rgbmatrix import graphics
import pyowm
import time
import datetime
import os
import urllib
        
owm = pyowm.OWM('412a6516f506201b00a7bc576cdd287a')
weatherCity = 'Dubai'
currentWeather = owm.weather_at_place(weatherCity).get_weather()
weatherStatus = currentWeather.get_status()
weatherTemp = int(currentWeather.get_temperature('fahrenheit')['temp'])
weatherIconCode = currentWeather.get_weather_icon_name()
weatherString = "Temp: " + str(weatherTemp) + "F " + weatherStatus.lower() + " in " + weatherCity

class RunScreen(SampleBase):
    def __init__(self, *args, **kwargs):
        super(RunScreen, self).__init__(*args, **kwargs)
        self.scrollPos0 = 32
        self.scrollPos1 = 32
        self.scrollPos2 = 32
        self.scrollPos3 = 32
        self.start = datetime.datetime.now()
        self.font = graphics.Font()
        self.font.LoadFont('rpi-rgb-led-matrix/fonts/tom-thumb.bdf')
        self.time = datetime.datetime.now()

    def scroll(self, secInd, length):
        if (secInd >= 0 and secInd <= 3 and length > 32):
            scrollPos = getattr(self, "scrollPos" + str(secInd));
            setattr(self, "scrollPos" + str(secInd), scrollPos - 1); 
            if (scrollPos - 1 + length < 0):
               setattr(self, "scrollPos" + str(secInd), 32);
        elif (secInd >= 0 and secInd <= 3 and length <= 32):
            setattr(self, "scrollPos" + str(secInd), 0)
    
    def getSectionHeight(self, sectionIndex):
        if (sectionIndex == 0):
            return 9;
        elif (sectionIndex == 1):
            return 16;
        elif (sectionIndex == 2):
            return 23;
        elif (sectionIndex == 3):
            return 30;
        else:
            return 32;
    
    def displayText(self, canvas, text, color, xOffset, secInd):
        if (secInd >= 0 and secInd <= 3):
            height = self.getSectionHeight(secInd)
            self.scroll(secInd, graphics.DrawText(canvas, self.font, xOffset + getattr(self, "scrollPos" + str(secInd)), height, color, text))
    
    def displayDate(self, canvas, color, secInd):
        self.displayText(canvas, self.time.strftime("%x"), color, 0, secInd)

    def displayWeather(self, canvas, color, secInd):
        self.displayText(canvas, weatherString, color, 0, secInd);
            
    def displayClock(self, canvas, color, secInd):
        self.displayText(canvas, self.time.strftime("%I:%M%p"), color, 2, secInd);

    def run(self):
        while True:
            canvas = self.matrix.CreateFrameCanvas()
            canvas.Clear()
        
            self.displayClock(canvas, graphics.Color(255, 165, 0), 0)
            self.displayWeather(canvas, graphics.Color(0, 255, 0), 1)
            self.displayText(canvas, "Example text", graphics.Color(0, 255, 255), 3, 2)
            self.displayDate(canvas, graphics.Color(255, 0, 0), 3)

            time.sleep(0.05)
            canvas = self.matrix.SwapOnVSync(canvas)
            

# Main function
if __name__ == "__main__":
    run_screen = RunScreen()
    if (not run_screen.process()):
        run_screen.print_help()
