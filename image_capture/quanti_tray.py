import math
import numpy as np
import os
from PIL import Image
import sys
from time import time

from constants import *
from unwarp_image import PrecomputedUnwarper
from well import Well, findWellPixels
from write_images import *

# Based on early calibration images. For UV especially expect to change
# with new camera settings.

def boxcar(arrLine, nWidth):
    # do simple boxcar smoothing, ignoring the ends
    arrOut = np.array(arrLine)
    nHalfWidth = nWidth//2
    for nI in range(arrLine.shape[0]):
        if nI >= nHalfWidth and nI < arrLine.shape[0]-nHalfWidth:
            arrOut[nI] = sum(arrLine[nI-nHalfWidth: nI+nHalfWidth])/nWidth

    return arrOut
    
def findEdge(arrImage, nColumnIndex, nStartRow, nEndRow):
    # find an edge working down a column from the top
    
    arrColumn = np.zeros(arrImage.shape[0])
    for nI, arrLine in enumerate(arrImage): # green column
        arrColumn[nI] = arrLine[nColumnIndex][2]

    nPeak = 0
    fMax = 0
    for nI in range(nStartRow, nEndRow):
        fDiff = arrColumn[nI+3]-arrColumn[nI]
        if fDiff > fMax:
            fMax = fDiff
            nPeak = nI
            
    return nPeak

def findRectangle(arrIntensity):
    # find the basic rectangle after BG subtraction
    nTopRow = -1
    nEndRow = -1
    for nI, arrRow in enumerate(arrIntensity):
        if nTopRow < 0 and np.sum(arrRow) > nRectangleStartThreshold:
            nTopRow = nI
        if np.sum(arrRow) > nRectangleEndThreshold:
            nEndRow = nI
    for nLeftCol, arrCol in enumerate(arrIntensity.T):
        if np.sum(arrCol) > nRectangleStartThreshold:
            break
    
    return nTopRow, nLeftCol, nEndRow

def bgSubtract(arrImage):

    # ensure we are above the actual well pixels
    for nEndRow, arrRow in enumerate(arrImage[nBGStartRow:]):
        nMax = np.max(arrRow[:, 1])
        if nMax > nBGWellThreshold:
            break
    nEndRow += nBGBoundary # step back from edge of wells
    nStartRow = nEndRow - nBGStartRow
    while nStartRow < 0:
        nStartRow += 1
    
    # find top of tray based on general region
    nColumnIndex = arrImage.shape[1]//2
    nUpperEdge = findEdge(arrImage, nColumnIndex, nStartRow, nEndRow)
    nEdge = nUpperEdge+nBGShift
    
    arrBGRow = arrImage[nEdge].astype(float)
    lstBands = [boxcar(arrBGRow[ :, nI], nBGWidth) for nI in range(3)]
    for nI in range(3):
        arrBGRow[ :, nI] = lstBands[nI]    
    fBackground = np.sum(arrBGRow)/arrBGRow.shape[0] # used for thresholding
    
    arrDiff = arrImage.astype(float) # background-subtract, clip, and rescale
    for nRow in range(arrImage.shape[0]):
        arrDiff[nRow] -= arrBGRow
    arrDiff = np.clip(arrDiff, 0, None)
    fRatio = 254/np.max(arrDiff)
    arrDiff *= fRatio
    return arrDiff.astype(np.uint8), fBackground

class NoOriginException(Exception):
    
    def __init__(self, strFilename):
        Exception.__init__(self, strFilename)

class BadScaleException(Exception):
    
    def __init__(self, strFilename):
        Exception.__init__(self, strFilename)

