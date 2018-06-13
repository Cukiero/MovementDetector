from Tkinter import *
import Tkinter as tk
import tkFileDialog
import cv2
from PIL import Image, ImageTk
import multiAnalyzer
import datetime

class Application:
    def __init__(self, analyzer):
        self.root = tk.Tk()
        self.root.bind('<Escape>', lambda e: self.root.quit())
        self.root.title('Movement Detector')
        self.video_area = tk.LabelFrame(self.root, width=800, height=600)
        self.video_area.pack(side=LEFT, fill=tk.BOTH, expand=True)
        self.video_panel = tk.Label(self.video_area)
        self.video_panel.place(x=0, y=0, anchor=NW)
        self.menu = tk.Frame(self.root, bg='darkgrey')
        self.menu.pack(side=LEFT, fill=tk.Y, expand=False)
        self.load_button = tk.Button(self.menu, text='Choose file', height=2, width=20, command=self.load_file)
        self.load_button.pack(fill=tk.BOTH, pady=5, padx=10)
        self.camera_button = tk.Button(self.menu, text='Camera', height=2, width=20, command=self.get_camera)
        self.camera_button.pack(fill=tk.BOTH, pady=5, padx=10)
        self.play_button = tk.Button(self.menu, text='Play', height=2, width=20, command=self.toggle_video_playback)
        self.play_button.pack(fill=tk.BOTH, pady=30, padx=10)
        self.analysis_button = tk.Button(self.menu, text='Enable', height=2, width=20, command=self.toggle_analysis)
        self.analysis_button.pack(side=BOTTOM, fill=tk.BOTH, pady=5, padx=10)
        self.analysis_state = tk.Label(self.menu, text='Analysis\nDisabled', font=('Courier', 15), bg='darkgrey', fg='red', width=20)
        self.analysis_state.pack(side=BOTTOM, fill=tk.BOTH, pady=5, padx=10)

        self.analyzer = analyzer
        self.fps_number = 0
        self.time_between_frames = 0
        self.is_camera = False
        self.permission_to_analyze = False
        self.is_blocked = True
        self.path = 0
        self.video_playing = False
        self.video_loaded = False
        self.frame_delay = 30
        self.delay_count = 0
        self.count_frames = False
        self.cam_anl_delay = 5
        self.save_path = 'recordings/'
        self.video_height = 600
        self.video_width = 800

        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.out = cv2.VideoWriter()
        self.cap = cv2.VideoCapture(0)

    def video_cap(self):
        if(self.cap.isOpened()):	
       	    self.cap.release()
        self.cap = cv2.VideoCapture(self.path)
        self.out.release()
        self.count_frames = False

        if(self.is_camera):
            self.path = 0
            self.is_blocked = True
            ret, frame = self.cap.read()
            self.video_height, self.video_width, channels = frame.shape
            self.video_area['height'] = self.video_height
            self.video_area['width'] = self.video_width
            self.root.after(50, self.get_frame)
        else:
            ret, frame = self.cap.read()
            self.video_height, self.video_width, channels = frame.shape
            self.video_area['height'] = self.video_height
            self.video_area['width'] = self.video_width
            self.show_frame(frame)

    def load_file(self):
        path_to_file = tkFileDialog.askopenfilename(title='Select video', filetypes=(('mp4 files', '*.mp4'), (('All files'), '*.*')))
        print(path_to_file)
        if len(path_to_file) > 0:
            self.is_camera = False
            self.enable_analysis()
            self.path = path_to_file
            self.video_loaded = True
            self.pause_video()
            self.root.after(100, self.video_cap)
        else:
            return

    def get_camera(self):
        self.path = 0
        self.is_camera = True
        self.cap.release()
        self.video_loaded = False
        self.pause_video()
        self.disable_analysis()
        self.play_button['text'] = 'No use for camera'
        self.root.after(100, self.video_cap)

    def get_frame(self):
        if not(self.is_camera) and not(self.video_playing):
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        if (self.permission_to_analyze):
            (movement, frame) = self.analyzer.analyze_frame(frame)
            if movement is True:
                if self.out.isOpened():
                    self.out.write(frame)
                else:
                    filename = self.save_path+datetime.datetime.now().strftime('%m%d-%H%M%S')+'.avi'
                    self.out.open(filename, self.fourcc, 15.0, (self.video_width, self.video_height))
                    self.count_frames = True
                self.delay_count = 0
            else:
                if self.out.isOpened() and self.delay_count >= self.frame_delay:
                    self.out.release()
                    self.count_frames = False
                if self.count_frames == True:
                    self.out.write(frame)
                    self.delay_count += 1
        self.show_frame(frame)
        self.root.after(10, self.get_frame)

    def show_frame(self, frame):
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_panel.imgtk = imgtk
        self.video_panel.configure(image=imgtk)

    def toggle_video_playback(self):
        if self.video_loaded:
            if self.video_playing:
                self.pause_video()
            else:
                self.play_video()

    def play_video(self):
        self.video_playing = True
        self.play_button['text'] = 'Pause'
        self.root.after(100, self.get_frame)

    def pause_video(self):
        self.play_button['text'] = 'Play'
        self.video_playing = False

    def toggle_analysis(self):
        if self.is_camera:
            if self.permission_to_analyze:
                self.disable_analysis()
            else:
                for i in range(self.cam_anl_delay):
                    self.root.after(i*1000, self.counter_number, self.cam_anl_delay - i)
                self.root.after(self.cam_anl_delay*1000, self.enable_analysis)
        else:
            if self.permission_to_analyze:
                self.disable_analysis()
            else:
                self.enable_analysis()

    def counter_number(self, number):
        self.analysis_state['text'] = number

    def enable_analysis(self):
        self.analyzer.__init__()
        self.permission_to_analyze = True
        self.analysis_button['text'] = 'Disable'
        self.analysis_state['text'] = 'Analysis\nEnabled'
        self.analysis_state['fg'] = 'darkgreen'

    def disable_analysis(self):
        self.permission_to_analyze = False
        self.out.release()
        self.count_frames = False
        self.analysis_button['text'] = 'Enable'
        self.analysis_state['text'] = 'Analysis\nDisabled'
        self.analysis_state['fg'] = 'red'

if __name__ == '__main__':
    analyzer = multiAnalyzer.Analyzer();
    app = Application(analyzer)
    app.root.mainloop()
    app.cap.release()
    app.out.release()
    cv2.destroyAllWindows()
