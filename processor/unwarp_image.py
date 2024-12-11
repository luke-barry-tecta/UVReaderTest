import math
import numpy as np
import os

"""Applies the Tsai unwarping model to an image held as a numpy array.

The model is:

Xu = Xd*(1+k*Rd**2)
Yu = Yd*(1+k*Rd**2)

where:

Rd**2 = Xd**2 + Yd**2

and X and Y are in image-center coordinates, so:

Xd = nColD - nCenterCol
Yd = nRowD - nCenterRow

nColU = Xu + nCenterRow
nRowU = Yu + nCenterCol

and Xd, Yd are the coordinates in the distorted (original, source) image
and Xu, Yu are the coordinates in the undistorted (target) image.

Geometric image transformation always has to be done on a "pull"
model, where we raster over the coordinates of the target and find
the equivalent pixel in the source. If we raster over the source image
there will be pixesl in the target image that get missed, because 
multiple source pixels map onto a single target pixel in some cases,
and NO souce pixel maps onto some target pixels, by the nature of
integer arithmetic.

However, the radius in the Tsai model is in terms of the distorted
image, so we need a mapping between the unwarped radius and
the warped radius.

This is given by:

k*Rd**3 + Rd - Ru = 0

Under the circumstances found here this equation has two complex
and one real root, which is always returned last. The real root is the
one we want.

"""

nColors = 3
nDimensions = 2

def distanceFunction(fTargetRsquared, fK):
    # This is the "right" way to get the distorted distance from the undistorted
    # value, but it is fantastically slow (~40 times slower than the simple lookup
    # used here, taking an unwarping from < 0.5 s to ~20 seconds.). It is used
    # go generate a lookup table during construction of the Unwarper, and this
    # lookup table is used--without interpolation--during unwarping. The
    # difference in the resulting unwarped images with and without interpolation
    # is minimal.
    return (np.roots([fK, 0, 1, -math.sqrt(fTargetRsquared)])[-1].real)**2

class Unwarper:
    
    def __init__(self, fK):
        
        self.fK = fK

        nSteps = 100 # size of radius mapping array
        self.fRsquaredStep = 1/nSteps # used to index source distance array
        self.lstSourceRsquared = []
        for nI in range(nSteps+20): # go beyond 1 to allow for interpolation
            fTargetRsquared = self.fRsquaredStep*nI
            self.lstSourceRsquared.append(distanceFunction(fTargetRsquared, self.fK))

    def distanceMap(self, fTargetRsquared):
        # map the unwarped distance (target) to the warped distance (source) 
        fIndex = fTargetRsquared/self.fRsquaredStep
        nIndex = int(fIndex)
        fLow = self.lstSourceRsquared[nIndex]
        fHigh = self.lstSourceRsquared[nIndex+1]
        fSourceRsquared = fLow + (fHigh-fLow)*(fIndex-nIndex)
        return fSourceRsquared
        
    def unwarpImage(self, arrImage, nPadding=0):
        """This applies the Tsai camera model unwarping factor
        to an image. The radial distance is scaled to the image
        size so that K is independent of image size."""
        nCenterRow = arrImage.shape[0]//2
        nCenterCol = arrImage.shape[1]//2
        fRsquaredMax = nCenterRow**2+nCenterCol**2
        arrUnwarped = np.array(arrImage)
        if nPadding:
            arrUnwarped = np.pad(arrUnwarped, ((nPadding, nPadding), (nPadding, nPadding), (0, 0)), constant_values=0)
        nTargetCenterRow = arrUnwarped.shape[0]//2
        nTargetCenterCol = arrUnwarped.shape[1]//2
        for nRow in range(arrUnwarped.shape[0]):
            for nCol in range(arrUnwarped.shape[1]):
                # unlike the unwarping of points, here pull rather than push
                # to ensure that every target pixel gets filled.
                fDist = ((nRow-nTargetCenterRow)**2+(nCol-nTargetCenterCol)**2)/fRsquaredMax
                fDist = self.lstSourceRsquared[int(fDist/self.fRsquaredStep)] # 15% faster than distanceMap()
                nSourceRow = int((nRow - nTargetCenterRow)/(1+self.fK*fDist))+nCenterRow
                nSourceCol = int((nCol - nTargetCenterCol)/(1+self.fK*fDist))+nCenterCol
                if self.fK < 0 or nPadding > 0:
                    if nSourceRow >= 0 and nSourceRow < arrImage.shape[0]:
                        if nSourceCol >= 0 and nSourceCol < arrImage.shape[1]:
                            arrUnwarped[nRow, nCol] = arrImage[nSourceRow, nSourceCol]
                else:
                        arrUnwarped[nRow, nCol] = arrImage[nSourceRow, nSourceCol]
                    
        return arrUnwarped

