# -*- coding: utf-8 -*-
import tkinter
from tkinter import ttk, filedialog
import tkinter as tk
import os
import threading
import cv2
from capturemanager import MyCaptureManager
from videoanalysis import VideoAnalysis
from PIL import Image
import PIL.Image, PIL.ImageTk
import time
import queue
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.pdfgen import canvas
import numpy
import math
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

class App:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.finish = queue.Queue()
        self.answer = ''
        self.queue_frame = queue.Queue()
        self.data_frame = []
        self.queue_angle = queue.Queue()
        self.data_angle = []
        self.queue_distance_max = queue.Queue()
        self.data_distance_max = []
        self.queue_distance = queue.Queue()
        self.data_distance = []
        self.queue_height = queue.Queue()
        self.data_height = []
        self.data_angle_fabs = []
        self.number = -1
        self.remember_start = 0
        self.remember_stop = -1
        self.films = []
        self.screenshot = []
        self.stop = True
        self.run()
        self.delay = 15
        self.window.mainloop()

    def run(self):
        leftFrame = ttk.LabelFrame(self.window, relief=tk.RIDGE)
        leftFrame.pack(side=tk.LEFT, anchor= tk.NW, expand=True)
        uploadFrame = ttk.LabelFrame(leftFrame, text="Wprowadź dane do analizy", relief=tk.RIDGE)
        uploadFrame.pack(side=tk.TOP, anchor= tk.NW, expand=True)
        loadButton = tk.Button(uploadFrame, text="Wybierz plik", command=lambda: self._openMovie(), height=1, width=35)
        loadButton.pack(expand=True, side=tkinter.LEFT)
        startButton = tk.Button(uploadFrame, text="Uruchom analizę pliku", command=lambda: self.start(), height=1, width=35)
        startButton.pack(side=tkinter.LEFT, expand=True)
        uploadFrame2 = ttk.LabelFrame(leftFrame, relief=tk.RIDGE)
        uploadFrame2.pack(side=tk.TOP, anchor= tk.NW, expand=True)
        uploadInfo = ttk.Label(uploadFrame2, text="Maksymalna odległość między otwartymi zębami w milimetrach", width=70)
        uploadInfo.pack(side=tkinter.LEFT, expand=True)
        self.scaleEntry = tk.Entry(uploadFrame2, width=30)
        self.scaleEntry.pack(side=tkinter.LEFT, expand=True)
        uploadFrame3 = ttk.LabelFrame(leftFrame, relief=tk.RIDGE)
        uploadFrame3.pack(side=tk.TOP, anchor= tk.NW, expand=True)
        uploadName = ttk.Label(uploadFrame3, text="Nazwa pliku do zapisu analizy", width=70)
        uploadName.pack(side= tkinter.LEFT, expand=True)
        self.nameEntry = tk.Entry(uploadFrame3, width=30)
        self.nameEntry.pack(side= tkinter.LEFT, expand=True)
        ### Video Frame
        self.videoFrame = ttk.LabelFrame(leftFrame, text="Analizowany film", relief=tk.RIDGE)
        self.videoFrame.pack(anchor=tk.SW, expand=True)
        self.canvas = tkinter.Canvas(self.videoFrame, width=600, height=300)
        self.canvas.pack(anchor=tkinter.NW)
        self.btn_snapshot = tkinter.Button(self.videoFrame, text="Zrzut ekranu", width=30, command=self.snapshot)
        self.btn_snapshot.pack(anchor=tkinter.CENTER, expand=True)
        ### Result Frame
        self.resultFrame = ttk.LabelFrame(self.window, text="Wyniki", relief=tk.RIDGE)
        self.resultFrame.pack(side=tk.LEFT, anchor= tk.NW, expand=True)


    def update(self):
        if not self.queue_frame.empty() or self.finish.empty():
            self.data_frame.append(self.queue_frame.get())
            self.data_angle.append(self.queue_angle.get())
            self.data_distance.append(self.queue_distance.get())
            self.data_distance_max.append(self.queue_distance_max.get())
            self.data_height.append(self.queue_height.get())
            self.number = len(self.data_frame) - 1
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(cv2.cvtColor(self.data_frame[-1], cv2.COLOR_RGB2BGR)))
            self.canvas.create_image(300, 150, image=self.photo, anchor=tkinter.CENTER)
            self.canvas.pack()
            self.window.after(self.delay, self.update)
        else:
            self.thread.join()
            self.window.after(self.delay, self.add_buttons())

    def snapshot(self):
        if len(self.data_frame) > 0:
            if self.nameEntry.get():
                name = self.nameEntry.get() + "-frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg"
            else:
                name = "frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg"
            cv2.imwrite(name, self.data_frame[self.number])
            self.screenshot.append(name)

    def add_buttons(self):
        self.number = 0
        btn_start_video = tkinter.Button(self.videoFrame, text="Włącz film", width=30, height=1, command=lambda: self.start_video())
        btn_start_video.pack(anchor=tkinter.CENTER, expand=True)
        btn_stop_video = tkinter.Button(self.videoFrame, text="Wyłącz film", width=30, height=1, command=lambda: self.video_stop())
        btn_stop_video.pack(anchor=tkinter.CENTER, expand=True)
        btn_start_analyze = tkinter.Button(self.videoFrame, text="Włącz analizę filmu", width=30, height=1, command=lambda: self.start_recording_video())
        btn_start_analyze.pack(anchor=tkinter.CENTER, expand=True)
        btn_stop_analyze = tkinter.Button(self.videoFrame, text="Wyłącz analizę filmu", width=30, height=1, command=lambda: self.stop_recording_video())
        btn_stop_analyze.pack(anchor=tkinter.CENTER, expand=True)
        if self.scaleEntry.get():
            unit = int(self.scaleEntry.get())/max(self.data_distance_max)
            id = numpy.argmax(self.data_distance_max)
            self.compare = self.data_height[id] * unit
            for i in range(1, len(self.data_distance)):
                self.data_distance[i] = self.data_distance[i] * self.compare/self.data_height[i]
            fig, axs = self.create_graph(False, 0, len(self.data_angle))
        else:
            fig, axs = self.create_graph(True, 0, len(self.data_angle))
        self.data_angle_fabs = [math.fabs(a) for a in self.data_angle]
        self.resultAngleLabel = ttk.Label(self.resultFrame, text="Wynik w kątach " + str(round(max(self.data_angle_fabs),3)),
                                          width=50)
        self.resultAngleLabel.pack(anchor=tk.NW, expand=True)
        text = "Wynik w milimetrach "
        if self.scaleEntry.get():
            text = "Wynik w milimetrach " + str(round(max(self.data_distance), 3))
        self.resultMiliLabel = ttk.Label(self.resultFrame, text=text, width=50)
        self.resultMiliLabel.pack(anchor=tk.NW, expand=True)
        pdfButton = tk.Button(self.resultFrame, text="Zapisz analizę", command=lambda: self.create_pdf(), height=1,
                              width=35)
        pdfButton.pack(anchor=tk.SW, expand=True)
        self.resultCanvas = FigureCanvasTkAgg(fig, master=self.resultFrame)
        self.resultCanvas.get_tk_widget().pack(anchor=tk.SW)
        self.resultCanvas.draw()



    def start_video(self):
        if self.number == len(self.data_frame):
            self.number = 0
        self.stop = True
        self.thread2 = threading.Thread(target=self.update2, args=(), daemon=True)
        self.thread2.start()

    def update2(self):
        if self.number != len(self.data_frame) and self.stop:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(cv2.cvtColor(self.data_frame[self.number], cv2.COLOR_RGB2BGR)))
            self.canvas.create_image(300, 150, image=self.photo, anchor=tkinter.CENTER)
            self.canvas.pack()
            self.number += 1
            self.window.after(self.delay, self.update2)
        else:
            if self.remember_start != 0:
                self.stop_recording_video()

    def video_stop(self):
        self.stop = False

    def start_recording_video(self):
        self.remember_start = self.number
        self.stop = True
        self.start_video()


    def stop_recording_video(self):
        self.remember_stop = self.number
        if self.remember_start < self.remember_stop:
            self.films.append([self.remember_start, self.remember_stop])
            self.remember_start = 0
            self.remember_stop = 0
            self.show_graph()

    def show_graph(self):
        if self.scaleEntry.get():
            fig, axs = self.create_graph(False, self.films[-1][0], self.films[-1][1])
            self.resultMiliLabel['text'] = "Wynik w milimetrach " + str(round(max(self.data_angle_fabs[self.films[-1][0]:self.films[-1][1]]),3))
            self.resultMiliLabel.pack(anchor=tk.NW)
        else:
            fig, axs = self.create_graph(True,  self.films[-1][0], self.films[-1][1])
        self.resultCanvas.get_tk_widget().destroy()
        self.resultCanvas = FigureCanvasTkAgg(fig, master=self.resultFrame)
        self.resultCanvas.get_tk_widget().pack(anchor=tk.SW)
        self.resultCanvas.draw()
        self.resultAngleLabel['text'] = "Wynik w kątach " + str(round(max(self.data_angle_fabs[self.films[-1][0]:self.films[-1][1]]),3))
        self.resultAngleLabel.pack()
        self.window.after(self.delay)

    def create_graph(self, one, start, stop):
        y = [a for a in range(len(self.data_angle))]
        if one:
            fig = plt.Figure()
            axs = fig.add_subplot(111)
            axs.plot(y[start:stop], self.data_angle[start:stop],color='blue')
            axs.invert_yaxis()
            axs.set_title("Odchylenie", fontsize=12)
            axs.set_ylabel("Kąty", fontsize=8)
            axs.yaxis.grid(color='gray', linestyle='dashed')
        else:
            fig, axs = plt.subplots(2)
            fig.suptitle('Odchylenie')
            axs[0].plot(y[start:stop], self.data_angle[start:stop])
            axs[0].yaxis.grid(color='gray', linestyle='dashed')
            axs[0].set_ylabel("Kąty", fontsize=8)
            axs[1].plot(y[start:stop], self.data_distance[start:stop])
            axs[1].yaxis.grid(color='gray', linestyle='dashed')
            axs[1].set_ylabel("Milimetry", fontsize=8)
        return fig, axs


    def _openMovie(self):
        openFileTypes = [('MP4', '.mp4')]
        self.answer = filedialog.askopenfilename(parent=self.window, initialdir=os.getcwd(), title="Please select a file", filetypes=openFileTypes)
        print("Opening document: " + self.answer)


    def start(self):
        if self.answer != '':
            self.finish = queue.Queue()
            self.queue_frame = queue.Queue()
            self.data_frame = []
            self.queue_angle = queue.Queue()
            self.data_angle = []
            self.queue_distance_max = queue.Queue()
            self.data_distance_max = []
            self.queue_distance = queue.Queue()
            self.data_distance = []
            self.queue_height = queue.Queue()
            self.data_height = []
            self.films = []
            self.screenshot = []
            self.thread = threading.Thread(target=self.create_thread, args=(), daemon=True)
            self.thread.start()
            self.update()

    def create_thread(self):
        capture = MyCaptureManager(cv2.VideoCapture(self.answer), self.queue_frame)
        VideoAnalysis(capture, self.finish, self.queue_angle, self.queue_distance, self.queue_distance_max, self.queue_height).run()

    def create_pdf(self):
        if self.nameEntry.get():
            pdf = canvas.Canvas(self.nameEntry.get() + '.pdf', pagesize=A4)
            width, height = A4
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            pdf.setFont("Arial", 14)
            minus = 40
            pdf.drawString(40, (height - minus), 'Wynik analizy filmu \"' + self.answer.split('/')[-1] + '\".')
            minus += 40
            pdf.drawString(40, (height - minus), 'Wynik w kątach ' + str(round(max(self.data_angle_fabs), 3)) + '.')
            minus += 40
            if self.scaleEntry.get():
                pdf.drawString(40, (height - minus), 'Wynik w milimetrach ' + str(round(max(self.data_distance), 3)) + '.')
                minus += 40
            if self.scaleEntry.get():
                drawing = self.create_graph_pdf(False, 0, len(self.data_angle))
            else:
                drawing = self.create_graph_pdf(True, 0, len(self.data_angle))
            minus += drawing.height
            renderPDF.draw(drawing, pdf, 40, (height - minus))
            minus += 40
            for i in range(len(self.screenshot)):
                im = Image.open(self.screenshot[i])
                if minus + im.size[1] < height:
                    minus += im.size[1]
                    pdf.drawImage(self.screenshot[i], 40, (height - minus))
                    minus += 40
                else:
                    pdf.showPage()
                    minus = 40 + im.size[1]
                    pdf.drawImage(self.screenshot[i], 40, (height - minus))
                    minus += 40
            for i in range(len(self.films)):
                pdf.showPage()
                pdf.setFont("Arial", 14)

                minus = 40
                pdf.drawString(40, (height - minus),
                               'Wynik w kątach ' + str(round(max(self.data_angle_fabs[self.films[i][0]:self.films[i][1]]), 3)) + '.')
                minus += 40
                if self.scaleEntry.get():
                    drawing = self.create_graph_pdf(False, self.films[i][0], self.films[i][1])
                    pdf.drawString(40, (height - minus),
                                   'Wynik w milimetrach ' + str(round(max(self.data_distance[self.films[i][0]:self.films[i][1]]), 3)) + '.')
                    minus += 40
                else:
                    drawing = self.create_graph_pdf(True, self.films[i][0], self.films[i][1])
                minus += drawing.height
                renderPDF.draw(drawing, pdf, 40, (height - minus))
            pdf.showPage()
            pdf.save()

    def create_graph_pdf(self, one, start, stop):
        fig, axs = self.create_graph(one, start, stop)
        imgdata = BytesIO()
        fig.savefig(imgdata, format='svg')
        imgdata.seek(0)
        drawing = svg2rlg(imgdata)
        return drawing


if __name__ == "__main__":
    program = App(tkinter.Tk(), "Tkinter and OpenCV")
