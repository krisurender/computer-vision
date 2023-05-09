
import cv2
import numpy as np
import time
from cvzone.HandTrackingModule import HandDetector
import pyautogui

#volume control
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

"""Width and Height of camera """
wcam, hcam = 640, 480

capture = cv2.VideoCapture(0)
capture.set(3, wcam) # 3 means width
capture.set(4, hcam) # 4 means height
ptime = 0
plocx, plocy = 0, 0
clocx, clocy = 0, 0

detector = HandDetector(maxHands=2, detectionCon=0.8, minTrackCon=0.8)
wscr, hscr = pyautogui.size()


devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volrange  = volume.GetVolumeRange()

minVol = volrange[0]
maxVol = volrange[1]

vol = 0
volBar = 400
volPercentage = 0
area = 0
colorVol = (255, 0, 0)
frameR = 50  #frame reduction

pyautogui.FAILSAFE = False
while True:
    sucess, img = capture.read()
    img = cv2.flip(img, 1)

    """Find hands"""
    hands, img = detector.findHands(img, draw=True,flipType=False)
    lmlist, bbox = detector.findPosition(img,draw=True)

    if len(lmlist)!= 0:

        #filter based on size
        area = (bbox[2]-bbox[0])*(bbox[3]-bbox[1])//100
        hand = hands[0]
        handtype = hands[0].get('type')

        if handtype == 'Left':
            if 350 < area < 1000:

                """Find Distance between index and thumb"""
                # index is 8 and thumb is 4
                x1, y1 = lmlist[4][1], lmlist[4][2]
                x2, y2 = lmlist[8][1], lmlist[8][2]
                length, lineInfo, img = detector.findDistance((x1, y1), (x2, y2), img)

                """Convert volume"""
                # Hand range was 50 to 200
                # volume range was -96 to 0

                vol = np.interp(length, [50, 200], [minVol, maxVol])
                volBar = np.interp(length, [50, 180], [400, 100])
                volPercentage = np.interp(length, [50, 180], [0, 100])

                """Reducing resolution for smoother use"""
                smoothness = 10
                volPercentage = smoothness * round(volPercentage/smoothness)

                """Check fingers up"""
                fingers = detector.fingersUp(hands[0])

                """When picky finger is down"""
                if not fingers[4]:
                    volume.SetMasterVolumeLevelScalar(volPercentage/100, None)
                    cv2.circle(img, center=(lineInfo[4], lineInfo[5]), radius=15,
                               color=(0, 255, 255), thickness=cv2.FILLED)
                    colorVol = (0, 255,0)
                else:
                    colorVol = (255, 0, 0)

            else:
                print("Left Hand is too far away ")

    """MOUSE CONTROL"""
    if hands:
        hand = hands[0]
        handtype = hands[0].get('type')

        if handtype == 'Right':
            cv2.rectangle(img, pt1=(frameR, frameR), pt2=(wcam - frameR, hcam - frameR), color=(255, 255, 0),
                          thickness=2)

            smoothness = 6.5
            if len(lmlist) != 0:
                #get the index and middle finger tip
                x1, y1 = lmlist[8][1], lmlist[8][2]
                x2, y2 = lmlist[12][1], lmlist[12][2]

                #check which finger are up
                fingers = detector.fingersUp(hand)
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100
                cv2.rectangle(img, pt1=(frameR, frameR), pt2=(wcam-frameR, hcam-frameR), color=(255, 255, 0), thickness=3)

                #index and middle finger moving
                if fingers[1] == 1 and fingers [2] == 0:
                    #convert coordinates
                    x3 = np.interp(x1,(frameR, wcam-frameR),(0, wscr))
                    y3 = np.interp(y1,(frameR, hcam-frameR),(0, hscr))

                    #smooth the movement
                    clocx = plocx+(x3-plocx)/smoothness
                    clocy = plocy+(y3-plocy)/smoothness

                    #move mouse
                    pyautogui.moveTo(clocx,clocy)
                    cv2.circle(img, center=(x1, y1), radius=15, color=(0, 255, 255), thickness=cv2.FILLED)
                    plocx, plocy = clocx, clocy

                    #if index is down click
                elif fingers[1:] == [0, 0, 0, 0]:
                    cv2.putText(img, text='click', org=(500, 100), color=(0, 255, 0),
                                fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=3, thickness=2)
                    cv2.circle(img, center=(x1, y1), radius=15, color=(0, 0, 255), thickness=cv2.FILLED)  # index
                    pyautogui.click()

                elif fingers[1] == 1 and fingers [2] == 1:
                    length, lineInfo, img = detector.findDistance((x1, y1), (x2, y2), img)

                    if length < 30:
                        cv2.putText(img, text='Up scroll',org=(400, 100), color=(0, 255, 0), fontFace=cv2.FONT_HERSHEY_PLAIN, fontScale=3, thickness=2)
                        pyautogui.scroll(300)
                    elif length > 60:
                        cv2.putText(img, text='down scroll', org=(400, 100), color=(0, 255, 0), fontFace=cv2.FONT_HERSHEY_PLAIN,
                                    fontScale=3, thickness=2)
                        pyautogui.scroll(-300)

    """Drawing"""
    cv2.rectangle(img, pt1=(50, 100), pt2=(85, 400), color=(0, 255, 0), thickness=3)
    cv2.rectangle(img, pt1=(50, int(volBar)), pt2=(85, 400), color=(0, 255, 0), thickness=cv2.FILLED)
    cv2.putText(img, text=f'Volume:{int(volPercentage)}%', org=(40, 450), fontFace=cv2.FONT_HERSHEY_PLAIN,
                fontScale=1, color=(255, 0, 0), thickness=1)

    """Frame rate"""
    ctime = time.time()
    fps = 1 / (ctime - ptime)
    ptime = ctime

    cVol = (volume.GetMasterVolumeLevelScalar()*100)
    cv2.putText(img, text=f'FPS:{int(fps)}', org=(20,20), fontFace=cv2.FONT_HERSHEY_PLAIN,
                fontScale=1, color=(255, 0, 0), thickness=2)
    cv2.putText(img, text=f'Volume set:{int(cVol)}', org=(400, 20), fontFace=cv2.FONT_HERSHEY_PLAIN,
                fontScale=1, color=colorVol, thickness=2)

    cv2.imshow("img", img)
    cv2.waitKey(1)

    if cv2.waitKey(10) == ord('q'):
        break

