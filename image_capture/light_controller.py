import atexit
import os
from rpi_hardware_pwm import HardwarePWM
import RPi.GPIO as GPIO

class LightandFanController:
    #initializing all settings for hardware pwm on 0
    def __init__(self):
        # GPIO pin settings
        GPIO.setmode(GPIO.BCM)
        #white left
        self.pwm1 = HardwarePWM(pwm_channel=0, hz=25_000, chip=0)
        #white right
        self.pwm2 = HardwarePWM(pwm_channel=1, hz=25_000, chip=0)

        #inversed so off = duty cycle of 100
        self.pwm1.start(100)
        self.pwm2.start(100)

        #UV right (18) left (19) --- Fan (5)
        self.lstHighPins = [18, 19, 5]
        GPIO.setup(self.lstHighPins, GPIO.OUT)
        atexit.register(GPIO.cleanup) # ensure cleanup in most cases
    def fanOff(self):
        GPIO.output(5, GPIO.LOW)

    def fanOn(self):
        GPIO.output(5, GPIO.HIGH)

    #turn the White lights off        
    def WhitelightsOff(self):
        self.pwm1.change_duty_cycle(100)
        self.pwm2.change_duty_cycle(100)

    #turn the White lights on        
    def WhitelightsOn(self, slider):
        dutycycle = 100-slider
        self.pwm1.change_duty_cycle(dutycycle)


    #turn the UV lights off        
    def UVlightsOff(self):
        GPIO.output(18, GPIO.LOW)
        GPIO.output(19, GPIO.LOW)

    #turn the UV lights on        
    def UVlightsOn(self):
        GPIO.output(18, GPIO.HIGH)
        GPIO.output(19, GPIO.HIGH)

    