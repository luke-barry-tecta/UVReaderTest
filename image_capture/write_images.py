
import numpy as np
import os
from PIL import Image

# helper function to save intermediate steps of processing to various places
def saveto(strImageFile, arrImage, strType):
    strDir, strFile = os.path.split(strImageFile)
    strDir = os.path.join(os.path.join(strDir, "processed"), strType)
    strFile = strFile.replace(".tiff", "_"+strType+".png")
    Image.fromarray(arrImage).save(os.path.join(strDir, strFile))

# helper function to save vertical lines
def saveColumn(strImageFile, arrImage, strType, nColumnIndex):
    strDir, strFile = os.path.split(strImageFile)
    strDir = os.path.join(os.path.join(strDir, "processed"), strType)
    strFile = strFile.replace(".tiff", "_"+strType+".dat")
    with open(os.path.join(strDir, strFile), "w") as outFile:
        arrColumn = np.zeros(arrImage.shape[0])
        for nI, arrLine in enumerate(arrImage): # green column
            arrColumn[nI] = arrLine[nColumnIndex][2]
            
        lstDiff = [arrColumn[nI+3]-arrColumn[nI] for nI in range(len(arrColumn)-4)]
        for nI, nValue in enumerate(lstDiff):
            outFile.write(" ".join(map(str, [nI, nValue]))+"\n")

def writeColorData(strFilename, lstPixels, arrImage, bRB = False):
    with open(strFilename, "w") as outFile:
        arrRGB = np.array([0., 0., 0.])
        for (nRow, nCol) in lstPixels:
            if bRB:
                outFile.write(str(arrImage[nRow, nCol][0])+" "+str(arrImage[nRow, nCol][2])+"\n")
            else:
                outFile.write(" ".join(map(str, arrImage[nRow, nCol]))+" "+str(nRow)+" "+str(nCol)+"\n")
            arrRGB += arrImage[nRow, nCol]
        if len(lstPixels):
            arrRGB /= len(lstPixels)

