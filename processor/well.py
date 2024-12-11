import math
import numpy as np
from random import random

# PARAMETER
fFractionalThreshold = 0.20 # fraction of +ve pixels to call +ve well

fUVSlope = 0.4787443744374433
fUVOffset = 93.17743474347438
fVisSlope = 0.7410561056105607
fVisOffset = -25.893887788778862

nUVRedCutoff = 150

# (nRed, nBlue) points ABOVE this line are positive
def getUVLine(nRed):
    if nRed > nUVRedCutoff:
        nBlue = 256
    else:
        nBlue = nRed*fUVSlope+fUVOffset
    return nBlue
    
# (nRed, nBlue) points BELOW this line are positive
def getVisLine(nRed):
    return nRed*fVisSlope+fVisOffset

def findWellPixels(arrIntensity, nOriginRow, nOriginCol, nWellSize_pix, nThreshold, nBelowThisRow = -1):
    # expect to find first well around the origin, check random pixels
#    print("T: ", nThreshold)
    nCount = 0
    setStart = set()
    while nCount < nWellSize_pix: # fairly sparse search
        nCol = nOriginCol + int((0.5-random())*nWellSize_pix)
        nRow = nOriginRow + int((0.5-random())*nWellSize_pix)
        if nRow < nBelowThisRow:
            continue
        if arrIntensity[nRow, nCol] > nThreshold:
            setStart.add((nRow, nCol))
        nCount += 1

    # now search for connected pixels over threshold, if we found a good pixel
    setWell = set()
    lstStart = list(setStart)
    for nRow, nCol in lstStart:
        if (nRow, nCol) in setWell:
            continue
        setWell.add((nRow, nCol))
        setCandidates = set([(nRow-1, nCol-1), (nRow-1, nCol), (nRow-1, nCol+1),
                                    (nRow, nCol-1),                     (nRow, nCol+1),
                                    (nRow+1, nCol-1), (nRow+1, nCol), (nRow+1, nCol+1)])
        while len(setCandidates): # tail-recursive loop
            nRow, nCol = setCandidates.pop()
            if nBelowThisRow >= 0:
                # we are working on overflow, which can exceed image size
                if nRow < nBelowThisRow:
                    continue

                # stop overflow from running out into the tray area, which can happen
                if nCol < nOriginCol-nWellSize_pix or nCol >= arrIntensity.shape[1]:
                    continue
                if nRow < 0 or nRow >= arrIntensity.shape[0]:
                    continue
                    
            if (nRow, nCol) not in setWell:
                if nRow-1 < 0 or nRow+1 >= arrIntensity.shape[0]:
                    continue
                if nCol-1 < 0 or nCol+1 >= arrIntensity.shape[1]:
                    continue
                if arrIntensity[nRow, nCol] > 0.9*nThreshold:
                    setWell.add((nRow, nCol))
                    setCandidates.update([(nRow-1, nCol-1), (nRow-1, nCol), (nRow-1, nCol+1),
                                        (nRow, nCol-1),                     (nRow, nCol+1),
                                        (nRow+1, nCol-1), (nRow+1, nCol), (nRow+1, nCol+1)])
    
    return setWell

class Well:
    """
    A well represents a single dimple in the Idexx tray. It has a size in pixels and
    and position in pixels at creation. After processing it has computed image 
    coordinates and an array of pixel values associated with it.
    """
    def __init__(self, nRow, nCol, nSize, bUV):
        self.nSize = nSize
        self.bUV = bUV
        
        self.nRow = nRow # pixel co-ordinates based on approximate geometry
        self.nCol = nCol
        
        self.lstPixels = [] # (nRow, nCol) values from image array
        self.lstValues = [] # RGB values from image array
        self.lstPositive = [] # > 0 for positive, 0 for negative
        
        self.nPixelRow = -1 # pixel co-ordinates based on values
        self.nPixelCol = -1
        
        self.bPositive = False # not positive yet

    def fewPixels(self):
        # return true if have less than half the expected pixels flagged
        return len(self.lstPixels) < (self.nSize**2)/2

    def excessPixels(self):
        # return true if have more than half the expected pixels flagged
        return len(self.lstPixels) > self.nSize**2

    def setPixels(self, lstPixels):
        self.lstPixels = lstPixels

    def setValues(self, lstValues):
        self.lstValues = lstValues
        
    def regeneratePixels(self, arrIntensity, arrImage, nThreshold):
        fFactor = 1.0
        setWellPixels = set()
        while not len(setWellPixels) and fFactor > 0.8:
            setWellPixels = findWellPixels(arrIntensity, self.nPixelRow, self.nPixelCol, self.nSize, fFactor*nThreshold)
            fFactor *= 0.99
        self.lstPixels = []
        self.lstValues = []
        for (nPixelRow, nPixelCol) in setWellPixels:
            self.lstPixels.append((nPixelRow, nPixelCol))
            self.lstValues.append(arrImage[nPixelRow, nPixelCol])
        
    def findCentreFromPixels(self):
        # unweighted mean
        if len(self.lstPixels):
            self.nPixelRow = sum([nRow for nRow, nCol in self.lstPixels])//len(self.lstPixels)
            self.nPixelCol = sum([nCol for nRow, nCol in self.lstPixels])//len(self.lstPixels)
        else:
            print("NO PIXELS in findCentreFromPixels AT: ", self.nRow, self.nCol)
            self.nPixelRow = self.nRow
            self.nPixelCol = self.nCol
            
    def classify(self):
        # Determine if the well is positive in the visible or UV
        self.lstPositive = []
        nCount = 0
        for nI, (nR, nG, nB) in enumerate(self.lstValues):
            if self.bUV:
                if nR < nUVRedCutoff: # only count under cutoff in red for UV due to saturation
                    nCount += 1
                if nB > getUVLine(nR): # in the UV outer pixels tend to turn first and most clearly, so enhance!
                    nDist = int(math.sqrt((self.lstPixels[nI][0]-self.nPixelRow)**2+(self.lstPixels[nI][1]-self.nPixelCol)**2))
                    self.lstPositive.append(nDist)
                else:
                    self.lstPositive.append(0)
            else:
                nCount += 1
                if nB < getVisLine(nR):
                    self.lstPositive.append(1) # radial correction not needed here (yet)
                else:
                    self.lstPositive.append(0)
                    
        self.bPositive = False
        if sum(self.lstPositive)/(nCount+1) > fFractionalThreshold:
            self.bPositive = True

    def simpleClassify(self):
        # Determine if the well is positive in the visible or UV
        self.lstPositive = []
        nCount = 0
        for nI, (nR, nG, nB) in enumerate(self.lstValues):
            if self.bUV:
                if nR < nSimpleUVRedThreshold: # only count under cutoff in red for UV due to saturation
                    nCount += 1
                    self.lstPositive.append(1)
                else:
                    self.lstPositive.append(0)
            else: # visible
                nCount += 1
                if nB < nSimpleVisBlueThreshold:
                    self.lstPositive.append(1) # radial correction not needed here (yet)
                else:
                    self.lstPositive.append(0)
                    
        self.bPositive = False
        if sum(self.lstPositive)/(nCount+1) > fSimpleThreshold:
            self.bPositive = True