class QuantiTray:
    """
    The origin of the coordinate system of the tray is the upper left small well as the front of
    the tray is facing you with the big overflow well on the right. X increases to the right,
    Y increases down, in comformity the usual image layout. Small wells all have negative X.
    
    The scale and origin passed into the constructor are approximate and can be refined
    by calling findBigWells, which should be called before calling findSmallWells.
    
    Note that not all trays have small wells, so when that state is detected some things
    are turned off.
    """
    def __init__(self, strImageFile, bUV, bHasSmallWells, bDebug, pCallback=None):

        # image file and rough initial scale/location
        self.strImageFile = strImageFile
        self.bGoodScale = True # assume scale passed in is good
        self.bUV = bUV  # required for overflow well analysis and algorithm
        self.bHasSmallWells = bHasSmallWells
        self.bGood = True # assume things work
        
        self.pCallback = pCallback

        if self.bHasSmallWells:
            self.nBigWellRows = 6
            self.nBigWellCols = 8
            self.nSmallWellRows = 10
            self.nSmallWellCols = 5 # Except for first and last row, which have just 4 (taken care of at construction)
        else:
            self.nBigWellRows = 5
            self.nBigWellCols = 10
            self.nSmallWellRows = 0
            self.nSmallWellCols = 0
        
        self.bDebugOutput = bDebug
        
    def setDebugOutput(self, bDebugOutput):
        self.bDebugOutput = bDebugOutput
        
    def process(self):
        """Actually do the processing. This used to be in the constructor but
        separating it allows other state to be set before doing so, like if we
        want debug info or not, and which images to write in the process of
        processing (currently just yes/no on debug, but could be fancier)
        """
        
        # image file as numpy array
        pImage = Image.open(self.strImageFile)
        if pImage.size[0] > nTargetWidth:
            nHeight = int(pImage.size[1]*nTargetWidth/pImage.size[0])+1 # should be 480
            pImage = pImage.resize((nTargetWidth, nHeight), Image.Resampling.LANCZOS)        
            
        if self.pCallback: self.pCallback() # report progress
        
        pUnwarper = PrecomputedUnwarper(fK, pImage.size[0], pImage.size[1], nPadding) # this gives us excellent rectilinear geometry
        self.arrImage = pUnwarper.unwarpImage(np.array(pImage))
        
        if self.pCallback: self.pCallback() # report progress
        
        self.arrImage, fBackground = bgSubtract(self.arrImage) # RGB image array
        self.arrIntensity = np.sum(self.arrImage, axis=2)
        
        if self.bDebugOutput:
            saveto(self.strImageFile, self.arrImage, "unwarped")

        if self.pCallback: self.pCallback() # report progress
        
        # generate histogram and determine threshold, which is based on the low point above
        # 100. The "since" value cuts the search off if we haven't seen a new low after 25 grey
        # values. This deals with noise and prevents us from getting caught by the drop off
        # at the upper end.
        nImax, nJmax, _ = self.arrImage.shape
        self.lstHist = [0 for nI in range(256*3)] # 256 to make room for resampling error
        for nI in range(nImax): # generate intensity array for basic processing, and histogram
            for nValue in self.arrIntensity[nI, : ]:
                self.lstHist[nValue] += 1
        strHistFile = self.strImageFile.replace(".tiff", ".hst")
        nMinCount = 1E8
        self.nThreshold = 0
        nSince = 0
        
        if self.bDebugOutput: # output histogram if required
            with open(strHistFile, "w") as outFile:
                for nI, nCount in enumerate(self.lstHist):
                    outFile.write(" ".join(map(str, (nI, nCount)))+"\n")

        for nI, nCount in enumerate(self.lstHist): # identify threshold
            if nI > nLowerThreshold and nSince < nSinceThreshold:
                if nCount < nMinCount:
                    nMinCount = nCount
                    self.nThreshold = int(nI)
                    nSince = 0
                else:
                    nSince += 1    

        # very high thresholds are a result of bad histogram
        if self.nThreshold > nHighThresholdLimit: # PARAMETERS
            self.nThreshold = int(fBackgroundMultiplier*fBackground)
            
        if self.pCallback: self.pCallback() # report progress
        
        # find the upper-left big well and use it to nail down origin
        self.findOrigin()

        if self.pCallback: self.pCallback() # report progress
        
        # known tray geometry => this sets the scale
        self.generateBigWells()
        
        if self.pCallback: self.pCallback() # report progress
        
        self.lstSmallWells = [] # dummy for cases where we have none
        if self.bHasSmallWells:
            # use the big well geometry to find the small wells
            self.generateSmallWells()        
        
        if self.pCallback: self.pCallback() # report progress
        
        # regularize wells by finding and adjusting outliers
        self.regularizeWells()
        
        if self.pCallback: self.pCallback() # report progress
        
        # analyze overflow
        self.analyzeOverflow()
        
        if not self.bGoodScale:
            raise BadScaleException(self.strImageFile)

    def generateBigWells(self):
        # big wells start at zero and go forward. Column major vertical
        self.lstBigWells = []
        nBigWellSize_pix = int(fBigWellSize_mm*self.fScale)
        nBigWellSpacing_pix = int(fBigWellSpacing_mm*self.fScale)
        nRow = self.nOriginRow
        for nI in range(self.nBigWellRows):
            nRow = self.nOriginRow +nI*nBigWellSpacing_pix
            self.lstBigWells.append([]) # append next row
            nCol = self.nOriginCol                
            for nJ in range(self.nBigWellCols):
                if self.pCallback: self.pCallback() # report progress
                self.lstBigWells[-1].append(Well(nRow, nCol, nBigWellSize_pix, self.bUV))
                
                setWellPixels = set()
                fFactor = 1.0
                while not len(setWellPixels) and fFactor > fWellFactorThreshsold: # deal with bad contrast... carefully PARAMETER
                    setWellPixels = findWellPixels(self.arrIntensity, nRow, nCol, nBigWellSize_pix, fFactor*self.nThreshold)
                    fFactor *= fWellFactorReduction # very slow reduction PARAMETER
                
                lstWellPixels = []
                lstWellValues = []
                for (nPixelRow, nPixelCol) in setWellPixels:
                    lstWellPixels.append((nPixelRow, nPixelCol))
                    lstWellValues.append(self.arrImage[nPixelRow, nPixelCol])
                self.lstBigWells[-1][-1].setPixels(lstWellPixels)
                self.lstBigWells[-1][-1].setValues(lstWellValues)
                self.lstBigWells[-1][-1].findCentreFromPixels()
                if len(self.lstBigWells[-1]) > 1:
                    if self.lstBigWells[-1][-1].nPixelCol == self.lstBigWells[-1][-2].nPixelCol:
                        self.lstBigWells[-1][-1].nPixelCol = nCol # force approximate
                        print("Duplicate well: ", nRow, nCol, "|", self.lstBigWells[-1][-1].nPixelRow, self.lstBigWells[-1][-1].nPixelCol)
                        
                    # recompute spacing as we go in the first row
                    if not nI:
                        nBigWellSpacing_pix = (self.lstBigWells[-1][-1].nPixelCol-self.lstBigWells[-1][0].nPixelCol)//(len(self.lstBigWells[-1])-1)

                # increment column and use previous row position to determine current one
                nCol = self.lstBigWells[-1][-1].nPixelCol + nBigWellSpacing_pix
                nRow = self.lstBigWells[-1][-1].nPixelRow
                        
            if not nI: # recompute scale and origin after first row
                self.fScale = (self.lstBigWells[-1][-1].nPixelCol-self.lstBigWells[-1][0].nPixelCol)/(fBigWellSpacing_mm*(len(self.lstBigWells[-1])-1))
                self.nOriginRow = sum([pWell.nPixelRow for pWell in self.lstBigWells[-1]])//len(self.lstBigWells[-1])
                nBigWellSize_pix = int(fBigWellSize_mm*self.fScale)
                nBigWellSpacing_pix = int(fBigWellSpacing_mm*self.fScale)
            
            # increment row based on previous row, not global co-ordinates
            nRow = self.lstBigWells[-1][-1].nPixelRow + nBigWellSpacing_pix
    
    def generateSmallWells(self):
        # small wells start with the leftmost. Column major vertical
        self.lstSmallWells = []
        nSmallWellSize_pix = int(fSmallWellSize_mm*self.fScale) # scale from big wells
        nSmallWellSpacing_pix = int(fSmallWellSpacing_mm*self.fScale) # scale from big wells
        nFirstSmallWellCol_pix = self.nOriginCol + int(fFirstSmallWellColumn_mm*self.fScale)
        nSmallWellOriginRow = self.nOriginRow
        for nI in range(self.nSmallWellRows):
            nRow = self.nOriginRow + nI*nSmallWellSpacing_pix
            self.lstSmallWells.append([]) # append next row
            for nJ in range(self.nSmallWellCols):
                if self.pCallback: self.pCallback() # report progress
                # skip outer corner small wells
                if nJ == 0 and (nI ==0 or nI == self.nSmallWellRows-1):
                    continue
                nCol = nFirstSmallWellCol_pix + nJ*nSmallWellSpacing_pix
                self.lstSmallWells[-1].append(Well(nRow, nCol, nSmallWellSize_pix, self.bUV))

                setWellPixels = set()
                fFactor = 1.0
                while not len(setWellPixels) and fFactor > fWellFactorThreshsold: # deal with bad contrast... carefully
                    setWellPixels = findWellPixels(self.arrIntensity, nRow, nCol, nSmallWellSize_pix, fFactor*self.nThreshold)
                    fFactor *= fWellFactorReduction # very slow reduction
                
                lstWellPixels = []
                lstWellValues = []
                for (nPixelRow, nPixelCol) in setWellPixels:
                    lstWellPixels.append((nPixelRow, nPixelCol))
                    lstWellValues.append(self.arrImage[nPixelRow, nPixelCol])
                self.lstSmallWells[-1][-1].setPixels(lstWellPixels)
                self.lstSmallWells[-1][-1].setValues(lstWellValues)
                self.lstSmallWells[-1][-1].findCentreFromPixels()
            if not nI: # first row
                nSmallWellSpacing_pix = (self.lstSmallWells[-1][-1].nPixelCol-self.lstSmallWells[-1][0].nPixelCol)//(len(self.lstSmallWells[-1])-1)
                nSmallWellOriginRow = sum([pWell.nPixelRow for pWell in self.lstSmallWells[-1]])//len(self.lstSmallWells[-1])

    def analyzeOverflow(self):
        
        # this finds the line of water fill
        self.nOverflowStartCol =  self.nRightCol + int(fOverflowXStart*self.fScale)
        self.nOverflowEndCol =  self.nRightCol + int(fOverflowXEnd*self.fScale)
        if self.bUV: # use red edge for UV images, blue edge for visible
            arrSum = np.sum(self.arrImage[ :, self.nOverflowStartCol:self.nOverflowEndCol, 0], 1, dtype=int)
        else:
            arrSum = np.sum(self.arrImage[ :, self.nOverflowStartCol:self.nOverflowEndCol, 2], 1, dtype=int)
        nDiffRange = 3
        arrSumDiff = np.abs(arrSum[nDiffRange:] - arrSum[:-nDiffRange])
        arrWindow = np.hamming(arrSumDiff.shape[0])
        arrSumDiff = arrSumDiff*arrWindow
        self.nOverflowLine = np.argmax(arrSumDiff)+nDiffRange
        
        # now look for overflow pixels
        nRange = self.nOverflowEndCol - self.nOverflowStartCol
        nMid = (self.nOverflowEndCol + self.nOverflowStartCol)//2
        try:
            nThreshold = 0.7*self.arrIntensity[self.nOverflowLine+nRange, nMid]      # PARAMETER  
            setOverflowPixels = findWellPixels(self.arrIntensity, self.nOverflowLine+nRange, nMid, nRange, nThreshold, self.nOverflowLine)
        except IndexError as e:
            print("OVERFLOW DETECTION FAILURE")
            nOverflowRow = self.arrIntensity.shape[0]//2
            nOverflowCol = self.arrIntensity.shape[1] - nOverflowColOffset
            nThreshold = 0.7*self.arrIntensity[nOverflowRow, nOverflowCol]
        self.pOverflow = Well(0, 0, 0, self.bUV) # overflow is just a well
        lstOverflowPixels = []
        lstOverflowValues = []
        for (nPixelRow, nPixelCol) in setOverflowPixels:
            lstOverflowPixels.append((nPixelRow, nPixelCol))
            lstOverflowValues.append(self.arrImage[nPixelRow, nPixelCol])
        self.pOverflow.setPixels(lstOverflowPixels)
        self.pOverflow.setValues(lstOverflowValues)
        
        if self.bDebugOutput: # turn on/off test output
            strFilename = self.strImageFile.replace(".tiff", "_overflow.dat")
            with open(strFilename, "w") as outFile:
                for nI, nDiff in enumerate(arrSumDiff):
                    outFile.write(" ".join(map(str, (nI, nDiff)))+"\n")

    def findOrigin(self):
        
        """ 
        Simple-minded origin detector just searches in the general vicinity. Even with the sloppy
        prototype setup this finds the orgin well (upper left big well) correctly, so with production
        setup it should be very good. I've added some threshold-reduction and a minimum origin
        pixel set size to improve performance on bad images.
        """
        
        # find edges of layout. This can vary by dozens of pixels in the prototype hardware
        self.nOriginRow, self.nOriginCol, nEndRow = findRectangle(self.arrIntensity)
        fPhysicalHeight = (self.nBigWellRows-1)*fBigWellSpacing_mm + fBigWellSize_mm
        nPixelHeight = nEndRow-self.nOriginRow
        self.fScale = nPixelHeight/fPhysicalHeight

        nBigWellSize_pix = int(self.fScale*fBigWellSize_mm)
        self.nOriginRow += nBigWellSize_pix//2
        if self.bHasSmallWells: # firstSmallWellColumn is negative position
            self.nOriginCol += -int(self.fScale*fFirstSmallWellColumn_mm) + nBigWellSize_pix//2
        else:
            self.nOriginCol += nBigWellSize_pix//2

        setOrigin = set()
        fFactor = 1.0
        while not len(setOrigin) and fFactor > fWellFactorThreshsold:
            setOrigin = findWellPixels(self.arrIntensity, self.nOriginRow, self.nOriginCol, nBigWellSize_pix, fFactor*self.nThreshold)
            fFactor *= fWellFactorReduction # very slow reduction

        if not len(setOrigin): # not able to find origin
            raise NoOriginException(self.strImageFile)
            
        self.nOriginRow = 0
        self.nOriginCol = 0
        for (nRow, nCol) in setOrigin:
            self.nOriginRow += nRow
            self.nOriginCol += nCol
        self.nOriginRow //= len(setOrigin)
        self.nOriginCol //= len(setOrigin)

    def regularizeWells(self):
        """
        There are sometimes wells that are out of line due to scatter,
        weak response, or what-have-you. This finds the median row/column
        for each line of wells and brings everything in line with it. I tried various
        techniques for only bringing outliers in, but they suffered from the usual
        problems of identifying outliers, and given the fixed geometry we are
        working with it is unlikely that there will be an issue with this approach
        """

        lstColPositions = [[0 for nI in range(len(self.lstBigWells))] for nJ in range(len(self.lstBigWells[0]))] # puts column positions into row-major order
        for nI, lstRow in enumerate(self.lstBigWells):
            lstRowPosition = [pWell.nPixelRow for pWell in lstRow if len(pWell.lstPixels) > nWellSizeThreshold] # don't use wells we can't find
            lstRowPosition.sort() # even size so median is between middle points
            nMedian = int((lstRowPosition[len(lstRowPosition)//2]+lstRowPosition[len(lstRowPosition)//2-1])/2)            
            for nJ, pWell in enumerate(lstRow): # bring outliers into alignment
                pWell.nPixelRow = nMedian
                lstColPositions[nJ][nI] = pWell.nPixelCol # accumulate column positions
                
        for nJ, lstCol in enumerate(lstColPositions): # force all columns into the median position
            lstCol.sort()
            nMedian = int((lstCol[len(lstCol)//2]+lstCol[len(lstCol)//2-1])/2)
            for lstRow in self.lstBigWells:
                lstRow[nJ].nPixelCol = nMedian

        # regenerate well pixels if required
        for nI, lstRow in enumerate(self.lstBigWells):
            if self.pCallback: self.pCallback() # report progress
            for nJ, pWell in enumerate(lstRow):
                if pWell.fewPixels():
                    pWell.regeneratePixels(self.arrIntensity, self.arrImage, 0.8*self.nThreshold)
                if pWell.excessPixels():
                    pWell.regeneratePixels(self.arrIntensity, self.arrImage, 1.2*self.nThreshold)
                if not len(pWell.lstPixels):
                    print("NO PIXELS BIG WELL:", nI, nJ)

        # set the positions of the corners for future use
        self.nRightCol = self.lstBigWells[0][-1].nPixelCol
        self.nBottomRow = self.lstBigWells[-1][-1].nPixelRow

        if self.bHasSmallWells: # only do this if we have small wells
            # small wells are complicated by the absence of the outer corner wells
            # deal with this by analyzing the top and bottom row separately, after handling the central block,
            # which we do here
            lstColPositions = [[0 for nI in range(len(self.lstSmallWells[1:-1]))] for nJ in range(len(self.lstSmallWells[1]))] # puts column positions into row-major order
            for nI, lstRow in enumerate(self.lstSmallWells[1:-1]):
                lstRowPosition = [pWell.nPixelRow for pWell in lstRow]
                lstRowPosition.sort() # odd size so median is middle point
                nMedian = lstRowPosition[len(lstRowPosition)//2]
                for nJ, pWell in enumerate(lstRow): # bring outliers into alignment
                    pWell.nPixelRow = nMedian
                    lstColPositions[nJ][nI] = pWell.nPixelCol # accumulate column positions

            lstColMedian = [] # now use the accumulated column positions to fix the columns
            for nJ, lstCol in enumerate(lstColPositions): # all but the first column
                lstCol.sort()
                nMedian = int((lstCol[len(lstCol)//2]+lstCol[len(lstCol)//2-1])/2)
                lstColMedian.append(nMedian)
                for lstRow in self.lstSmallWells[1:-1]:
                    lstRow[nJ].nPixelCol = nMedian

            # and finally deal with top and bottom row, syncing them with pre-computed column positions
            # (to which they will be minor contributors) but working out their own row positions
            for lstRow in [self.lstSmallWells[0], self.lstSmallWells[-1]]:
                lstRowPosition = [pWell.nPixelRow for pWell in lstRow]
                lstRowPosition.sort() # even size so median is between middle points
                nMedian = int((lstRowPosition[len(lstRowPosition)//2]+lstRowPosition[len(lstRowPosition)//2-1])/2)
                for nJ, pWell in enumerate(lstRow): # bring outliers into alignment
                    pWell.nPixelRow = nMedian
                    pWell.nPixelCol = int(lstColMedian[nJ+1])

            # regenerate well pixels if required
            for nI, lstRow in enumerate(self.lstSmallWells):
                if self.pCallback: self.pCallback() # report progress
                for nJ, pWell in enumerate(lstRow):
                    if pWell.fewPixels():
                        pWell.regeneratePixels(self.arrIntensity, self.arrImage, 0.8*self.nThreshold)
                    if pWell.excessPixels():
                        pWell.regeneratePixels(self.arrIntensity, self.arrImage, 1.2*self.nThreshold)
                    if not len(pWell.lstPixels):
                        print("NO PIXELS SMALL WELL:", nI, nJ)

        if False: # for debugging if we want to see every well position
            for nRow, lstRow in enumerate(self.lstBigWells):
                for nCol, pWell in enumerate(lstRow):
                    print(nRow, nCol, pWell.nPixelRow, pWell.nPixelCol)
            for nRow, lstRow in enumerate(self.lstSmallWells):
                for nCol, pWell in enumerate(lstRow):
                    print(nRow, nCol, pWell.nPixelRow, pWell.nPixelCol)
                
    def processComparator(self):
        """
        This is run on comparator images to fit all the wells and develop thresholds for
        each one. It isn't clear if we want each well to have its own fit or if we want
        there to be one for the whole unit.
        """
        if self.bGood:
            # write R/B to file for analysis
            strDir, strFile = os.path.split(self.strImageFile)
            strDir = os.path.join(os.path.join(strDir, "processed"), "lines")
            strSubdir = os.path.join(strDir, strFile.replace(".tiff", "").replace(" ", "_"))
            if not os.path.exists(strSubdir):
                os.mkdir(strSubdir)
                
            for nWellRow, lstRow in enumerate(self.lstBigWells):
                for nWellCol, pWell in enumerate(lstRow):
                    with open(os.path.join(strSubdir, "big_"+str(nWellRow)+"-"+str(nWellCol)+".dat"), "w") as outFile:
                        for (nRow, nCol) in pWell.lstPixels:
                            outFile.write(str(self.arrImage[nRow, nCol, 0])+" "+str(self.arrImage[nRow, nCol, 2])+"\n")

            for nWellRow, lstRow in enumerate(self.lstSmallWells):                
                for nWellCol, pWell in enumerate(lstRow):
                    with open(os.path.join(strSubdir, "small_"+str(nWellRow)+"-"+str(nWellCol)+".dat"), "w") as outFile:
                        for (nRow, nCol) in pWell.lstPixels:
                            outFile.write(str(self.arrImage[nRow, nCol, 0])+" "+str(self.arrImage[nRow, nCol, 2])+"\n")
                        
            # overflow well
            with open(os.path.join(strSubdir, "overflow.dat"), "w") as outFile:
                for (nRow, nCol) in self.pOverflow.lstPixels:
                    outFile.write(str(self.arrImage[nRow, nCol, 0])+" "+str(self.arrImage[nRow, nCol, 2])+"\n")

    def classifyWells(self):
        """
        This is called after the initializer to run the classification algorithm on the wells
        """
        if self.bGood:
            for lstRow in self.lstBigWells:
                for pWell in lstRow:
                    pWell.classify()
            for lstRow in self.lstSmallWells:
                for pWell in lstRow:
                    pWell.classify()
            self.pOverflow.classify()
            
    def getBigWellPositiveCount(self):
        nCount = 0
        for lstRow in self.lstBigWells:
            for pWell in lstRow:
                if pWell.bPositive:
                    nCount += 1
        if self.pOverflow.bPositive:
            nCount += 1
        return nCount
    
    def getSmallWellPositiveCount(self):
        nCount = 0
        for lstRow in self.lstSmallWells:
            for pWell in lstRow:
                if pWell.bPositive:
                    nCount += 1
        return nCount

