import cv2
import datetime
from multiprocessing import Pool, cpu_count
import numpy as np

class Analyzer:
    def __init__(self):
        self.first_frame = None
        self.first_frame_parts = []
        self.process_count = cpu_count()
        self.pool = None
        self.once = False
        self.pool = Pool(self.process_count)

    def analyze_frame(self, frame):
        text = "No movement"
        movement = False

        height, width, channels = frame.shape

        height_step = height / self.process_count
        height_values = []
        height_values.append(0)

        for i in range(self.process_count - 1):
            height_values.append(height_values[i] + height_step)

        height_values.append(height + 1)

        if self.first_frame is None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            self.first_frame = gray

            for i in range(self.process_count):
                self.first_frame_parts.append(gray[height_values[i] : (height_values[i+1] - 1), 0 : width])

            return (movement, frame)

        frame_parts = []
        for i in range(self.process_count):
            frame_parts.append(frame[height_values[i]: (height_values[i + 1] - 1), 0: width])

        comm_data = []
        for i in range(self.process_count):
            comm_data.append([self.first_frame_parts[i],  frame_parts[i]])

        edited_parts = []
        edited_parts = self.pool.map(process_analyze, comm_data)

        edited = edited_parts[0]
        
        for i in range(self.process_count - 1):
            edited = np.concatenate((edited, edited_parts[i + 1]), axis=0)

        (_, contours, _) = cv2.findContours(edited.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            if cv2.contourArea(c) < 5000:
                continue
            movement = True
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = "Movement"

        cv2.putText(frame, "Status: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        return (movement, frame)

def process_analyze(frames):
    gray = cv2.cvtColor(frames[1], cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    frameDelta = cv2.absdiff(frames[0], gray)
    edited = cv2.threshold(frameDelta, 60, 255, cv2.THRESH_BINARY)[1]
    edited = cv2.dilate(edited, None, iterations=2)

    return edited
