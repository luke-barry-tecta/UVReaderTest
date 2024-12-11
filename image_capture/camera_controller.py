import atexit
import os

from PIL import Image

from is_rpi import isRPi

from picamera2 import Picamera2, Preview, Metadata

import time
import numpy as np

class CameraController:

    def __init__(self, strDirectory):        
        self.pTuning = Picamera2.load_tuning_file(os.path.join(strDirectory, "imx477.2.json"))

        # create and configure camera
        self.pCamera = Picamera2(tuning=self.pTuning)

        self.capture_config=self.pCamera.create_still_configuration(raw={})
        self.preview_config=self.pCamera.create_still_configuration({"size": (640, 480)}, raw={})
        
        atexit.register(self.shutdown)
        
    def captureImage(self, fAnalogGain, fRedGain, fBlueGain, nExposureTime_us, bPreview, bUV=False):
        # capture an image. bUV is ignored: it is for the dummy (testing) interface
        
        # start camera
        if bPreview:
            self.pCamera.configure(self.preview_config)
        else:
            self.pCamera.configure(self.capture_config)
            
        #turn off auto white balance and exposure
        self.pCamera.set_controls({"AwbEnable":False, "AeEnable":False})

        #set analogue gain, exposure time, and red and blue gains 
        self.pCamera.set_controls({"AnalogueGain": fAnalogGain,"ExposureTime": nExposureTime_us, 
        "ColourGains":(fRedGain,fBlueGain)}) 
        
        self.pCamera.start() # start capturing AFTER setting controls, rather than putting in delay
        
        #save metadata
        mapMetaData = self.pCamera.capture_metadata()
        
        # capture image
        arrImage = self.pCamera.capture_array()

        # stop capturing
        self.pCamera.stop()

        return mapMetaData, arrImage

    def shutdown(self):
        print("Closing camera")
        self.pCamera.close()

if __name__ == "__main__":
    
    strDirectory = os.path.dirname(os.path.realpath(__file__))

    pCameraController = CameraController(strDirectory)
    
    pMetadata, arrImage = pCameraController.captureImage(7.0, 2.5, 2.5, 65000)
    
    Image.fromarray(arrImage).save("test.tiff")
    