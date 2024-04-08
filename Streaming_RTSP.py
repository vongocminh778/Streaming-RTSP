# import the required packages.
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, \
    QLabel, QGridLayout, QScrollArea, QSizePolicy
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPalette
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QEvent, QObject
from PyQt5 import QtCore
import sys

sys.OpenCV_LOADER_DEBUG = True

class CaptureIpCameraFramesWorker(QThread):
    # Signal emitted when a new image or a new frame is ready.
    ImageUpdated = pyqtSignal(QImage)

    def __init__(self, url) -> None:
        super(CaptureIpCameraFramesWorker, self).__init__()
        # Declare and initialize instance variables.
        self.url = url
        self.__thread_active = True
        self.fps = 0
        self.__thread_pause = False

    def run(self) -> None:
        # Capture video from a network stream.
        cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
        # Get default video FPS.
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        print(self.fps)
        # If video capturing has been initialized already.
        if cap.isOpened():
            # While the thread is active.
            while self.__thread_active:
                if not self.__thread_pause:
                    # Grabs, decodes and returns the next video frame.
                    ret, frame = cap.read()
                    # If frame is read correctly.
                    if ret:
                        # print(cv2.getBuildInformation())
                        # Get the frame height, width and channels.
                        height, width, channels = frame.shape
                        # print(frame.shape)
                        # Calculate the number of bytes per line.
                        bytes_per_line = width * channels
                        # Convert image from BGR (cv2 default color format) to RGB (Qt default color format).
                        cv_rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        # Convert the image to Qt format.
                        qt_rgb_image = QImage(cv_rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                        # Scale the image.
                        # NOTE: consider removing the flag Qt.KeepAspectRatio as it will crash Python on older Windows machines
                        # If this is the case, call instead: qt_rgb_image.scaled(1280, 720)
                        qt_rgb_image_scaled = qt_rgb_image.scaled(1280, 720, Qt.KeepAspectRatio)  # 720p
                        # Emit this signal to notify that a new image or frame is available.
                        self.ImageUpdated.emit(qt_rgb_image_scaled)
                    else:
                        break
        # When everything done, release the video capture object.
        cap.release()
        # Tells the thread's event loop to exit with return code 0 (success).
        self.quit()

    def stop(self) -> None:
        self.__thread_active = False

    def pause(self) -> None:
        self.__thread_pause = True

    def unpause(self) -> None:
        self.__thread_pause = False


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super(MainWindow, self).__init__()

        # rtsp://<Username>:<Password>@<IP Address>:<Port>/cam/realmonitor?channel=1&subtype=0
        self.url_1 = "rtsp://192.168.55.1:8554/vio"

        # Create an instance of a QLabel class to show camera 1.
        self.camera_1 = QLabel()
        self.camera_1.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.camera_1.setScaledContents(True)
        self.camera_1.setObjectName("Camera_1")

        # Create an instance of a QScrollArea class to scroll camera 1 image.
        self.QScrollArea_1 = QScrollArea()
        self.QScrollArea_1.setBackgroundRole(QPalette.Dark)
        self.QScrollArea_1.setWidgetResizable(True)
        self.QScrollArea_1.setWidget(self.camera_1)

        # Set the UI elements for this Widget class.
        self.__SetupUI()

        # Create an instance of CaptureIpCameraFramesWorker.
        self.CaptureIpCameraFramesWorker_1 = CaptureIpCameraFramesWorker(self.url_1)
        self.CaptureIpCameraFramesWorker_1.ImageUpdated.connect(lambda image: self.ShowCamera1(image))

        # Start the thread getIpCameraFrameWorker_1.
        self.CaptureIpCameraFramesWorker_1.start()

    def __SetupUI(self) -> None:
        # Create an instance of a QGridLayout layout.
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self.QScrollArea_1, 0, 0)

        # Create a widget instance.
        self.widget = QWidget(self)
        self.widget.setLayout(grid_layout)

        # Set the central widget.
        self.setCentralWidget(self.widget)
        self.setMinimumSize(640, 480)
        self.showMaximized()
        self.setStyleSheet("QMainWindow {background: 'black';}")
        self.setWindowIcon(QIcon(QPixmap("camera_2.png")))
        # Set window title.
        self.setWindowTitle("IP Camera System")

    @QtCore.pyqtSlot()
    def ShowCamera1(self, frame: QImage) -> None:
        self.camera_1.setPixmap(QPixmap.fromImage(frame))

    # Override method for class MainWindow.
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """
        Method to capture the events for objects with an event filter installed.
        :param source: The object for whom an event took place.
        :param event: The event that took place.
        :return: True if event is handled.
        """
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            if source.objectName() == 'Camera_1':
                if self.list_of_cameras_state["Camera_1"] == "Normal":
                    self.QScrollArea_2.hide()
                    self.QScrollArea_3.hide()
                    self.QScrollArea_4.hide()
                    self.list_of_cameras_state["Camera_1"] = "Maximized"
                else:
                    self.QScrollArea_2.show()
                    self.QScrollArea_3.show()
                    self.QScrollArea_4.show()
                    self.list_of_cameras_state["Camera_1"] = "Normal"
            else:
                return super(MainWindow, self).eventFilter(source, event)
            return True
        else:
            return super(MainWindow, self).eventFilter(source, event)

    # Overwrite method closeEvent from class QMainWindow.
    def closeEvent(self, event) -> None:
        # If thread getIpCameraFrameWorker_1 is running, then exit it.
        if self.CaptureIpCameraFramesWorker_1.isRunning():
            self.CaptureIpCameraFramesWorker_1.quit()
        # Accept the event
        event.accept()


def main() -> None:
    # Create a QApplication object.
    app = QApplication(sys.argv)
    # Create an instance of the class MainWindow.
    window = MainWindow()
    # Show the window.
    window.show()
    # Start Qt event loop.
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