class PrecomputedUnwarper:
    """
    This is an attempt to speed things up by precomputing the unwarping
    map. It does not work.
    """
    
    def __init__(self, fK, nSourceWidth, nSourceHeight, nPadding):
        
        self.fK = fK
        self.nSourceWidth = nSourceWidth
        self.nSourceHeight = nSourceHeight
        self.nPadding = nPadding

        nSteps = 100 # size of radius mapping array
        self.fRsquaredStep = 1/nSteps # used to index source distance array
        self.lstSourceRsquared = []
        for nI in range(nSteps+50): # go beyond 1 to allow for interpolation
            fTargetRsquared = self.fRsquaredStep*nI
            self.lstSourceRsquared.append(distanceFunction(fTargetRsquared, self.fK))
            
        self.generateMap()

    def distanceMap(self, fTargetRsquared):
        # map the unwarped distance (target) to the warped distance (source) 
        fIndex = fTargetRsquared/self.fRsquaredStep
        nIndex = int(fIndex)
        fLow = self.lstSourceRsquared[nIndex]
        fHigh = self.lstSourceRsquared[nIndex+1]
        fSourceRsquared = fLow + (fHigh-fLow)*(fIndex-nIndex)
        return fSourceRsquared
        
    def generateMap(self):
        """This precomputes the Tsai camera model unwarping map
        for an image. The radial distance is scaled to the image
        size so that K is independent of image size."""
        nCenterRow = self.nSourceHeight//2
        nCenterCol = self.nSourceWidth//2
        fRsquaredMax = nCenterRow**2+nCenterCol**2
        self.nTargetHeight = self.nSourceHeight+self.nPadding*2
        self.nTargetWidth = self.nSourceWidth+self.nPadding*2
        nTargetCenterRow = self.nTargetHeight//2
        nTargetCenterCol = self.nTargetWidth//2

        strFilename = "unwarp_map_"+str(self.nTargetHeight)+"_"+str(self.nTargetWidth)+".npy"
        if os.path.exists(strFilename):
            self.arrFlatMap = np.load(strFilename)
        else:
            self.arrFlatMap = np.zeros([self.nTargetHeight*self.nTargetWidth*nColors], dtype=int)
            for nRow in range(self.nTargetHeight):
                for nCol in range(self.nTargetWidth):
                    # unlike the unwarping of points, here pull rather than push
                    # to ensure that every target pixel gets filled.
                    fDist = ((nRow-nTargetCenterRow)**2+(nCol-nTargetCenterCol)**2)/fRsquaredMax
                    fDist = self.lstSourceRsquared[int(fDist/self.fRsquaredStep)] # 15% faster than distanceMap()
                    nSourceRow = int((nRow - nTargetCenterRow)/(1+self.fK*fDist))+nCenterRow
                    nSourceCol = int((nCol - nTargetCenterCol)/(1+self.fK*fDist))+nCenterCol
                    if nSourceRow >= 0 and nSourceRow < self.nSourceHeight:
                        if nSourceCol >= 0 and nSourceCol < self.nSourceWidth:
                            for nRGB in range(nColors):
                                self.arrFlatMap[nRow*self.nTargetWidth*nColors+nCol*nColors+nRGB] = nSourceRow*self.nSourceWidth*nColors+nSourceCol*nColors+nRGB
            np.save(strFilename, self.arrFlatMap)
            
    def unwarpImage(self, arrImage):
        """This applies the Tsai camera model unwarping factor
        to an image. The radial distance is scaled to the image
        size so that K is independent of image size."""
        return arrImage.flatten()[self.arrFlatMap].reshape([self.nTargetHeight, self.nTargetWidth, 3])
                    
if __name__ == "__main__":
    from PIL import Image
    from time import time
    
    fK = 0.1322595

    if False:
        pUnwarper = Unwarper(fK)

        # test unwarp of real images
        strDir = "../../first_images/carrier/"
        strDir = "../../white_card/DW Colisure White card/"
        strDir = "."
        for strFile in os.listdir(strDir):
            if strFile.endswith(".tiff"):
                strImageFile = os.path.join(strDir, strFile)
                print(strImageFile)
                
                pImage = Image.open(strImageFile)            
                arrImage = np.array(pImage) # RGB image array
                
                fStartTime = time()
                arrUnwarped = pUnwarper.unwarpImage(arrImage)
                print(time() - fStartTime)
                pUnwarped = Image.fromarray(arrUnwarped)
                pUnwarped.save(strImageFile.replace(".tiff", "_unwarp.png"))

    fStartTime = time()
#    pUnwarper = PrecomputedUnwarper(fK, 640, 480, 20)
    pUnwarper = PrecomputedUnwarper(fK, 4056, 3040, 200)
    print("Init: ", time()-fStartTime)

    # test unwarp of real images
    strDir = "../../first_images/carrier/"
    strDir = "../../white_card/DW Colisure White card/"
    strDir = "."
    for strFile in os.listdir(strDir):
        if strFile.endswith(".tiff"):
            strImageFile = os.path.join(strDir, strFile)
            print(strImageFile)
            
            pImage = Image.open(strImageFile)            
            if False:
                nTargetWidth = 640 # pixels
                print(pImage.size)
                if pImage.size[0] > nTargetWidth:
                    nHeight = int(pImage.size[1]*nTargetWidth/pImage.size[0])+1 # should be 480
                    pImage = pImage.resize((nTargetWidth, nHeight), Image.Resampling.LANCZOS)        
            arrImage = np.array(pImage) # RGB image array
            
            fStartTime = time()
            arrUnwarped = pUnwarper.unwarpImage(arrImage)
            print(time() - fStartTime)
            pUnwarped = Image.fromarray(arrUnwarped)
            pUnwarped.save(strImageFile.replace(".tiff", "_precomputed_unwarp.png"))
