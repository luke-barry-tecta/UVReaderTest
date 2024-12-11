# these are approximate numbers based on measurements from Eric's
# QuantiTray carrier SolidWorks (.STL) file. Wells are positioned on
# their centre, as the CoM of a blob of pixels is easier to define than
# the corner. Physical layout is important both for guiding the analysis
# algorithm and for unwarping the image via the Tsai model. These
# are physical properties of the tray, so are fixed, unlike the pixels
# properties and scale, which are image-dependent.

fBigWellSpacing_mm = 21.3 # mm, centre-to-centre
fBigWellSize_mm = 13.8 # mm

fSmallWellSpacing_mm = 11.8 # mm, centre-to-centre
fSmallWellSize_mm = 6.5 # mm
fFirstSmallWellColumn_mm = -64.5 # mm, relative to center of origin cells
fFirstSmallWellRow_mm = 1.0 # mm, relative to center of origin cells

fOverflowXStart = 27.0 # mm (relative to last column of big wells)
fOverflowXEnd = 42.0 # mm

# parameters for analyzing the image histogram to find the threshold
nLowerThreshold = 100 # removes background pixels
nSinceThreshold = 25 # grey levels we have to pass without a new low before calling it

nHighThresholdLimit = 250 # if threshold exceeds this, use BG multiplier to get threshold
fBackgroundMutltiplier = 3

# THIS IS THE RESOLUTION OF THE ANALYZED IMAGES
# if it changes, various numbers below need to change
nDefaultTargetWidth = 640 # pixels
nTargetWidth = 640 # pixels (has been tested with 960, which takes twice as long for NO ADVANTAGE)

# PIXELS: these values have to be change if image deviates from 640x480
nBGWidth = int(20*nTargetWidth/nDefaultTargetWidth)
nBGShift = int(6*nTargetWidth/nDefaultTargetWidth)
nBGStartRow = int(40*nTargetWidth/nDefaultTargetWidth)
nBGBoundary = int(30*nTargetWidth/nDefaultTargetWidth)
nBGWellThreshold = 100 # gray level

# if overflow well detection fails, use this as approximate center
nOverflowColOffset = int(56*nTargetWidth/nDefaultTargetWidth)

nRectangleStartThreshold = 30000 # used to find basic position of well layout
nRectangleEndThreshold = 50000 # used to find basic position of well layout

nWellSizeThreshold = int(100*nTargetWidth/nDefaultTargetWidth) # number of pixels to count well in regularization

fWellFactorThreshsold = 0.8
fWellFactorReduction = 0.99

fK = 0.1322595 # Tsai model unwarping parameter for -2 cm images
nPadding = 20 # padding around unwarped images