def writeColors(arrImage, strImageFile, lstBigWells, lstSmallWells, pOverflow, bUV):
    # write colors to file for analysis
    strDir, strFile = os.path.split(strImageFile)
    strDir = os.path.join(os.path.join(strDir, "processed"), "colors")
    strSubdir = os.path.join(strDir, strFile.replace(".tiff", "").replace(" ", "_"))
    strPosDirUV = os.path.join(strDir, "positive_uv")
    strNegDirUV = os.path.join(strDir, "negative_uv")
    strPosDirVis = os.path.join(strDir, "positive_vis")
    strNegDirVis = os.path.join(strDir, "negative_vis")
    if not os.path.exists(strSubdir):
        os.mkdir(strSubdir)
    if not os.path.exists(strPosDirUV):
        os.mkdir(strPosDirUV)
    if not os.path.exists(strNegDirUV):
        os.mkdir(strNegDirUV)
    if not os.path.exists(strPosDirVis):
        os.mkdir(strPosDirVis)
    if not os.path.exists(strNegDirVis):
        os.mkdir(strNegDirVis)
    nCount = 0
    for nWellRow, lstRow in enumerate(lstBigWells):
        for nWellCol, pWell in enumerate(lstRow):
            if pWell.bPositive:
                strFilename = os.path.join(strSubdir, "big_"+str(nWellRow)+"-"+str(nWellCol)+"_p.dat")
                if bUV:
                    strSecondary = os.path.join(strPosDirUV, "big_"+str(nCount)+".dat")
                else:
                    strSecondary = os.path.join(strPosDirVis, "big_"+str(nCount)+".dat")
                while os.path.exists(strSecondary):
                    nCount += 1
                    if bUV:
                        strSecondary = os.path.join(strPosDirUV, "big_"+str(nCount)+".dat")
                    else:
                        strSecondary = os.path.join(strPosDirVis, "big_"+str(nCount)+".dat")
            else:
                strFilename = os.path.join(strSubdir, "big_"+str(nWellRow)+"-"+str(nWellCol)+"_n.dat")
                if bUV:
                    strSecondary = os.path.join(strNegDirUV, "big_"+str(nCount)+".dat")
                else:
                    strSecondary = os.path.join(strNegDirVis, "big_"+str(nCount)+".dat")
                while os.path.exists(strSecondary):
                    nCount += 1
                    if bUV:
                        strSecondary = os.path.join(strNegDirUV, "big_"+str(nCount)+".dat")
                    else:
                        strSecondary = os.path.join(strNegDirVis, "big_"+str(nCount)+".dat")
            nCount += 1
            writeColorData(strFilename, pWell.lstPixels, arrImage)
            writeColorData(strSecondary, pWell.lstPixels, arrImage, True)
            
    nCount = 0
    for nWellRow, lstRow in enumerate(lstSmallWells):                
        for nWellCol, pWell in enumerate(lstRow):
            if pWell.bPositive:
                strFilename = os.path.join(strSubdir, "small_"+str(nWellRow)+"-"+str(nWellCol)+"_p.dat")
                if bUV:
                    strSecondary = os.path.join(strPosDirUV, "small_"+str(nCount)+".dat")
                else:
                    strSecondary = os.path.join(strPosDirVis, "small_"+str(nCount)+".dat")
                while os.path.exists(strSecondary):
                    nCount += 1
                    if bUV:
                        strSecondary = os.path.join(strPosDirUV, "small_"+str(nCount)+".dat")
                    else:
                        strSecondary = os.path.join(strPosDirVis, "small_"+str(nCount)+".dat")
            else:
                strFilename = os.path.join(strSubdir, "small_"+str(nWellRow)+"-"+str(nWellCol)+"_n.dat")
                if bUV:
                    strSecondary = os.path.join(strNegDirUV, "small_"+str(nCount)+".dat")
                else:
                    strSecondary = os.path.join(strNegDirVis, "small_"+str(nCount)+".dat")
                while os.path.exists(strSecondary):
                    nCount += 1
                    if bUV:
                        strSecondary = os.path.join(strNegDirUV, "small_"+str(nCount)+".dat")
                    else:
                        strSecondary = os.path.join(strNegDirVis, "small_"+str(nCount)+".dat")
            nCount += 1
            writeColorData(strFilename, pWell.lstPixels, arrImage)
            writeColorData(strSecondary, pWell.lstPixels, arrImage, True)
                
    # overflow well
    nCount = 0
    if pWell.bPositive:
        strFilename = os.path.join(strSubdir, "overflow_p.dat")
        if bUV:
            strSecondary = os.path.join(strPosDirUV, "overflow_"+str(nCount)+".dat")
        else:
            strSecondary = os.path.join(strPosDirVis, "overflow_"+str(nCount)+".dat")
        while os.path.exists(strSecondary):
            nCount += 1
            if bUV:
                strSecondary = os.path.join(strPosDirUV, "overflow_"+str(nCount)+".dat")
            else:
                strSecondary = os.path.join(strPosDirVis, "overflow_"+str(nCount)+".dat")
    else:
        strFilename = os.path.join(strSubdir, "overflow_n.dat")            
        if bUV:
            strSecondary = os.path.join(strNegDirUV, "overflow_"+str(nCount)+".dat")
        else:
            strSecondary = os.path.join(strNegDirVis, "overflow_"+str(nCount)+".dat")
        while os.path.exists(strSecondary):
            nCount += 1
            if bUV:
                strSecondary = os.path.join(strNegDirUV, "overflow_"+str(nCount)+".dat")
            else:
                strSecondary = os.path.join(strNegDirVis, "overflow_"+str(nCount)+".dat")
    writeColorData(strFilename, pOverflow.lstPixels, arrImage)
    writeColorData(strSecondary, pOverflow.lstPixels, arrImage, True)
        
# dump image showing wells and overflow well
def writeFilled(arrImage, strImageFile, lstBigWells, lstSmallWells, pOverflow):
    lstRED = [255, 0 , 0]
    lstBLUE = [0, 0 , 255]
    arrImage = np.array(arrImage)
    for lstRow in lstBigWells:         
        for pWell in lstRow:
            for (nRow, nCol) in pWell.lstPixels:
                arrImage[nRow, nCol] = lstRED
            arrImage[pWell.nPixelRow, pWell.nPixelCol] = lstBLUE
    for lstRow in lstSmallWells:                
        for pWell in lstRow:
            for (nRow, nCol) in pWell.lstPixels:
                arrImage[nRow, nCol] = lstRED
            if pWell.nPixelRow > 0: # mark center
                arrImage[pWell.nPixelRow, pWell.nPixelCol] = lstBLUE
            else:
                arrImage[pWell.nRow, pWell.nCol] = lstBLUE
    # overflow well
    for (nRow, nCol) in pOverflow.lstPixels:
        arrImage[nRow, nCol] = lstRED

    # save image with filled in well pixels
    saveto(strImageFile, arrImage, "filled")
    
    return arrImage

