import atexit

import numpy as np
from PIL import Image

mapDummyMetaData = {"AeLocked": False,
"AnalogueGain": 6.78145694732666,
"ColourCorrectionMatrix": (2.2561264038085938, -1.218212366104126, -0.005854170303791761, -0.10794853419065475, 1.6070090532302856, -0.5276356339454651, -0.008709984831511974, -0.4265385866165161, 1.4563173055648804),
"ColourGains": (4.400000095367432, 1.0),
"ColourTemperature": 8600,
"DigitalGain": 1.0027344226837158,
"ExposureTime": 65000,
"FocusFoM": 9379,
"FrameDuration": 100000,
"Lux": 49.23330307006836,
"ScalerCrop": (0, 0, 4056, 3040),
"SensorBlackLevels": (4096, 4096, 4096, 4096),
"SensorTemperature": 22.0,
"SensorTimestamp": 88610006344000}

class DummyCameraController:

    def __init__(self, strDirectory):        
        
        atexit.register(self.shutdown)
        
    def captureImage(self, fAnalogGain, fRedGain, fBlueGain, nExposureTime_us, bPreview, bUV=False):
        
        # load images
        if bPreview:
            if bUV:
                arrImage = np.array(Image.open("test_preview_uv.png"))
            else:
                arrImage = np.array(Image.open("test_preview_vis.png"))
        else:
            if bUV:
                arrImage = np.array(Image.open("test_image_uv.jpg")) # jpg because huge
            else:
                arrImage = np.array(Image.open("test_image_vis.jpg"))

        return mapDummyMetaData, arrImage

    def shutdown(self):
        print("Closing camera")
