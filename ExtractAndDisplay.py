#!/usr/bin/env python3

import threading
import cv2
import numpy as np
import base64
import queue

class TObject:
    def __init__(self):
        self.queue = queue.Queue()#here we use a queue as our queue in the object
        self.full = threading.Semaphore(0)#semaphore for keeping track if our queue is full
        self.empty = threading.Semaphore(10)#semaphore for keeping track if we have an empty queue
        self.lock = threading.Lock()#lock to keep our threads safe
    def PUT(self, item):
        self.empty.acquire()#we decrement our empty semaphore
        self.lock.acquire()#lock so no one else can put while we are putting
        self.queue.put(item)#put our frame
        self.lock.release()#unlock
        self.full.release()#full semaphore is incremented
    def GET(self):
        self.full.acquire()#full semaphore is decremented
        self.lock.acquire()#lock so no one else can get while we are getting
        frame = self.queue.get()#get our frame
        self.lock.release()#unlock
        self.empty.release()#empty semaphore is decremented
        return frame#return our frame

def extractFrames(fileName, outputBuffer, maxFramesToLoad=9999):
    # Initialize frame count 
    count = 0

    # open video file
    vidcap = cv2.VideoCapture(fileName)

    # read first image
    success,image = vidcap.read()
    
    print(f'Reading frame {count} {success}')
    while success and count < maxFramesToLoad:
        # get a jpg encoded frame
        success, jpgImage = cv2.imencode('.jpg', image)

        #encode the frame as base 64 to make debugging easier
        jpgAsText = base64.b64encode(jpgImage)

        # add the frame to the buffer
        outputBuffer.PUT(image)#place frame in our queue

        success,image = vidcap.read()
        print(f'Reading frame {count} {success}')
        count += 1

    print('Frame extraction complete')

def convertFrames(inputBuffer, outputBuffer):
    # initialize frame count
    count = 0
    inputFrame = inputBuffer.GET()#get from original frames
    while inputFrame is not None and count < 72:
        print(f'Converting frame {count}')
        
        # convert the image to grayscale
        grayscaleFrame = cv2.cvtColor(inputFrame, cv2.COLOR_BGR2GRAY)
        count += 1

        #queue next frame after converting
        outputBuffer.PUT(grayscaleFrame)#put converted frame in our queue

            
        # load the next frame
        inputFrame = inputBuffer.GET()#get from original frames
    print("Done converting")

def displayFrames(inputBuffer):
    # initialize frame count
    count = 0

    frame = inputBuffer.GET()#get b&w frame
    # go through each frame in the buffer until the buffer is empty
    while frame is not None and count < 72:
        print(f'Displaying frame {count}')        

        # display the image in a window called "video" and wait 42ms
        # before displaying the next frame
        cv2.imshow('Video', frame)
        if cv2.waitKey(42) and 0xFF == ord("q"):
            break
        count += 1

        # get the next frame
        frame = inputBuffer.GET()
    print('Finished displaying all frames')
    # cleanup the windows
    cv2.destroyAllWindows()

# filename of clip to load
filename = 'clip.mp4'

# shared queue  
extractionQueue = TObject()

# temporary queue
convertQueue = TObject()

t = threading.Thread(target = extractFrames, name = 'extract', args=(filename, extractionQueue, 72))
t.start()

t2 = threading.Thread(target = convertFrames, name = 'convert', args=(extractionQueue, convertQueue))
t2.start()

t3 = threading.Thread(target = displayFrames, name = 'display', args=(convertQueue,))
t3.start()