# dump image showing positive well and overflow well pixels
def writeFlagged(arrImage, strImageFile, lstBigWells, lstSmallWells, pOverflow):
    lstRED = [255, 0 , 0]
    lstBLUE = [0, 0 , 255]
    arrImage = np.array(arrImage)
    for lstRow in lstBigWells:         
        for pWell in lstRow:
            for nI, (nRow, nCol) in enumerate(pWell.lstPixels):
                if pWell.lstPositive[nI]:
                    arrImage[nRow, nCol] = lstRED
            arrImage[pWell.nPixelRow, pWell.nPixelCol] = lstBLUE
    for lstRow in lstSmallWells:                
        for pWell in lstRow:
            for nI, (nRow, nCol) in enumerate(pWell.lstPixels):
                if pWell.lstPositive[nI]:
                    arrImage[nRow, nCol] = lstRED
            if pWell.nPixelRow > 0: # mark center
                arrImage[pWell.nPixelRow, pWell.nPixelCol] = lstBLUE
            else:
                arrImage[pWell.nRow, pWell.nCol] = lstBLUE
    # overflow well
    for nI, (nRow, nCol) in enumerate(pOverflow.lstPixels):
        if pOverflow.lstPositive[nI]:
            arrImage[nRow, nCol] = lstRED

    # save image with filled in well pixels
    saveto(strImageFile, arrImage, "flagged")
    
    return arrImage

# dump image showing well outlines and overflow line
def writeFramed(arrImage, strImageFile, lstBigWells, lstSmallWells, pOverflow, 
                                nOverflowLine, nOverflowStartCol, nOverflowEndCol, 
                                nBigWellHalfSize_pix, nSmallWellHalfSize_pix):
    lstRED = [255, 0 , 0]
    lstBLUE = [0, 0 , 255]
    arrImage = np.array(arrImage)
    for lstRow in lstBigWells:         # color big wells
        for pWell in lstRow:
            nTopRow = pWell.nPixelRow + nBigWellHalfSize_pix # actually bottom row
            nBottomRow = pWell.nPixelRow - nBigWellHalfSize_pix
            nLeftCol = pWell.nPixelCol - nBigWellHalfSize_pix
            nRightCol = pWell.nPixelCol + nBigWellHalfSize_pix
            for nCol in range(nLeftCol, nRightCol):
                arrImage[nTopRow, nCol] = lstRED
            for nRow in range(nBottomRow, nTopRow):
                arrImage[nRow, nLeftCol] = lstRED
            for nCol in range(nLeftCol, nRightCol):
                arrImage[nBottomRow, nCol] = lstRED
            for nRow in range(nBottomRow, nTopRow):
                arrImage[nRow, nRightCol] = lstRED
                
            arrImage[pWell.nPixelRow, pWell.nPixelCol] = lstBLUE

    for lstRow in lstSmallWells:        # color small wells
        for pWell in lstRow:
            nTopRow = pWell.nPixelRow + nSmallWellHalfSize_pix
            nBottomRow = pWell.nPixelRow - nSmallWellHalfSize_pix
            nLeftCol = pWell.nPixelCol - nSmallWellHalfSize_pix
            nRightCol = pWell.nPixelCol + nSmallWellHalfSize_pix
            for nCol in range(nLeftCol, nRightCol):
                arrImage[nTopRow, nCol] = lstRED
            for nRow in range(nBottomRow, nTopRow):
                arrImage[nRow, nLeftCol] = lstRED
            for nCol in range(nLeftCol, nRightCol):
                arrImage[nBottomRow, nCol] = lstRED
            for nRow in range(nBottomRow, nTopRow):
                arrImage[nRow, nRightCol] = lstRED

            arrImage[pWell.nPixelRow, pWell.nPixelCol] = lstBLUE
                
    # color overflow pixels above threshold
    for nCol in range(nOverflowStartCol, nOverflowEndCol):
        arrImage[nOverflowLine-1, nCol] = lstRED
        arrImage[nOverflowLine, nCol] = lstRED
        arrImage[nOverflowLine+1, nCol] = lstRED

    saveto(strImageFile, arrImage, "framed") # save image with frame around wells and level marker
    
    return arrImage

