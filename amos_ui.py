import sys, os
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QSpacerItem, QPushButton, QGroupBox, QHBoxLayout, QProgressBar, QMenuBar, QMenu, QMainWindow, QApplication, QAction, QStatusBar, QFileDialog, QSizePolicy, QMessageBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QCursor, QImage, QFontDatabase, QMovie
from amos_functions import analyse, get_thumbnail, save_spreadsheet, apply_defaults, set_defaults, delete_defaults

StyleSheet = """
QMainWindow#AmosWindow {
    background-color:#121212;
    color:white;
}
QLabel#video_thumb {
    border-style:solid;
    border-width:1px;
    border-color:#eeeeee;
}
QPushButton#browse_video_button , #browse_xml_button, #browse_folder_button {
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
QPushButton#browse_video_button:hover, #browse_xml_button:hover, #browse_folder_button:hover {
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
QPushButton#open_spreadsheet_button, #save_spreadsheet_button, #apply_defaults_button, #set_defaults_button, #delete_defaults_button {
    background-color:transparent;
    color:white;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:white;
}
QPushButton#open_spreadsheet_button:hover, #save_spreadsheet_button:hover, #apply_defaults_button:hover, #set_defaults_button:hover, #delete_defaults_button:hover {
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
QPushButton#analyse_button {
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
QPushButton#analyse_button:hover {
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
QLabel#video_selection_status, #xml_selection_status, #folder_selection_status {
    max-width: 35px;
}
QPushButton#delete_video_selection_button, #delete_xml_selection_button, #delete_folder_selection_button {
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
QPushButton#delete_video_selection_button:hover, #delete_xml_selection_button:hover, #delete_folder_selection_button:hover {
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
QLabel#videopath_label, #xmlpath_label, #folderpath_label, #video_thumb_label {
    color:#eeeeee;
}
QToolTip {
    background:#4f5764;
    border-style: none;
    color:#b0b0b0;
    padding:4px;
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

class AmosWindow(QMainWindow):
    def __init__(self):
        super(AmosWindow, self).__init__()

        #Define fonts
        roboto_light = QFontDatabase.addApplicationFont("files/Roboto-Light.ttf")
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
        self.help_icon = QIcon()
        self.help_icon.addPixmap(QPixmap("files/question_mark_icon.png"), QIcon.Normal, QIcon.Off)
        self.analyse_icon = QIcon()
        self.analyse_icon.addPixmap(QPixmap("files/analyse_icon.png"), QIcon.Normal, QIcon.Off)

        #define movies
        self.loading_animation = QMovie("files/loading.gif")
        self.loading_animation.setScaledSize(QSize(32,32))
        

        self.resize(1000, 700)
        self.setFont(self.default_font)
        self.setWindowTitle("AMOS - Automatic Meteor Observation System")
        self.setWindowIcon(self.app_icon)
        self.setObjectName("AmosWindow")
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
        self.video_thumb_label.setObjectName("video_thumb_label")
        self.video_thumb_label.setFont(self.font_bold_10)

        self.video_thumb = QLabel(self.centralwidget)
        self.video_thumb.move(405, 135)
        self.video_thumb.resize(192,108)
        self.video_thumb.setPixmap(QPixmap("files/default_thumbnail.png"))
        self.video_thumb.setScaledContents(True)
        self.video_thumb.setObjectName("video_thumb")


        #File selection section
        self.file_selection_widget = QWidget(self.centralwidget)
        self.file_selection_widget.setGeometry(20, 240, 741, 151)
        self.file_selection_grid = QGridLayout(self.file_selection_widget)
        self.file_selection_grid.setContentsMargins(0, 0, 0, 0)        

        self.video_selection_status = QLabel(self.file_selection_widget)
        self.video_selection_status.setObjectName("video_selection_status")
        self.video_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
        self.xml_selection_status = QLabel(self.file_selection_widget)
        self.xml_selection_status.setObjectName("xml_selection_status")
        self.xml_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
        self.folder_selection_status = QLabel(self.file_selection_widget)
        self.folder_selection_status.setObjectName("folder_selection_status")
        self.folder_selection_status.setPixmap(QPixmap("files/cross_icon.png"))

        spacer_status_browse = QSpacerItem(60, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.browse_video_button = QPushButton(self.file_selection_widget)
        self.browse_video_button.setFont(self.font_bold_10)
        self.browse_video_button.setObjectName("browse_video_button")
        self.browse_video_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.browse_xml_button = QPushButton(self.file_selection_widget)
        self.browse_xml_button.setFont(self.font_bold_10)
        self.browse_xml_button.setObjectName("browse_xml_button")
        self.browse_xml_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.browse_folder_button = QPushButton(self.file_selection_widget)
        self.browse_folder_button.setFont(self.font_bold_10)
        self.browse_folder_button.setObjectName("browse_folder_button")
        self.browse_folder_button.setCursor(QCursor(Qt.PointingHandCursor))

        spacer_browse_path = QSpacerItem(60, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.videopath_label = Drop_Label(self.file_selection_widget)
        self.videopath_label.defineType("video")
        self.videopath_label.setFont(self.default_font)
        self.videopath_label.setAlignment(Qt.AlignCenter)
        self.videopath_label.setObjectName("videopath_label")
        self.xmlpath_label = Drop_Label(self.file_selection_widget)
        self.xmlpath_label.defineType("xml")
        self.xmlpath_label.setFont(self.default_font)
        self.xmlpath_label.setAlignment(Qt.AlignCenter)
        self.xmlpath_label.setObjectName("xmlpath_label")
        self.folderpath_label = Drop_Label(self.file_selection_widget)
        self.folderpath_label.defineType("folder")
        self.folderpath_label.setFont(self.default_font)
        self.folderpath_label.setAlignment(Qt.AlignCenter)
        self.folderpath_label.setObjectName("folderpath_label")
        
        self.delete_video_selection_button = QPushButton(self.file_selection_widget)
        self.delete_video_selection_button.setObjectName("delete_video_selection_button")
        self.delete_video_selection_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_xml_selection_button = QPushButton(self.file_selection_widget)
        self.delete_xml_selection_button.setObjectName("delete_xml_selection_button")
        self.delete_xml_selection_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_folder_selection_button = QPushButton(self.file_selection_widget)
        self.delete_folder_selection_button.setObjectName("delete_folder_selection_button")
        self.delete_folder_selection_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.file_selection_grid.addWidget(self.video_selection_status, 0, 0, 1, 1)
        self.file_selection_grid.addWidget(self.xml_selection_status, 1, 0, 1, 1)
        self.file_selection_grid.addWidget(self.folder_selection_status, 2, 0, 1, 1)
        self.file_selection_grid.addItem(spacer_status_browse, 0, 1, 3, 1)
        self.file_selection_grid.addWidget(self.browse_video_button, 0, 2, 1, 1)
        self.file_selection_grid.addWidget(self.browse_xml_button, 1, 2, 1, 1)
        self.file_selection_grid.addWidget(self.browse_folder_button, 2, 2, 1, 1)
        self.file_selection_grid.addItem(spacer_browse_path, 0, 3, 3, 1)
        self.file_selection_grid.addWidget(self.videopath_label, 0, 4, 1, 1)
        self.file_selection_grid.addWidget(self.xmlpath_label, 1, 4, 1, 1)
        self.file_selection_grid.addWidget(self.folderpath_label, 2, 4, 1, 1)
        self.file_selection_grid.addWidget(self.delete_video_selection_button, 0, 5, 1, 1)
        self.file_selection_grid.addWidget(self.delete_xml_selection_button, 1, 5, 1, 1)
        self.file_selection_grid.addWidget(self.delete_folder_selection_button, 2, 5, 1, 1)

        #Defaults section
        self.defaults_group = QGroupBox(self.centralwidget)
        self.defaults_group.setGeometry(430, 20, 480, 80)
        self.defaults_group.setFont(self.font_normal_10)
        self.defaults_group.setFlat(True)
        
        self.apply_defaults_button = QPushButton(self.defaults_group)
        self.apply_defaults_button.setGeometry(20, 30, 130, 33)
        self.apply_defaults_button.setFont(self.font_bold_9)
        self.apply_defaults_button.setObjectName("apply_defaults_button")
        self.apply_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.set_defaults_button = QPushButton(self.defaults_group)
        self.set_defaults_button.setGeometry(160, 30, 120, 33)
        self.set_defaults_button.setFont(self.font_bold_9)
        self.set_defaults_button.setObjectName("set_defaults_button")
        self.set_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_defaults_button = QPushButton(self.defaults_group)
        self.delete_defaults_button.setGeometry(290, 30, 140, 33)
        self.delete_defaults_button.setFont(self.font_bold_9)
        self.delete_defaults_button.setObjectName("delete_defaults_button")
        self.delete_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.help_defaults_button = QPushButton(self.centralwidget)
        self.help_defaults_button.setGeometry(870, 25, 32, 32)
        self.help_defaults_button.setText("?")
        self.help_defaults_button.setFont(self.font_bold_14)
        self.help_defaults_button.setObjectName("help_defaults_button")
        self.help_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        #Analyse section
        self.analyse_widget = QWidget(self.centralwidget)
        self.analyse_widget.setGeometry(20, 400, 751, 71)
        self.analyse_layout = QHBoxLayout(self.analyse_widget)
        self.analyse_layout.setContentsMargins(0, 0, 0, 0)

        self.analysation_status_image = QLabel(self.analyse_widget)
        self.analysation_status_image.setPixmap(QPixmap("files/cross_icon.png"))

        spacer_status_analyse = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.analyse_button = QPushButton(self.analyse_widget)
        self.analyse_button.setFont(self.font_bold_15)
        self.analyse_button.setObjectName("analyse_button")
        self.analyse_button.setMinimumWidth(170)
        self.analyse_button.setMinimumHeight(50)
        self.analyse_button.setCursor(QCursor(Qt.PointingHandCursor))

        spacer_analyse_progress = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.analysation_progressbar = QProgressBar(self.analyse_widget)
        self.analysation_progressbar.setStyleSheet("color:white;")
        self.analysation_progressbar.setProperty("value", 0)

        self.analyse_layout.addWidget(self.analysation_status_image)
        self.analyse_layout.addItem(spacer_status_analyse)
        self.analyse_layout.addWidget(self.analyse_button)
        self.analyse_layout.addItem(spacer_analyse_progress)        
        self.analyse_layout.addWidget(self.analysation_progressbar)

        #Spreadsheet section
        self.spreadsheet_group = QGroupBox(self.centralwidget)
        self.spreadsheet_group.setGeometry(20, 520, 480, 81)
        self.spreadsheet_group.setFont(self.font_normal_10)
        self.spreadsheet_group.setFlat(True)
        
        self.open_spreadsheet_button = QPushButton(self.spreadsheet_group)
        self.open_spreadsheet_button.setGeometry(20, 30, 250, 32)
        self.open_spreadsheet_button.setFont(self.font_bold_9)
        self.open_spreadsheet_button.setObjectName("open_spreadsheet_button")
        self.open_spreadsheet_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_spreadsheet_button = QPushButton(self.spreadsheet_group)
        self.save_spreadsheet_button.setGeometry(300, 30, 150, 32)
        self.save_spreadsheet_button.setFont(self.font_bold_9)
        self.save_spreadsheet_button.setObjectName("save_spreadsheet_button")
        self.save_spreadsheet_button.setCursor(QCursor(Qt.PointingHandCursor))
        
        #Setup the central widget
        self.setCentralWidget(self.centralwidget)

        #Add a menubar
        self.menubar = QMenuBar(self)
        self.filemenu = QMenu(self.menubar)
        self.setMenuBar(self.menubar)

        self.actionSettings = QAction(self)
        self.actionQuit = QAction(self)

        self.filemenu.addAction(self.actionSettings)
        self.filemenu.addSeparator()
        self.filemenu.addAction(self.actionQuit)
        self.menubar.addAction(self.filemenu.menuAction())

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
        self.actionSettings.setText("Settings")
        self.actionSettings.setShortcut("Ctrl+Shift+P")
        self.actionQuit.setText("Quit")
        self.actionQuit.setShortcut("Ctrl+Q")

        self.browse_video_button.clicked.connect(self.get_video_location)
        self.browse_xml_button.clicked.connect(self.get_xml_location)
        self.browse_folder_button.clicked.connect(self.get_folder_location)
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

    def setup_video_selection(self, videopath_list):
        self.videopath_list = videopath_list
        if self.videopath_list != []: #If the user didn't cancel the selection
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
            thumbnail = get_thumbnail(self.videopath_list[0])
            height, width, channel = thumbnail.shape
            bytesPerLine = 3 * width
            video_thumbnail = QImage(thumbnail.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
            self.video_thumb.setPixmap(QPixmap(video_thumbnail))

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
            self.videopath_label.setText('Please press "Browse or drag & drop a video to select it')
            self.video_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
            del self.videopath_list
            self.video_thumb.setPixmap(QPixmap("files/default_thumbnail.png"))
            self.video_selection_status.setToolTip("Status:\nNot yet completed!")
        except AttributeError:
            pass

    def delete_xml_selection(self):
        try:
            self.xmlpath_label.setText('Please press "Browse" or drag & drop a video to select it')
            self.xml_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
            del self.xmlpath_list
            self.xml_selection_status.setToolTip("Status:\nNot yet completed!")
        except AttributeError:
            pass
    
    def delete_folder_selection(self):
        try:
            self.folderpath_label.setText('Please press "Browse" or drag & drop a video to select it')
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

        x = help_defaults_message.exec_()
    
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

            x = self.open_spreadsheet_message.exec_()
    
    def analyse(self):
        try:
            for i in range(len(self.videopath_list)):
                print(self.videopath_list)
                print(self.xmlpath_list)
                print(self.VideoID_List)
                analyse(self.videopath_list[i],self.xmlpath_list[i],self.folderpath, self.VideoID_List[i], Window)
            self.analysation_status_image.setPixmap(QPixmap("files/check_icon.png"))
            self.analysation_status_image.setToolTip("Status:\nCompleted!")
        except AttributeError as a:
            print(a)
            self.analyse_error_message = QMessageBox()
            self.analyse_error_message.setWindowTitle("File selection missing!")
            self.analyse_error_message.setText('The analysation algorithm needs three infos:\n    1. The video to process.\n    2. The corresponding XML file to get information like the \n        duration, resolution and frame rate.\n    3. The folder where it saves images of frames with meteors \n        and the spreadsheet.')
            self.analyse_error_message.setInformativeText('<h3><strong>To select these infos, press the blue "Browse" buttons.</strong></h3>')
            self.analyse_error_message.setIcon(QMessageBox.Critical)
            self.analyse_error_message.setStandardButtons(QMessageBox.Close)

            x = self.analyse_error_message.exec_()

    def save_spreadsheet(self):
        try:
            save_spreadsheet(Window)
            self.spreadsheet_sucess_message = QMessageBox()
            self.spreadsheet_sucess_message.setWindowTitle("Saved succesfully!")
            self.spreadsheet_sucess_message.setText('Spreadsheet saved succesfully!')
            self.spreadsheet_sucess_message.setIcon(QMessageBox.Information)
            self.spreadsheet_sucess_message.setStandardButtons(QMessageBox.Ok)

            x = self.spreadsheet_sucess_message.exec_()

        except PermissionError:
            self.spreadsheet_opened_error = QMessageBox()
            self.spreadsheet_opened_error.setWindowTitle("Spreadsheet still opened!")
            self.spreadsheet_opened_error.setText('You have your spreadsheet still opened! Close it and press "Save spreadsheet" again, otherwise ALL DATA WILL BE LOST!')
            self.spreadsheet_opened_error.setIcon(QMessageBox.Warning)
            self.spreadsheet_opened_error.setStandardButtons(QMessageBox.Close)

            x = self.spreadsheet_opened_error.exec_()

        except NameError:
            self.spreadsheet_not_able_to_save = QMessageBox()
            self.spreadsheet_not_able_to_save.setWindowTitle("Data missing!")
            self.spreadsheet_not_able_to_save.setText('Please run the analysation before saving the spreadsheet.')
            self.spreadsheet_not_able_to_save.setIcon(QMessageBox.Warning)
            self.spreadsheet_not_able_to_save.setStandardButtons(QMessageBox.Close)

            x = self.spreadsheet_not_able_to_save.exec_()
    
    def apply_defaults(self):
        apply_defaults(Window)

    def set_defaults(self):
        set_defaults(Window)

    def delete_defaults(self):
        delete_defaults(Window)


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
app = QApplication(sys.argv)
app.setStyleSheet(StyleSheet)

Window = AmosWindow()
Window.show()

sys.exit(app.exec_())