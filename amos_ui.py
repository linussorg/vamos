import sys, os, datetime, cv2, json
import xml.etree.ElementTree as ET
import openpyxl as xl
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QSpacerItem, QPushButton, QGroupBox, QHBoxLayout, QVBoxLayout, QProgressBar, QMenuBar, QMenu, QMainWindow, QApplication, QAction, QStatusBar, QFileDialog, QSizePolicy, QMessageBox, QSpinBox, QDialog, QCheckBox, QRadioButton, QProgressDialog, QTableView, QSlider, QStyle
from PyQt5.QtCore import Qt, QSize, QAbstractTableModel, QUrl
from PyQt5.QtGui import QFont, QIcon, QPixmap, QCursor, QImage, QFontDatabase, QMovie
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from amos_functions import analyse, get_thumbnail, save_spreadsheet, apply_defaults, set_defaults, delete_defaults, write_ama_file

StyleSheet = """
QMainWindow#AnalysationWindow {
    background-color:#121212;
    color:white;
}
QWidget#default_widget {
    background-color:#121212;
    color:white;
}
QLabel#video_thumb {
    border-style:solid;
    border-width:1px;
    border-color:#eeeeee;
}
QPushButton#secondary_button {
    background-color:transparent;
    color:#2894E0;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#2894E0;
    padding:6px;
    max-width:80px;
    min-width:80px;
}
QPushButton#secondary_button:hover {
    background-color:#2894E0;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#2894E0;
    padding:6px;
    max-width:80px;
    min-width:80px;
}
QPushButton#tertiary_button {
    background-color:transparent;
    color:white;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:white;
}
QPushButton#tertiary_button:hover {
    background-color:white;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:white;
}
QGroupBox {
    background-color:transparent;
    color:white;
    border-style:solid;
    border-width:2px;
    border-radius:8px;
    border-color:white;
    padding:6px;
}
QPushButton#primary_button {
    background-color:transparent;
    color:#00BD66;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#00BD66;
    text-align:right;
    background-image:url(files/analyse_icon.png);
    background-repeat:no repeat;
    background-position:left;
    padding:10px;
}
QPushButton#primary_button:hover {
    background-color:#00BD66;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#00BD66;
    text-align:right;
    background-image:url(files/analyse_icon_hover.png);
    background-repeat:no repeat;
    background-position:left;
    padding:10px;
}
QPushButton#help_defaults_button {
    border-style:solid;
    border-width:2px;
    border-radius:16px;
    border-color:white;
    color:white;
}
QPushButton#help_defaults_button:hover {
    background-color:white;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:16px;
    border-color:white;
}
QLabel#selection_status {
    max-width: 35px;
}
QPushButton#delete_button {
    background-color:transparent;
    color:#2894E0;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#2894E0;
    padding:6px;
    max-width:20px;
    background-image:url(files/trash_icon.png);
    background-repeat:no repeat;
    background-position:center;
}
QPushButton#delete_button:hover {
    background-color:#2894E0;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#2894E0;
    padding:6px;
    max-width:20px;
    background-image:url(files/trash_icon_hover.png);
    background-repeat:no repeat;
    background-position:center;
}
QLabel#default_label {
    color:#eeeeee;
}
QSpinBox {
    padding-left: 8px;
    background-color:transparent;
    color:#eeeeee;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#eeeeee;
}
QCheckBox {
    color:#eeeeee;
}
QRadioButton {
    color:#eeeeee;
}
QToolTip {
    background:#4f5764;
    border-style: none;
    color:#b0b0b0;
    padding:4px;
}
QGridLayout {
    background-color:transparent;
}
QTableView {
    background:transparent;
    color:white;
}
QPushButton#video_button {
    background-color:transparent;
}
"""
class Drop_Label(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.pathtype=""

    def defineType(self, type_define):
        self.pathtype = type_define

    def dragEnterEvent(self, event):
        path=str(event.mimeData().urls()[0].toLocalFile())
        if event.mimeData().hasUrls and path[-4:].upper() == ".MP4" and self.pathtype == "video":
            event.accept()
        elif event.mimeData().hasUrls and path[-4:].upper() == ".XML" and self.pathtype == "xml":
            event.accept()
        elif event.mimeData().hasUrls and os.path.isdir(path) and self.pathtype == "folder":
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()

            output = event.mimeData().urls()
            links = []
            for link in output:
                if link.isLocalFile():
                    links.append(str(link.toLocalFile()))

            if self.pathtype == "video":
                Window.setup_video_selection(links)

            if self.pathtype == "xml":
                Window.setup_xml_selection(links)

            if self.pathtype == "folder":
                Window.setup_folder_selection(links[0])
        else:
            event.ignore()

class PickSpinbox(QSpinBox):
    def __init__(self, *args):
        QSpinBox.__init__(self, *args)
        
        self.setFont(Window.font_bold_14)
        self.setWrapping(True)
        self.setAlignment(Qt.AlignCenter)
    
    def textFromValue(self, value):
        return "%02d" % value

class DatePickerPopup(QDialog):
    def __init__(self):
        QDialog.__init__(self)

        self.setObjectName("default_widget")
        self.setWindowTitle("Select the video starting time and date")
        self.initUI()

    def initUI(self):
        self.now = datetime.datetime.now()

        self.datetime_group = QGroupBox(self)
        self.datetime_group.setTitle("First video")
        self.datetime_group.setFont(Window.font_normal_10)
        self.datetime_group.setFlat(True)
        self.datetime_group.setGeometry(10,10, 330, 100)

        self.date_label = QLabel(self.datetime_group, text="Date:")
        self.date_label.setGeometry(10,20,60,28)
        self.date_label.setObjectName("default_label")
        self.date_label.setFont(Window.font_bold_14)

        self.time_label = QLabel(self.datetime_group, text="Time:")
        self.time_label.setGeometry(10,60,60,28)
        self.time_label.setObjectName("default_label")
        self.time_label.setFont(Window.font_bold_14)

        self.day_month_separator = QLabel(self.datetime_group, text=".")
        self.day_month_separator.move(145,22)
        self.day_month_separator.setObjectName("time_label")
        self.day_month_separator.setFont(Window.font_bold_15)

        self.month_year_separator = QLabel(self.datetime_group, text=".")
        self.month_year_separator.move(220,22)
        self.month_year_separator.setObjectName("time_label")
        self.month_year_separator.setFont(Window.font_bold_15)

        self.hour_minute_separator = QLabel(self.datetime_group, text=":")
        self.hour_minute_separator.move(145,60)
        self.hour_minute_separator.setObjectName("time_label")
        self.hour_minute_separator.setFont(Window.font_bold_15)

        self.minute_second_separator = QLabel(self.datetime_group, text=":")
        self.minute_second_separator.move(220,60)
        self.minute_second_separator.setObjectName("time_label")
        self.minute_second_separator.setFont(Window.font_bold_15)

        self.day_spin_box = PickSpinbox(self.datetime_group)
        self.day_spin_box.move(80, 20)
        self.day_spin_box.setRange(1,31)
        self.day_spin_box.setValue(self.now.day)

        self.month_spin_box = PickSpinbox(self.datetime_group)
        self.month_spin_box.move(155, 20)
        self.month_spin_box.setRange(1,12)
        self.month_spin_box.setValue(self.now.month)

        self.year_spin_box = PickSpinbox(self.datetime_group)
        self.year_spin_box.move(230, 20)
        self.year_spin_box.setRange(1,9999)
        self.year_spin_box.setValue(self.now.year)


        self.hours_spin_box = PickSpinbox(self.datetime_group)
        self.hours_spin_box.move(80, 60)
        self.hours_spin_box.setRange(0,23)
        self.hours_spin_box.setValue(self.now.hour)

        self.minutes_spin_box = PickSpinbox(self.datetime_group)
        self.minutes_spin_box.move(155, 60)
        self.minutes_spin_box.setRange(0,59)
        self.minutes_spin_box.setValue(self.now.minute)

        self.seconds_spin_box = PickSpinbox(self.datetime_group)
        self.seconds_spin_box.move(230, 60)
        self.seconds_spin_box.setRange(0,59)
        self.seconds_spin_box.setValue(self.now.second)

        self.write_xml_box = QCheckBox(self)
        self.write_xml_box.move(120,130)
        self.write_xml_box.setText("Write XML File")
        self.write_xml_box.setChecked(True)
        self.write_xml_box.setFont(Window.font_normal_10)

        self.confirm_date_button = QPushButton(self)
        self.confirm_date_button.setGeometry(250,120, 100, 32)
        self.confirm_date_button.setText("CONFIRM")
        self.confirm_date_button.setFont(Window.font_bold_10)
        self.confirm_date_button.setObjectName("secondary_button")
        self.confirm_date_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.confirm_date_button.clicked.connect(self.confirm_date)

    def confirm_date(self):
        Window.base_time = datetime.datetime(self.year_spin_box.value(), self.month_spin_box.value(), self.day_spin_box.value(), self.hours_spin_box.value(), self.minutes_spin_box.value(), self.seconds_spin_box.value())
        if self.write_xml_box.isChecked():
            for Window.video_index in range(len(Window.videopath_list)):
                meta_data_video = cv2.VideoCapture(Window.videopath_list[Window.video_index])

                Window.length = int(meta_data_video.get(cv2.CAP_PROP_FRAME_COUNT))
                Window.Fps = int(meta_data_video.get(cv2.CAP_PROP_FPS))
                Window.Height = int(meta_data_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                Window.Width = int(meta_data_video.get(cv2.CAP_PROP_FRAME_WIDTH))

                non_realtime_meta = ET.Element('NonRealTimeMeta')
                duration = ET.SubElement(non_realtime_meta, 'Duration')
                duration.set('value', str(Window.length))
                creation_date = ET.SubElement(non_realtime_meta, 'CreationDate')
                creation_date.set('value', '%04d' % self.year_spin_box.value() + '-' + '%02d' % self.month_spin_box.value() + '-' + '%02d' % self.day_spin_box.value() + 'T' + '%02d' % self.hours_spin_box.value() + ':' + '%02d' % self.minutes_spin_box.value() + ':' + '%02d' % self.seconds_spin_box.value() + '+1:00')
                video_format = ET.SubElement(non_realtime_meta, 'VideoFormat')
                video_frame = ET.SubElement(video_format, 'VideoFrame')
                video_frame.set('captureFps', str(Window.Fps))
                video_layout = ET.SubElement(video_format, 'VideoLayout')
                video_layout.set('pixel', str(Window.Width))
                video_layout.set('numOfVerticalLine', str(Window.Height))

                xml_data = ET.tostring(non_realtime_meta, "unicode")
                
                self.write_xml_path = QFileDialog.getSaveFileName(self, "Select a directory to save the generated XML file.", f"{Window.videopath_list[Window.video_index][:-4]}.XML", "XML Files (*.xml)")
                self.write_xml_path = self.write_xml_path[0]

                if self.write_xml_path != "":
                    with open(self.write_xml_path, "w") as f:
                        f.write(xml_data)
            
        self.accept()

class TableModel(QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
        self.header_labels = ['Videopath', 'XML-Path', 'Folderpath', 'Duration', 'FPS', 'Resolution']

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.header_labels[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)

class ResultsWindow(QWidget):
    def __init__(self, ama_filepath):
        QWidget.__init__(self)
        
        self.setObjectName("default_widget")
        self.setWindowTitle("AMOS - Automatic Meteor Observation System")
        self.setGeometry(350, 100, 900, 500)

        self.ama_filepath = ama_filepath

        self.initUI()

        self.showMaximized()

    def initUI(self):
        self.meta_data_table = QTableView(self)

        self.get_ama_data()

        self.table_data = []

        for i in range(len(self.videopath_list)):
            self.table_data.append([self.videopath_list[i], self.xmlpath_list[i], self.folderpath, self.length[i], self.Fps[i], f"{self.Width[i]} x {self.Height[i]}"])
        
        self.model = TableModel(self.table_data)
        self.meta_data_table.setModel(self.model)
        self.meta_data_table.setMaximumSize(1000,150)
        self.meta_data_table.setColumnWidth(0, 200)
        self.meta_data_table.setColumnWidth(1, 200)
        self.meta_data_table.setColumnWidth(2, 200)
        self.meta_data_table.setColumnWidth(3, 60)
        self.meta_data_table.setColumnWidth(4, 60)
        self.meta_data_table.setColumnWidth(5, 100)

        self.video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile("C:/Users/Linus/V-0001.mp4")))

        self.video_widget = QVideoWidget(self)
        self.video_widget.setMinimumHeight(500)
        self.video_widget.resize(800, 450)
        self.video_player.setVideoOutput(self.video_widget)

        self.volume_icon = QIcon()
        self.volume_icon.addPixmap(QPixmap("files/volume.png"), QIcon.Normal, QIcon.Off)
        self.volume_muted_icon = QIcon()
        self.volume_muted_icon.addPixmap(QPixmap("files/volume_mute.png"), QIcon.Normal, QIcon.Off)
        self.play_icon = QIcon()
        self.play_icon.addPixmap(QPixmap("files/play.png"), QIcon.Normal, QIcon.Off)
        self.pause_icon = QIcon()
        self.pause_icon.addPixmap(QPixmap("files/pause.png"), QIcon.Normal, QIcon.Off)

        self.mute_button = QPushButton(self)
        self.mute_button.setIcon(self.volume_icon)
        self.mute_button.setObjectName("video_button")
        self.play_button = QPushButton(self)
        self.play_button.setIcon(self.play_icon)
        self.play_button.setObjectName("video_button")
        # self.skip_forward = QPushButton(self)
        # self.mute_button.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))

        self.main_layout = QGridLayout(self)
        self.button_layout = QHBoxLayout(self)

        self.button_layout.addWidget(self.mute_button)
        self.button_layout.addWidget(self.play_button)

        self.main_layout.addWidget(self.meta_data_table, 0, 0)
        self.main_layout.addWidget(self.video_widget, 1, 0)
        self.main_layout.addLayout(self.button_layout, 2,0)

        self.mute_button.clicked.connect(self.toggle_muted)
        self.play_button.clicked.connect(self.toggle_play)

    def get_ama_data(self):
        self.path = self.ama_filepath
        with open(self.path, "r") as f:
            self.data = f.read().split(sep="\n")
            self.videopath_list, self.xmlpath_list, self.folderpath = json.loads(self.data[0])
            self.base_times = json.loads(self.data[1])
            self.base_time_list = []
            for base_time in self.base_times:
                self.base_time_list.append(datetime.datetime(*base_time))
            self.length = json.loads(self.data[2])
            self.Fps = json.loads(self.data[3])
            self.Width, self.Height = json.loads(self.data[4])
            self.meteors = json.loads(self.data[5])

    def toggle_muted(self):
        if self.video_player.isMuted():
            self.video_player.setMuted(False)
            self.mute_button.setIcon(self.volume_icon)
        else:
            self.video_player.setMuted(True)
            self.mute_button.setIcon(self.volume_muted_icon)

    def toggle_play(self):
        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.pause()
            self.play_button.setIcon(self.play_icon)
        else:
            self.video_player.play()
            self.play_button.setIcon(self.pause_icon)

    def closeEvent(self, event):
        # Make sure the video stops when the window closes
        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.stop()
        event.accept()

class AnalysationWindow(QMainWindow):
    def __init__(self):
        super(AnalysationWindow, self).__init__()

        #Define fonts
        #roboto_light = QFontDatabase.addApplicationFont("files/Roboto-Light.ttf")
        self.default_font = QFont("Roboto Light", 9)
        self.font_bold_9 = QFont("Roboto Light", 9)
        self.font_bold_9.setBold(True)
        self.font_bold_10 = QFont("Roboto Light", 10)
        self.font_bold_10.setBold(True)
        self.font_bold_14 = QFont("Roboto Medium", 14)
        self.font_bold_14.setBold(True)
        self.font_normal_10 = QFont("Roboto Light", 10)
        self.font_bold_15 = QFont("Poetsen One", 15)
        self.font_bold_15.setBold(True)

        #define icons
        self.app_icon = QIcon()
        self.app_icon.addPixmap(QPixmap("files/logo.ico"), QIcon.Normal, QIcon.Off)
        self.trash_icon = QIcon()
        self.trash_icon.addPixmap(QPixmap("files/trash_icon.png"), QIcon.Normal, QIcon.Off)
        self.analyse_icon = QIcon()
        self.analyse_icon.addPixmap(QPixmap("files/analyse_icon.png"), QIcon.Normal, QIcon.Off)

        #define movies
        self.loading_animation = QMovie("files/loading.gif")
        self.loading_animation.setScaledSize(QSize(32,32))

        self.resize(1000, 700)
        self.setFont(self.default_font)
        self.setWindowTitle("AMOS - Automatic Meteor Observation System")
        self.setWindowIcon(self.app_icon)
        self.setObjectName("AnalysationWindow")
        self.initUI()

    def initUI(self):
        #setup the main widget
        self.centralwidget = QWidget(self)

        #Setup the logo
        self.amos_title_image = QLabel(self.centralwidget)
        self.amos_title_image.setGeometry(10, 0, 400, 132)
        self.amos_title_image.setPixmap(QPixmap("files/amos_logo_white.png"))
        self.amos_title_image.setScaledContents(True)

        #Thumbnail section
        self.video_thumb_label = QLabel(self.centralwidget)
        self.video_thumb_label.move(260, 180)
        self.video_thumb_label.setText("Video preview:")
        self.video_thumb_label.setObjectName("default_label")
        self.video_thumb_label.setFont(self.font_bold_10)

        self.video_thumb = QLabel(self.centralwidget)
        self.video_thumb.move(405, 135)
        self.video_thumb.resize(192,108)
        self.video_thumb.setPixmap(QPixmap("files/default_thumbnail.png"))
        self.video_thumb.setScaledContents(True)
        self.video_thumb.setObjectName("video_thumb")


        #File selection section
        self.file_selection_widget = QWidget(self.centralwidget)
        self.file_selection_widget.setGeometry(20, 240, 820, 200)
        self.file_selection_grid = QGridLayout(self.file_selection_widget)
        self.file_selection_grid.setContentsMargins(0, 0, 0, 0)        

        self.video_selection_status = QLabel(self.file_selection_widget)
        self.video_selection_status.setObjectName("selection_status")
        self.video_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
        self.xml_selection_status = QLabel(self.file_selection_widget)
        self.xml_selection_status.setObjectName("selection_status")
        self.xml_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
        self.folder_selection_status = QLabel(self.file_selection_widget)
        self.folder_selection_status.setObjectName("selection_status")
        self.folder_selection_status.setPixmap(QPixmap("files/cross_icon.png"))

        spacer_status_browse = QSpacerItem(60, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.browse_video_button = QPushButton(self.file_selection_widget)
        self.browse_video_button.setFont(self.font_bold_10)
        self.browse_video_button.setObjectName("secondary_button")
        self.browse_video_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.browse_xml_button = QPushButton(self.file_selection_widget)
        self.browse_xml_button.setFont(self.font_bold_10)
        self.browse_xml_button.setObjectName("secondary_button")
        self.browse_xml_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.browse_folder_button = QPushButton(self.file_selection_widget)
        self.browse_folder_button.setFont(self.font_bold_10)
        self.browse_folder_button.setObjectName("secondary_button")
        self.browse_folder_button.setCursor(QCursor(Qt.PointingHandCursor))

        spacer_browse_path = QSpacerItem(60, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.videopath_label = Drop_Label(self.file_selection_widget)
        self.videopath_label.defineType("video")
        self.videopath_label.setFont(self.default_font)
        self.videopath_label.setAlignment(Qt.AlignCenter)
        self.videopath_label.setObjectName("default_label")
        self.xmlpath_label = Drop_Label(self.file_selection_widget)
        self.xmlpath_label.defineType("xml")
        self.xmlpath_label.setFont(self.default_font)
        self.xmlpath_label.setAlignment(Qt.AlignCenter)
        self.xmlpath_label.setObjectName("default_label")
        self.folderpath_label = Drop_Label(self.file_selection_widget)
        self.folderpath_label.defineType("folder")
        self.folderpath_label.setFont(self.default_font)
        self.folderpath_label.setAlignment(Qt.AlignCenter)
        self.folderpath_label.setObjectName("default_label")
        
        self.delete_video_selection_button = QPushButton(self.file_selection_widget)
        self.delete_video_selection_button.setObjectName("delete_button")
        self.delete_video_selection_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_xml_selection_button = QPushButton(self.file_selection_widget)
        self.delete_xml_selection_button.setObjectName("delete_button")
        self.delete_xml_selection_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_folder_selection_button = QPushButton(self.file_selection_widget)
        self.delete_folder_selection_button.setObjectName("delete_button")
        self.delete_folder_selection_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.use_xml_radio = QRadioButton(self.file_selection_widget)
        self.use_xml_radio.setText("Use XML video starting time")
        self.use_xml_radio.setChecked(True)
        self.use_xml = True

        self.use_no_xml_radio = QRadioButton(self.file_selection_widget)
        self.use_no_xml_radio.setText("Use custom video starting time")
        self.use_no_xml_radio.setChecked(False)
        self.use_no_xml_radio.toggled.connect(self.toggle_xml_usage)

        self.select_starting_time_button = QPushButton(self)
        self.select_starting_time_button.setText("SELECT")
        self.select_starting_time_button.setFixedSize(100, 33)
        self.select_starting_time_button.setObjectName("secondary_button")
        self.select_starting_time_button.setFont(self.font_bold_10)
        self.select_starting_time_button.setVisible(False)
        self.select_starting_time_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.file_selection_grid.addWidget(self.video_selection_status, 0, 0, 1, 1)
        self.file_selection_grid.addWidget(self.xml_selection_status, 4, 0, 1, 1)
        self.file_selection_grid.addWidget(self.folder_selection_status, 1, 0, 1, 1)
        self.file_selection_grid.addItem(spacer_status_browse, 0, 1, 3, 1)
        self.file_selection_grid.addWidget(self.browse_video_button, 0, 2, 1, 1)
        self.file_selection_grid.addWidget(self.browse_xml_button, 4, 2, 1, 1)
        self.file_selection_grid.addWidget(self.browse_folder_button, 1, 2, 1, 1)
        self.file_selection_grid.addItem(spacer_browse_path, 0, 3, 3, 1)
        self.file_selection_grid.addWidget(self.videopath_label, 0, 4, 1, 1)
        self.file_selection_grid.addWidget(self.xmlpath_label, 4, 4, 1, 1)
        self.file_selection_grid.addWidget(self.folderpath_label, 1, 4, 1, 1)
        self.file_selection_grid.addWidget(self.delete_video_selection_button, 0, 5, 1, 1)
        self.file_selection_grid.addWidget(self.delete_xml_selection_button, 4, 5, 1, 1)
        self.file_selection_grid.addWidget(self.delete_folder_selection_button, 1, 5, 1, 1)
        self.file_selection_grid.addWidget(self.use_xml_radio, 2, 2, 1, 1)
        self.file_selection_grid.addWidget(self.use_no_xml_radio, 3, 2, 1, 1)
        self.file_selection_grid.addWidget(self.select_starting_time_button, 3, 3, 1, 2)

        #Defaults section
        self.defaults_group = QGroupBox(self.centralwidget)
        self.defaults_group.setGeometry(430, 20, 480, 80)
        self.defaults_group.setFont(self.font_normal_10)
        self.defaults_group.setFlat(True)
        
        self.apply_defaults_button = QPushButton(self.defaults_group)
        self.apply_defaults_button.setGeometry(20, 30, 130, 33)
        self.apply_defaults_button.setFont(self.font_bold_9)
        self.apply_defaults_button.setObjectName("tertiary_button")
        self.apply_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.set_defaults_button = QPushButton(self.defaults_group)
        self.set_defaults_button.setGeometry(160, 30, 120, 33)
        self.set_defaults_button.setFont(self.font_bold_9)
        self.set_defaults_button.setObjectName("tertiary_button")
        self.set_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_defaults_button = QPushButton(self.defaults_group)
        self.delete_defaults_button.setGeometry(290, 30, 140, 33)
        self.delete_defaults_button.setFont(self.font_bold_9)
        self.delete_defaults_button.setObjectName("tertiary_button")
        self.delete_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.help_defaults_button = QPushButton(self.centralwidget)
        self.help_defaults_button.setGeometry(870, 25, 32, 32)
        self.help_defaults_button.setText("?")
        self.help_defaults_button.setFont(self.font_bold_14)
        self.help_defaults_button.setObjectName("help_defaults_button")
        self.help_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        #Analyse section
        self.analyse_widget = QWidget(self.centralwidget)
        self.analyse_widget.setGeometry(20, 450, 250, 71)
        self.analyse_layout = QHBoxLayout(self.analyse_widget)
        self.analyse_layout.setContentsMargins(0, 0, 0, 0)

        self.analysation_status_image = QLabel(self.analyse_widget)
        self.analysation_status_image.setPixmap(QPixmap("files/cross_icon.png"))

        spacer_status_analyse = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.analyse_button = QPushButton(self.analyse_widget)
        self.analyse_button.setFont(self.font_bold_15)
        self.analyse_button.setObjectName("primary_button")
        self.analyse_button.setFixedWidth(170)
        self.analyse_button.setFixedHeight(50)
        self.analyse_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.analyse_layout.addWidget(self.analysation_status_image)
        self.analyse_layout.addItem(spacer_status_analyse)
        self.analyse_layout.addWidget(self.analyse_button)

        #Spreadsheet section
        self.spreadsheet_group = QGroupBox(self.centralwidget)
        self.spreadsheet_group.setGeometry(20, 570, 480, 80)
        self.spreadsheet_group.setFont(self.font_normal_10)
        self.spreadsheet_group.setFlat(True)
        
        self.open_spreadsheet_button = QPushButton(self.spreadsheet_group)
        self.open_spreadsheet_button.setGeometry(20, 30, 250, 32)
        self.open_spreadsheet_button.setFont(self.font_bold_9)
        self.open_spreadsheet_button.setObjectName("tertiary_button")
        self.open_spreadsheet_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_spreadsheet_button = QPushButton(self.spreadsheet_group)
        self.save_spreadsheet_button.setGeometry(300, 30, 150, 32)
        self.save_spreadsheet_button.setFont(self.font_bold_9)
        self.save_spreadsheet_button.setObjectName("tertiary_button")
        self.save_spreadsheet_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        #Setup the central widget
        self.setCentralWidget(self.centralwidget)

        #Add a menubar
        self.menubar = QMenuBar(self)
        self.filemenu = QMenu(self.menubar)
        self.languagemenu = QMenu(self.menubar)
        self.setMenuBar(self.menubar)

        self.actionOpen = QAction(self)
        self.actionSave = QAction(self)
        self.actionSettings = QAction(self)
        self.actionQuit = QAction(self)

        self.actionGerman = QAction(self)
        self.actionEnglish = QAction(self)

        self.filemenu.addAction(self.actionOpen)
        self.filemenu.addAction(self.actionSave)
        self.filemenu.addAction(self.actionSettings)
        self.filemenu.addSeparator()
        self.filemenu.addAction(self.actionQuit)
        self.languagemenu.addAction(self.actionGerman)
        self.languagemenu.addAction(self.actionEnglish)
        self.menubar.addAction(self.filemenu.menuAction())
        self.menubar.addAction(self.languagemenu.menuAction())

        #Add a statusbar
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        #Add all the text
        self.browse_video_button.setText("BROWSE")
        self.browse_xml_button.setText("BROWSE")
        self.browse_folder_button.setText("BROWSE")
        self.videopath_label.setText('Please press "Browse" or drag & drop a video to select it')
        self.xmlpath_label.setText('Please press "Browse" or drag & drop an XML file to select it')
        self.folderpath_label.setText('Please press "Browse" or drag & drop a folder to select it')
        
        self.defaults_group.setTitle("Defaults")
        self.set_defaults_button.setText("Set defaults")
        self.apply_defaults_button.setText("Apply defaults")
        self.delete_defaults_button.setText("Delete defaults")
        

        self.analyse_button.setText("ANALYSE")

        self.spreadsheet_group.setTitle("Spreadsheet options")
        self.open_spreadsheet_button.setText("Open spreadsheet with results")
        self.save_spreadsheet_button.setText("Save spreadsheet")

        self.browse_video_button.setToolTip("Browse to select a video to process.")
        self.browse_xml_button.setToolTip("Browse to select an xml file.")
        self.browse_folder_button.setToolTip("Browse to select a folder to store results in.")
        self.video_selection_status.setToolTip("Status:\nNot yet completed!")
        self.xml_selection_status.setToolTip("Status:\nNot yet completed!")
        self.folder_selection_status.setToolTip("Status:\nNot yet completed!")
        self.analysation_status_image.setToolTip("Status:\nNot yet completed!")
        self.delete_video_selection_button.setToolTip("Clear your video selection.")
        self.delete_xml_selection_button.setToolTip("Clear your xml selection.")
        self.delete_folder_selection_button.setToolTip("Clear your folder selection.")
        self.help_defaults_button.setToolTip("What are defaults?")
        self.analyse_button.setToolTip("Analyse the selected video.")

        self.filemenu.setTitle("File")
        self.languagemenu.setTitle("Language")
        self.actionOpen.setText("Open")
        self.actionOpen.setShortcut("Ctrl+O")
        self.actionSave.setText("Save")
        self.actionSave.setShortcut("Ctrl+S")
        self.actionSettings.setText("Settings")
        self.actionSettings.setShortcut("Ctrl+Shift+P")
        self.actionQuit.setText("Quit")
        self.actionQuit.setShortcut("Ctrl+Q")
        self.actionGerman.setText("German")
        self.actionEnglish.setText("English")

        self.browse_video_button.clicked.connect(self.get_video_location)
        self.browse_xml_button.clicked.connect(self.get_xml_location)
        self.browse_folder_button.clicked.connect(self.get_folder_location)
        self.select_starting_time_button.clicked.connect(self.select_starting_time)
        self.delete_video_selection_button.clicked.connect(self.delete_video_selection)
        self.delete_xml_selection_button.clicked.connect(self.delete_xml_selection)
        self.delete_folder_selection_button.clicked.connect(self.delete_folder_selection)
        self.apply_defaults_button.clicked.connect(self.apply_defaults)
        self.set_defaults_button.clicked.connect(self.set_defaults)
        self.delete_defaults_button.clicked.connect(self.delete_defaults)
        self.help_defaults_button.clicked.connect(self.help_defaults)
        self.open_spreadsheet_button.clicked.connect(self.open_spreadsheet)
        self.save_spreadsheet_button.clicked.connect(self.save_spreadsheet)
        self.analyse_button.clicked.connect(self.analyse)

        self.actionQuit.triggered.connect(self.exit_program)
        self.actionOpen.triggered.connect(self.open_ama_file)
        self.actionSave.triggered.connect(self.save_ama_file)

    def setup_video_selection(self, videopath_list):
        self.videopath_list = videopath_list
        if self.videopath_list != []: #If the user didn't cancel the selection
            thumbnail = get_thumbnail(self.videopath_list[0])
            if thumbnail.any() == None:
                return
            height, width, _ = thumbnail.shape
            bytesPerLine = 3 * width
            video_thumbnail = QImage(thumbnail.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
            self.video_thumb.setPixmap(QPixmap(video_thumbnail))
            self.VideoID_List = []
            self.videopath_string = ""
            for video in self.videopath_list:
                self.VideoID_List.append(video[-10:-4])
            if len(self.videopath_list) == 1:
                self.videopath_string = self.videopath_list[0]
                if len(self.videopath_string) > 50:
                    self.videopath_string = f"{self.videopath_string[:3]} [ . . . ] {self.videopath_string[-50:]}"
                self.videopath_label.setText("Video:\n" + self.videopath_string)
            else:
                for i in range(1):
                    video=self.videopath_list[i]
                    if len(video) > 50:
                        video=f"{video[:3]} [ . . . ] {video[-50:]}"
                    self.videopath_string += f"\n{video}"
                self.videopath_string += f"\n... and {str(len(self.videopath_list)-1)} more"
                self.videopath_label.setText("Videos:" + self.videopath_string)
            self.video_selection_status.setPixmap(QPixmap("files/check_icon.png"))
            self.video_selection_status.setToolTip("Status:\nCompleted!")

    def setup_xml_selection(self, xmlpath_list):
        self.xmlpath_list = xmlpath_list
        if self.xmlpath_list != []: #If the user didn't cancel the selection
            self.xmlpath_string = ""
            if len(self.xmlpath_list) == 1:
                self.xmlpath_string = self.xmlpath_list[0]
                if len(self.xmlpath_string) > 50:
                    self.xmlpath_string = f"{self.xmlpath_string[:3]} [ . . . ] {self.xmlpath_string[-50:]}"
                self.xmlpath_label.setText("XML:\n" + self.xmlpath_string)
            else:
                for i in range(1):
                    xml=self.xmlpath_list[i]
                    if len(xml) > 50:
                        xml=f"{xml[:3]} [ . . . ] {xml[-50:]}"
                    self.xmlpath_string += f"\n{xml}"
                self.xmlpath_string += f"\n... and {str(len(self.xmlpath_list)-1)} more"
                self.xmlpath_label.setText("XMLs:" + self.xmlpath_string)
            self.xml_selection_status.setPixmap(QPixmap("files/check_icon.png"))
            self.xml_selection_status.setToolTip("Status:\nCompleted!")

    def setup_folder_selection(self, folderpath):
        self.folderpath = folderpath
        if self.folderpath != "": #If the user didn't cancel the selection
            if len(self.folderpath) > 50:
                self.folderpath_string = f"{self.folderpath[:3]} [ . . . ] {self.folderpath[-50:]}"
            else:
                self.folder
            self.folderpath_label.setText("Results folder:\n" + self.folderpath_string)
            
            self.folder_selection_status.setPixmap(QPixmap("files/check_icon.png"))
            self.folder_selection_status.setToolTip("Status:\nCompleted!")

    def get_video_location(self):
        self.videopath_list = QFileDialog.getOpenFileNames(parent=self, filter="MP4 Files (*.mp4)")
        self.videopath_list = self.videopath_list[0]
        self.setup_video_selection(self.videopath_list)
            
    def get_xml_location(self):
        self.xmlpath_list = QFileDialog.getOpenFileNames(parent=self, filter="XML Files (*.xml)")
        self.xmlpath_list = self.xmlpath_list[0]
        self.setup_xml_selection(self.xmlpath_list)

    def get_folder_location(self):
        self.folderpath = QFileDialog.getExistingDirectory(parent=self)
        self.setup_folder_selection(self.folderpath)

    def delete_video_selection(self):
        try:
            self.videopath_label.setText('Please press "Browse" or drag & drop a video to select it')
            self.video_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
            del self.videopath_list
            self.video_thumb.setPixmap(QPixmap("files/default_thumbnail.png"))
            self.video_selection_status.setToolTip("Status:\nNot yet completed!")
        except AttributeError:
            pass

    def delete_xml_selection(self):
        try:
            self.xmlpath_label.setText('Please press "Browse" or drag & drop an XML file to select it')
            self.xml_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
            del self.xmlpath_list
            self.xml_selection_status.setToolTip("Status:\nNot yet completed!")
        except AttributeError:
            pass
    
    def delete_folder_selection(self):
        try:
            self.folderpath_label.setText('Please press "Browse" or drag & drop a folder to select it')
            self.folder_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
            del self.folderpath
            self.folder_selection_status.setToolTip("Status:\nNot yet completed!")
        except AttributeError:
            pass
    
    def help_defaults(self):
        help_defaults_message = QMessageBox()
        help_defaults_message.setWindowTitle("What are defaults?")
        help_defaults_message.setText("Defaults are not required for the program to work. They let you quickly fill out the video, xml and folderpath with predefined values. You should only use them if you analyse the same video over and over again.")
        help_defaults_message.setIcon(QMessageBox.Question)
        help_defaults_message.setStandardButtons(QMessageBox.Ok)

        help_defaults_message.exec_()
    
    def exit_program(self):
        sys.exit()

    def open_spreadsheet(self):
        try:
            os.startfile(f"{self.folderpath}/Results.xlsx")
        except AttributeError:
            self.open_spreadsheet_message = QMessageBox()
            self.open_spreadsheet_message.setWindowTitle("Folder selection missing!")
            self.open_spreadsheet_message.setText("To open the results spreadsheet, you first have to: \n    1. Select a folder where the results are stored in.\n    2. Run the analysation to generate results. NOTE: You can also use this \n        application to view existing results. In this case, you don't have to run the \n        analysation, but you have to select the folder where it is stored in")
            self.open_spreadsheet_message.setIcon(QMessageBox.Warning)
            self.open_spreadsheet_message.setStandardButtons(QMessageBox.Close)
            self.open_spreadsheet_message.exec_()
    
    def analyse(self):
        try:
            self.wb = xl.load_workbook('files/Results_template.xlsx')
            self.sheet = self.wb['Data']
            self.meteor_count = 0

            for self.video_index in range(len(self.videopath_list)):
                meta_data_video = cv2.VideoCapture(self.videopath_list[self.video_index])
                self.length = int(meta_data_video.get(cv2.CAP_PROP_FRAME_COUNT))
                self.Fps = int(meta_data_video.get(cv2.CAP_PROP_FPS))
                self.Height = int(meta_data_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.Width = int(meta_data_video.get(cv2.CAP_PROP_FRAME_WIDTH))
                
                if self.use_xml:
                    self.was_successful, self.meteor_data = analyse(self.videopath_list[self.video_index],self.xmlpath_list[self.video_index],self.folderpath, self.VideoID_List[self.video_index], Window, True)
                else:
                    date_picker_popup = DatePickerPopup()
                    date_picker_popup.exec_()

                    self.was_successful, self.meteor_data = analyse(Window.videopath_list[self.video_index],None,Window.folderpath, Window.VideoID_List[self.video_index], Window, False)
            
            if self.was_successful:
                self.analysation_status_image.setPixmap(QPixmap("files/check_icon.png"))
                self.analysation_status_image.setToolTip("Status:\nCompleted!")
                try:
                    self.wb.save(f'{self.folderpath}/Results.xlsx')
                except PermissionError:
                    Window.spreadsheet_opened_error = QMessageBox(icon=QMessageBox.Warning, text='You have your spreadsheet still opened! Close it and press "Save spreadsheet" again, otherwise ALL DATA WILL BE LOST!')
                    Window.spreadsheet_opened_error.setWindowTitle("Spreadsheet still opened!")
                    Window.spreadsheet_opened_error.setStandardButtons(QMessageBox.Close)

                    Window.spreadsheet_opened_error.exec_()
                
        except AttributeError as a:
            self.analyse_error_message = QMessageBox(icon=QMessageBox.Critical, text='The analysation algorithm needs three infos:\n    1. The video to process.\n    2. The corresponding XML file to get information like the \n        duration, resolution and frame rate.\n    3. The folder where it saves images of frames with meteors \n        and the spreadsheet.')
            self.analyse_error_message.setWindowTitle("File selection missing!")
            self.analyse_error_message.setInformativeText('<h3><strong>To select these infos, press the blue "Browse" buttons.</strong></h3>')
            self.analyse_error_message.setDetailedText("Error message:\n"+str(a))
            self.analyse_error_message.setStandardButtons(QMessageBox.Close)
            self.analyse_error_message.exec_()
        except Exception as e:
            self.analyse_error_message = QMessageBox(icon=QMessageBox.Critical, text=f"The following unknown error occurred:\n'{e}'\nPlease contact the developer of this program to fix the problem!")
            self.analyse_error_message.setWindowTitle("Unknown error occured")
            self.analyse_error_message.exec_()

    def save_spreadsheet(self):
        try:
            save_spreadsheet(Window)
            self.spreadsheet_sucess_message = QMessageBox()
            self.spreadsheet_sucess_message.setWindowTitle("Saved succesfully!")
            self.spreadsheet_sucess_message.setText('Spreadsheet saved succesfully!')
            self.spreadsheet_sucess_message.setIcon(QMessageBox.Information)
            self.spreadsheet_sucess_message.setStandardButtons(QMessageBox.Ok)
            self.spreadsheet_sucess_message.exec_()

        except PermissionError:
            self.spreadsheet_opened_error = QMessageBox()
            self.spreadsheet_opened_error.setWindowTitle("Spreadsheet still opened!")
            self.spreadsheet_opened_error.setText('You have your spreadsheet still opened! Close it and press "Save spreadsheet" again, otherwise ALL DATA WILL BE LOST!')
            self.spreadsheet_opened_error.setIcon(QMessageBox.Warning)
            self.spreadsheet_opened_error.setStandardButtons(QMessageBox.Close)
            self.spreadsheet_opened_error.exec_()

        except NameError:
            self.spreadsheet_not_able_to_save = QMessageBox()
            self.spreadsheet_not_able_to_save.setWindowTitle("Data missing!")
            self.spreadsheet_not_able_to_save.setText('Please run the analysation before saving the spreadsheet.')
            self.spreadsheet_not_able_to_save.setIcon(QMessageBox.Warning)
            self.spreadsheet_not_able_to_save.setStandardButtons(QMessageBox.Close)
            self.spreadsheet_not_able_to_save.exec_()
    
    def apply_defaults(self):
        apply_defaults(Window)

    def set_defaults(self):
        set_defaults(Window)

    def delete_defaults(self):
        delete_defaults(Window)

    def toggle_xml_usage(self):
        if self.use_no_xml_radio.isChecked():
            self.use_xml = False
            self.delete_xml_selection()
            self.xml_selection_status.setVisible(False)
            self.browse_xml_button.setVisible(False)
            self.xmlpath_label.setVisible(False)
            self.delete_xml_selection_button.setVisible(False)
            self.select_starting_time_button.setVisible(True)
        else:
            self.use_xml = True
            self.xml_selection_status.setVisible(True)
            self.browse_xml_button.setVisible(True)
            self.xmlpath_label.setVisible(True)
            self.delete_xml_selection_button.setVisible(True)
            self.select_starting_time_button.setVisible(False)

    def select_starting_time(self):
        try:
            a = self.videopath_list
            b = self.folderpath
            del a
            del b
            date_picker_popup = DatePickerPopup()
            date_picker_popup.exec_()
        except AttributeError:
            self.video_not_defined = QMessageBox()
            self.video_not_defined.setWindowTitle("No video selected!")
            self.video_not_defined.setText('To be able to select the video starting time, you have to select a video.')
            self.video_not_defined.setInformativeText('<h3><strong>For that, press the first blue "Browse" button.</strong></h3>')
            self.video_not_defined.setIcon(QMessageBox.Critical)
            self.video_not_defined.setStandardButtons(QMessageBox.Close)
            self.video_not_defined.exec_()
    
    def open_ama_file(self):
        #ama_filepath = QFileDialog.getOpenFileName(self, "Select AMA File")[0]
        ama_filepath = "D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/template.ama"
        if ama_filepath != "":
            self.results_window = ResultsWindow(ama_filepath)
            self.results_window.show()

    def save_ama_file(self):
        ama_filepath = QFileDialog.getSaveFileName(self, "Select a directory to save the AMA file in")[0]
        temp_meteor_data = {'signal_1': {'position': (1410, 931), 'frame': [52]}, 'signal_2': {'position': (1425, 939), 'frame': [53]}, 'signal_3': {'position': (1440, 947), 'frame': [54]}, 'signal_4': {'position': (1456, 955), 'frame': [55]}, 'signal_5': {'position': (1473, 963), 'frame': [56]}, 'signal_6': {'position': (1490, 972), 'frame': [57]}, 'signal_7': {'position': (1507, 980), 'frame': [58]}, 'signal_8': {'position': (1525, 989), 'frame': [59]}, 'signal_9': {'position': (1461, 957), 'frame': [59]}, 'signal_10': {'position': (1474, 964), 'frame': [60]}, 'signal_11': {'position': (1475, 965), 'frame': [61]}, 'signal_12': {'position': (1475, 964), 'frame': [62]}, 'signal_13': {'position': (1474, 964), 'frame': [63]}, 'signal_14': {'position': (1473, 964), 'frame': [64]}, 'signal_15': {'position': (1471, 962), 'frame': [65]}, 'signal_16': {'position': (1482, 968), 'frame': [66]}, 'signal_17': {'position': (1455, 954), 'frame': [66]}, 'signal_18': {'position': (1484, 969), 'frame': [67]}, 'signal_19': {'position': (1457, 955), 'frame': [67]}, 'signal_20': {'position': (1484, 968), 'frame': [68]}, 'signal_21': {'position': (904, 480), 'frame': [245]}, 'signal_22': {'position': (909, 481), 'frame': [246]}, 'signal_23': {'position': (915, 482), 'frame': [247]}, 'signal_24': {'position': (921, 483), 'frame': [248]}, 'signal_25': {'position': (928, 484), 'frame': [249]}, 'signal_26': {'position': (934, 485), 'frame': [250]}, 'signal_27': {'position': (941, 486), 'frame': [251]}, 'signal_28': {'position': (948, 487), 'frame': [252]}, 'signal_29': {'position': (955, 488), 'frame': [253]}, 'signal_30': {'position': (962, 489), 'frame': [254]}, 'signal_31': {'position': (967, 491), 'frame': [255]}, 'signal_32': {'position': (964, 492), 'frame': [256]}, 'signal_33': {'position': (967, 493), 'frame': [257]}, 'signal_34': {'position': (972, 495), 'frame': [258]}, 'signal_35': {'position': (982, 496), 'frame': [259]}, 'signal_36': {'position': (988, 497), 'frame': [260]}, 'signal_37': {'position': (1012, 500), 'frame': [266]}, 'signal_38': {'position': (1009, 498), 'frame': [267]}, 'signal_39': {'position': (1008, 497), 'frame': [268]}, 'signal_40': {'position': (1008, 497), 'frame': [269]}, 'signal_41': {'position': (1009, 496), 'frame': [270]}, 'signal_42': {'position': (1008, 496), 'frame': [271]}, 'signal_43': {'position': (1009, 496), 'frame': [272]}, 'signal_44': {'position': (1008, 496), 'frame': [273]}, 'signal_45': {'position': (1007, 496), 'frame': [274]}, 'signal_46': {'position': (1006, 495), 'frame': [275]}, 'signal_47': {'position': (1006, 495), 'frame': [276]}, 'signal_48': {'position': (1006, 495), 'frame': [277]}, 'signal_49': {'position': (1006, 496), 'frame': [278]}, 'signal_50': {'position': (1005, 496), 'frame': [279]}, 'signal_51': {'position': (1004, 495), 'frame': [280]}, 'signal_52': {'position': (1004, 495), 'frame': [281]}, 'signal_53': {'position': (1003, 495), 'frame': [282]}, 'signal_54': {'position': (1003, 495), 'frame': [283]}, 'signal_55': {'position': (1006, 496), 'frame': [284]}, 'signal_56': {'position': (1005, 495), 'frame': [285]}, 'signal_57': {'position': (1002, 495), 'frame': [286]}, 'signal_58': {'position': (1003, 495), 'frame': [287]}, 'signal_59': {'position': (1002, 495), 'frame': [288]}, 'signal_60': {'position': (1002, 495), 'frame': [289]}, 'signal_61': {'position': (1000, 496), 'frame': [290]}, 'signal_62': {'position': (1001, 496), 'frame': [291]}, 'signal_63': {'position': (1000, 496), 'frame': [292]}, 'signal_64': {'position': (1061, 506), 'frame': [293]}, 'signal_65': {'position': (999, 496), 'frame': [293]}, 'signal_66': {'position': (999, 496), 'frame': [294]}, 'signal_67': {'position': (1001, 496), 'frame': [295]}, 'signal_68': {'position': (1000, 496), 'frame': [296]}, 'signal_69': {'position': (1000, 496), 'frame': [297]}, 'signal_70': {'position': (995, 495), 'frame': [298]}, 'signal_71': {'position': (994, 495), 'frame': [299]}, 'signal_72': {'position': (994, 495), 'frame': [300]}, 'signal_73': {'position': (995, 495), 'frame': [301]}, 'signal_74': {'position': (995, 495), 'frame': [302]}, 'signal_75': {'position': (995, 495), 'frame': [303]}, 'signal_76': {'position': (995, 495), 'frame': [304]}, 'signal_77': {'position': (994, 495), 'frame': [305]}, 'signal_78': {'position': (995, 495), 'frame': [306]}, 'signal_79': {'position': (996, 495), 'frame': [307]}, 'signal_80': {'position': (995, 494), 'frame': [308]}, 'signal_81': {'position': (994, 494), 'frame': [309]}, 'signal_82': {'position': (995, 495), 'frame': [310]}, 'signal_83': {'position': (994, 495), 'frame': [311]}, 'signal_84': {'position': (994, 495), 'frame': [312]}, 'signal_85': {'position': (994, 495), 'frame': [313]}, 'signal_86': {'position': (994, 494), 'frame': [314]}, 'signal_87': {'position': (995, 494), 'frame': [315]}, 'signal_88': {'position': (995, 495), 'frame': [316]}, 'signal_89': {'position': (994, 494), 'frame': [317]}, 'signal_90': {'position': (995, 495), 'frame': [318]}, 'signal_91': {'position': (995, 495), 'frame': [319]}, 'signal_92': {'position': (995, 494), 'frame': [320]}, 'signal_93': {'position': (994, 494), 'frame': [321]}, 'signal_94': {'position': (994, 494), 'frame': [322]}, 'signal_95': {'position': (992, 494), 'frame': [323]}}
        write_ama_file(ama_filepath, temp_meteor_data, 1, 1, [[2020, 6, 8, 15, 10, 30],[2020, 6, 9, 10, 12, 10]], ["D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/V-0001.mp4", "D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/V-0002.mp4"], ["D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/V-0001.XML", "D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/V-0002.XML"], "D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/Results", [1000, 2000], [25, 50], [[3840, 2160], [1920, 1080]])
        

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
app = QApplication(sys.argv)
app.setStyleSheet(StyleSheet)

Window = AnalysationWindow()
#Window.show()
Window.open_ama_file()

sys.exit(app.exec_())