# dump image showing well outlines and overflow line with +ve tagging
def writeTagged(arrImage, strImageFile, lstBigWells, lstSmallWells, pOverflow, 
                        nOverflowLine, nOverflowStartCol, nOverflowEndCol, 
                        nBigWellHalfSize_pix, nSmallWellHalfSize_pix):
    lstRED = [255, 0 , 0]
    lstBLUE = [0, 0 , 255]
    arrImage = np.array(arrImage)
    for lstRow in lstBigWells:         # color big wells
        for pWell in lstRow:
            nTopRow = pWell.nPixelRow + nBigWellHalfSize_pix # actually bottom row
            nBottomRow = pWell.nPixelRow - nBigWellHalfSize_pix
            nLeftCol = pWell.nPixelCol - nBigWellHalfSize_pix
            nRightCol = pWell.nPixelCol + nBigWellHalfSize_pix
            for nCol in range(nLeftCol, nRightCol):
                arrImage[nTopRow, nCol] = lstRED
            for nRow in range(nBottomRow, nTopRow):
                arrImage[nRow, nLeftCol] = lstRED
            for nCol in range(nLeftCol, nRightCol):
                arrImage[nBottomRow, nCol] = lstRED
            for nRow in range(nBottomRow, nTopRow):
                arrImage[nRow, nRightCol] = lstRED
                
            if pWell.bPositive:
                nRow = nTopRow
                for nCol in range(nLeftCol+1, nRightCol):
                    arrImage[nRow, nCol-1] = lstRED
                    arrImage[nRow, nCol] = lstRED
                    nRow -= 1
                nRow = nTopRow
                for nCol in range(nRightCol, nLeftCol-1, -1):
                    arrImage[nRow, nCol-1] = lstRED
                    arrImage[nRow, nCol] = lstRED
                    nRow -= 1
                
            arrImage[pWell.nPixelRow, pWell.nPixelCol] = lstBLUE

    for lstRow in lstSmallWells:        # color small wells
        for pWell in lstRow:
            nTopRow = pWell.nPixelRow + nSmallWellHalfSize_pix
            nBottomRow = pWell.nPixelRow - nSmallWellHalfSize_pix
            nLeftCol = pWell.nPixelCol - nSmallWellHalfSize_pix
            nRightCol = pWell.nPixelCol + nSmallWellHalfSize_pix
            for nCol in range(nLeftCol, nRightCol):
                arrImage[nTopRow, nCol] = lstRED
            for nRow in range(nBottomRow, nTopRow):
                arrImage[nRow, nLeftCol] = lstRED
            for nCol in range(nLeftCol, nRightCol):
                arrImage[nBottomRow, nCol] = lstRED
            for nRow in range(nBottomRow, nTopRow):
                arrImage[nRow, nRightCol] = lstRED

            if pWell.bPositive:
                nRow = nTopRow
                for nCol in range(nLeftCol+1, nRightCol):
                    arrImage[nRow, nCol-1] = lstRED
                    arrImage[nRow, nCol] = lstRED
                    nRow -= 1
                nRow = nTopRow
                for nCol in range(nRightCol, nLeftCol-1, -1):
                    arrImage[nRow, nCol-1] = lstRED
                    arrImage[nRow, nCol] = lstRED
                    nRow -= 1

            arrImage[pWell.nPixelRow, pWell.nPixelCol] = lstBLUE
                
    # color overflow pixels above threshold
    if pOverflow.bPositive:
        arrImage[nOverflowLine-1, nCol] = lstRED
        arrImage[nOverflowLine, nCol] = lstRED
        arrImage[nOverflowLine+1, nCol] = lstRED
        nLow = nOverflowStartCol
        nHigh = nOverflowEndCol
        nLine = nOverflowLine            
        while nHigh > nLow:                
            for nCol in range(nLow, nHigh):
                arrImage[nLine, nCol] = lstRED
                arrImage[nLine+1, nCol] = lstRED
            nHigh -= 1
            nLow += 1
            nLine += 4
    else:
        for nCol in range(nOverflowStartCol, nOverflowEndCol):
            arrImage[nOverflowLine-1, nCol] = lstRED
            arrImage[nOverflowLine, nCol] = lstRED
            arrImage[nOverflowLine+1, nCol] = lstRED

    saveto(strImageFile, arrImage, "tagged") # save image with frame around wells and level marker

    return arrImage
    