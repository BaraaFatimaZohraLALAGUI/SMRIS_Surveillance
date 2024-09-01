import cv2 as cv

# backSub_KNN = cv.createBackgroundSubtractorKNN(dist2Threshold = 4.0, detectShadows = False)
backSub_MOG2 = cv.createBackgroundSubtractorMOG2(history = 200, detectShadows = False, varThreshold=300)
backSub_MOG = cv.bgsegm.createBackgroundSubtractorMOG(history=200, nmixtures=3, backgroundRatio=.95, noiseSigma=10)

bg = cv.imread ('BG.JPG')
fg = cv.imread ('FG.JPG')

fgMask_MOG = backSub_MOG.apply(bg)
fgMask_MOG = backSub_MOG.apply(fg)

fgMask_MOG2 = backSub_MOG2.apply(bg)
fgMask_MOG2 = backSub_MOG2.apply(fg)

# fgMask_KNN = backSub_KNN.apply(bg)
# fgMask_KNN = backSub_KNN.apply(fg)

cv.imshow('FG Mask MOG', fgMask_MOG)
cv.imshow('FG Mask MOG2', fgMask_MOG2)
# cv.imshow('FG Mask KNN', fgMask_KNN)
