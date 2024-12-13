import atexit

import rpi_hardware_pwm import HardwarePWM
import RPi.GPIO as GPIO
class LightController:

    def __init__(self):
        # GPIO pin settings
        GPIO.setmode(GPIO.BCM)
        #white
        pwm1 = HardwarePWM(pwm_chennel=0, hz=60, chip=0)
        #UV
        pwm2 = HardwarePWM(pwm=channel=1, hz=60, chip=0)
        #inversed so off = duty cycle of 100
        pwm1.start(100)
        pwm2.start(100)

        #white(16(left), 20(right)) UV(19(left), 26(right))
        self.lstHighPins = [16, 19, 20, 26]
        GPIO.setup(self.lstHighPins, GPIO.OUT)
        atexit.register(GPIO.cleanup) # ensure cleanup in most cases

    #turn the White lights off        
    def WhitelightsOff(self):
        GPIO.output(16, GPIO.LOW)
        GPIO.output(19, GPIO.LOW)

    #turn the White lights on        
    def WhitelightsOn(self):
        pwm1.change_duty_cycle(50)
        GPIO.output(16, GPIO.HIGH)
        GPIO.output(19, GPIO.HIGH)


    #turn the UV lights off        
    def UVlightsOff(self):
        GPIO.output(20, GPIO.LOW)
        GPIO.output(26, GPIO.LOW)

    #turn the UV lights on        
    def UVlightsOn(self):
        pwm2.change_duty_cycle(50)
        GPIO.output(20, GPIO.HIGH)
        GPIO.output(26, GPIO.HIGH)
    
if __name__ == "__main__":
    
    import time
    
    pController = LightController()
    
    pController.lightsOn()
    
    time.sleep(3)
    
    pController.lightsOff()
    