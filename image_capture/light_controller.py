import atexit

import RPi.GPIO as GPIO

class LightController:

    def __init__(self):
        # GPIO pin settings
        GPIO.setmode(GPIO.BCM)

        #white led panel brightness 75%
        self.nLEDPercent = 75 # must be int

        self.lstPWM = []
        self.lstHighPins = [16, 20, 21, 13, 12, 6]
        GPIO.setup(self.lstHighPins, GPIO.OUT)
        atexit.register(GPIO.cleanup) # ensure cleanup in most cases

        for nI in range(len(self.lstHighPins)):
            self.lstPWM.append(GPIO.PWM(self.lstHighPins[nI], 1000))

    #turn the lights off        
    def lightsOff(self):
        for pin in self.lstPWM: 
            pin.stop()

    #turn the lights on        
    def lightsOn(self):
        for pin in self.lstPWM: 
            pin.start(self.nLEDPercent)

if __name__ == "__main__":
    
    import time
    
    pController = LightController()
    
    pController.lightsOn()
    
    time.sleep(3)
    
    pController.lightsOff()
    