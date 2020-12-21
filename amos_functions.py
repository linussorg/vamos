# Importing all modules
from datetime import timedelta
from xml.dom import minidom

import cv2
import datetime
import json
import numpy
import os
import shutil
import statistics
from PyQt5.QtCore import QTime, Qt
# from bokeh.plotting import figure, show, output_file
# from bokeh.models import HoverTool, ColumnDataSource
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
from filevideostream import FileVideoStream


def check_pos(first, second, thresh):
    f_x = first[0]
    f_y = first[1]
    s_x = second[0]
    s_y = second[1]
    if thresh >= f_x - s_x >= -thresh:
        if thresh >= f_y - s_y >= -thresh:
            return True
        else:
            return False
    else:
        return False


def analyse(videopath, xmlpath, folderpath, VideoID, Window, use_xml):
    """
    Analyse a video. 
    
    videopath(String): Full path to the processed video. 
    
    xmlpath(String): Full path to the XML File. 
    
    folderpath(String): Full path to the folder to store results in. 
    
    VideoID(String): ID of the processing video. 
    
    Window(Qt Window object): The Window where the UI for the analysation is in.
    
    use_xml(Bool): Whether to use an xml file for the video starting time.
    """

    # Reading Files
    if os.path.isfile(videopath):
        video = FileVideoStream(path=videopath, start_frame=Window.start_frame).start()
    else:
        video_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected Video does not exist.")
        video_not_found.setWindowTitle("Video not found")
        video_not_found.exec_()
        return False, {}, []

    with open("files/settings.txt", "r") as settings_file:
        settings = json.loads(settings_file.read())
        blur, x_grid, y_grid, thresh_value, thresh_max_brightness, dilate, max_meteors, min_area, max_area, \
            signal_label, sort_out_area_difference, max_length, min_length, resolution_to_write = settings[:-4]

    # black = cv2.imread('files/black.png', 0)

    try:
        os.rename(src=f'{folderpath}/frames', dst=f'{folderpath}/remove')
        os.rename(src=f'{folderpath}/thrash', dst=f'{folderpath}/remove2')
    except WindowsError:
        pass

    shutil.rmtree(f'{folderpath}/remove', ignore_errors=True)
    shutil.rmtree(f'{folderpath}/remove2', ignore_errors=True)

    try:
        os.mkdir(f'{folderpath}/frames')
        os.mkdir(f'{folderpath}/thrash')
    except FileExistsError:
        pass

    # Defining the variable for the reference frame
    ref_frame = None

    global position_names
    position_names = []
    global MeteorID_List
    MeteorID_List = []
    rotation_list = []
    meteor_area_list = []
    pause_analysation = False

    status_list = [None, None]
    times = []
    sort_out_list = []

    length = Window.length
    fps = Window.Fps
    Height = Window.Height
    Width = Window.Width

    if use_xml:
        # Reading and processing the XML-file
        try:
            xml_file = minidom.parse(xmlpath)
        except FileNotFoundError:
            xml_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected XML file does not exist.")
            xml_not_found.setWindowTitle("XML not found")
            xml_not_found.exec_()
            return False, {}, []
        try:
            creation_date = xml_file.getElementsByTagName('CreationDate')
            creation_date = creation_date[0].attributes['value'].value

            year, month, day, hour, minute, second = int(creation_date[:4]), int(creation_date[5:7]), int(
                creation_date[8:10]), int(creation_date[11:13]), int(creation_date[14:16]), int(creation_date[17:19])
        except IndexError:
            xml_not_valid = QMessageBox(icon=QMessageBox.Critical,
                                        text='The selected XML file is not valid, the key "creationDate" and its '
                                             'value is missing.')
            xml_not_valid.setWindowTitle("XML not valid")
            xml_not_valid.exec_()
            return False, {}, []

        base_time = datetime.datetime(year, month, day, hour, minute, second)
    else:
        base_time = Window.base_time

    beginning_video_time = datetime.datetime(1, 1, 1, 0, 0, 0)

    len_mul = Height // 1080
    ar_mul = len_mul ** 2

    # Defining the variable for the current frame
    frame_number = Window.start_frame
    # video.set(cv2.CAP_PROP_POS_FRAMES, Window.start_frame)

    # Processing the Excel-File
    sheet = Window.sheet
    detection_count = 0

    meteor_data = {}

    Window.analysation_status_image.setMovie(Window.loading_animation)
    Window.loading_animation.start()

    Window.analysation_progressdialog = QProgressDialog(
        "Analysing the video... \n\nEstimated remaining time: \nCalculating...", "Exit", 1, 100, Window)
    Window.analysation_progressdialog.setWindowTitle("Analysing...")
    Window.analysation_progressdialog.setMinimumWidth(500)
    Window.analysation_progressdialog.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
    Window.analysation_progressdialog.setObjectName("default_widget")

    t = QTime()
    t.start()
    frames_since_reset = 1

    for i in range(length - Window.start_frame):
        frames_since_reset += 1
        if frame_number % 100 == 0:
            t.restart()
            frames_since_reset = 1
        progress_percent = frame_number / length * 100
        Window.analysation_progressdialog.setValue(progress_percent)
        Window.remaining_seconds = round((length - frame_number) * ((t.elapsed() / frames_since_reset) / 1000)) + 1
        Window.remaining_time = str(datetime.timedelta(seconds=Window.remaining_seconds))
        Window.analysation_progressdialog.setLabelText(
            f"Analysing the video... \n\nEstimated remaining time: \n{Window.remaining_time} s")

        # Reading current frame
        frame = video.read()

        # Calculating the time
        current_seconds = frame_number / fps

        time = base_time + timedelta(seconds=current_seconds)

        if pause_analysation:
            # Resize the main window to match the screen size
            frameResized = cv2.resize(frame, (1280, 720))

            # Writing the text for the time, date and frame number
            cv2.putText(frameResized, str(time)[:-5], (20, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, str(frame_number), (1220, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1,
                        cv2.LINE_AA)

            # Drawing and writing the text for the grid
            cv2.putText(frameResized, 'A', (70, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frameResized, 'B', (70 + 160, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, 'C', (70 + 320, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, 'D', (70 + 480, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, 'E', (70 + 640, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, 'F', (70 + 800, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, 'G', (70 + 960, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, 'H', (70 + 1120, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, '1', (15, 80), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frameResized, '2', (15, 80 + 144), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, '3', (15, 80 + 288), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, '4', (15, 80 + 432), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frameResized, '5', (15, 80 + 576), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)

            cv2.putText(frameResized,
                        'Press "esc" to exit, "P" to pause the analysation and "R" to set a new reference frame',
                        (300, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.imshow('AMOS - Analysation', frameResized)
            key = cv2.waitKey(1)

            if key == 27 or Window.analysation_progressdialog.wasCanceled():
                Window.broke_frame = frame_number
                break

            if key == ord('p'):
                pause_analysation = not pause_analysation

            frame_number += 1
            continue

        # Reset variables
        status = 0

        # Preparing the Video for calculations
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (blur * len_mul + 1, 20 * len_mul + 1), 0)

        if ref_frame is None:
            ref_frame = gray
            status_list = [0]
            frame_number += 1
            continue
        if frame_number % 1000 == 0:
            ref_frame = gray

        width = Width // x_grid
        height = Height // y_grid
        for v in range(y_grid):
            move = v * height
            for h in range(x_grid):
                cv2.rectangle(frame, (width * h, move), (width * (h + 1), move + height), (100, 100, 100), 1)

        # Calculating the difference between the current frame and the reference frame
        delta_frame = cv2.absdiff(ref_frame, gray)

        thresh_delta = cv2.threshold(delta_frame, thresh_value, thresh_max_brightness, cv2.THRESH_BINARY)[1]

        thresh_delta = cv2.dilate(thresh_delta, None, iterations=dilate)

        (cnts, _) = cv2.findContours(thresh_delta.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Drawing boxes around areas that are meteors
        if len(cnts) > max_meteors:
            ref_frame = gray
            print(f"Frame was reset because more than {max_meteors} {signal_label}s")
            frame_number += 1
            continue
        else:
            for contour in cnts:
                if cv2.contourArea(contour) < min_area * ar_mul or cv2.contourArea(contour) > max_area * ar_mul:
                    continue
                status = 1
                detection_count += 1
                meteor_area_list.append(cv2.contourArea(contour))
                rect = cv2.minAreaRect(contour)
                rotation_list.append(rect[2])
                (x, y, w, h) = cv2.boundingRect(contour)
                border = 10 * len_mul
                text_border = 20 * len_mul
                cv2.rectangle(frame, (x - border, y - border), (x + w + border, y + h + border), (255, 255, 255), 2)
                cv2.putText(frame, signal_label, (x - border, y - text_border), cv2.FONT_HERSHEY_SIMPLEX, 1 * len_mul,
                            (100, 255, 0), 1, cv2.LINE_AA)
                average_x = x + (w // 2)
                average_y = y + (h // 2)
                meteor_data[f"signal_{detection_count}"] = {
                    "VideoID": VideoID,
                    "position": (average_x, average_y),
                    "frame": [frame_number],
                    "area": cv2.contourArea(contour),
                    "rotation": rect[2],
                }

        # Return if a meteor was detected
        status_list.append(status)
        status_list = status_list[-3:]

        if i != 1:
            try:
                diff = cv2.absdiff(thresh_delta, thresh_delta_previous)
                diff_px = numpy.sum(diff == 255)
                if 0 < diff_px < sort_out_area_difference * ar_mul and status_list[-1] == 1 and \
                        status_list[-2] == 1:
                    sort_out_list.append(frame_number)
                    print(frame_number, diff_px)
                    cv2.imwrite(f"{folderpath}/thrash/{frame_number}_frame.png", frameResized)
            except UnboundLocalError:
                thresh_delta_previous = thresh_delta
                diff = cv2.absdiff(thresh_delta, thresh_delta_previous)

        thresh_delta_previous = thresh_delta

        # Return the Start and End time of the meteor
        if status_list[-1] == 1 and status_list[-2] == 0:  # If the meteor appeared
            Window.meteor_count += 1
            times.append(time)

            start_meteor = [average_x, average_y]

            width_box = Width // x_grid
            height_box = Height // y_grid

            x_names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P"]

            for index in range(x_grid):
                if start_meteor[0] > (index + 1) * width_box:
                    continue
                x_position_name = x_names[index]
                break

            for index in range(y_grid):
                if start_meteor[1] > (index + 1) * height_box:
                    continue
                y_position_name = str(index + 1)
                break

            Position_name = x_position_name + y_position_name

            position_names.append(Position_name)
            position_names.append(Position_name)

            current_meteor_start = base_time + timedelta(seconds=current_seconds)

            row_number = Window.meteor_count + 1
            cell = sheet.cell(row_number, 1)
            MeteorID = "M-" + "%07d" % Window.meteor_count
            MeteorID_List.append(MeteorID)
            MeteorID_List.append(MeteorID)
            MeteorID_List.append(MeteorID)
            cell.value = MeteorID

            cell = sheet.cell(row_number, 2)
            cell.value = str(base_time)[-8:]

            cell = sheet.cell(row_number, 3)
            cell.value = VideoID

            cell = sheet.cell(row_number, 4)
            cell.value = str(beginning_video_time + timedelta(seconds=current_seconds))[11:]

            cell = sheet.cell(row_number, 6)
            cell.value = str(current_meteor_start)[11:]

            cell = sheet.cell(row_number, 11)
            cell.value = Position_name

            cell = sheet.cell(row_number, 12)
            cell.value = str(current_meteor_start)[:10]

        if status_list[-1] == 0 and status_list[-2] == 1:  # If the meteor disappeared
            current_meteor_end = base_time + timedelta(seconds=current_seconds)
            meteor_length = current_meteor_end - current_meteor_start

            if meteor_length > timedelta(seconds=max_length) or meteor_length < timedelta(seconds=min_length):
                Window.meteor_count += -1
                times.pop()  # Remove the beginning from the list
                position_names.pop()
                position_names.pop()
                sheet.delete_rows(row_number)
            else:
                times.append(time)

                cell = sheet.cell(row_number, 5)
                cell.value = str(beginning_video_time + timedelta(seconds=current_seconds))[11:]

                cell = sheet.cell(row_number, 7)
                cell.value = str(current_meteor_end)[11:]

                cell = sheet.cell(row_number, 8)
                cell.value = str(current_meteor_end - current_meteor_start)

                cell = sheet.cell(row_number, 9)
                meteor_area_list = sorted(meteor_area_list)
                Meteor_area = meteor_area_list[-1]
                Meteor_area = round(Meteor_area)
                cell.value = Meteor_area

                cell = sheet.cell(row_number, 10)
                rot_average = statistics.mean(rotation_list)
                cell.value = str(round(rot_average))

                rotation_list.clear()
                meteor_area_list.clear()

        # Resize the main window to match the screen size
        frameResized = cv2.resize(frame, (1280, 720))

        # Writing the text for the time, date and frame number
        cv2.putText(frameResized, str(time)[:-5], (20, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1,
                    cv2.LINE_AA)
        cv2.putText(frameResized, str(frame_number), (1220, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1,
                    cv2.LINE_AA)

        # Drawing and writing the text for the grid
        cv2.putText(frameResized, 'A', (70, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, 'B', (70 + 160, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, 'C', (70 + 320, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, 'D', (70 + 480, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, 'E', (70 + 640, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, 'F', (70 + 800, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, 'G', (70 + 960, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, 'H', (70 + 1120, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, '1', (15, 80), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, '2', (15, 80 + 144), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, '3', (15, 80 + 288), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, '4', (15, 80 + 432), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frameResized, '5', (15, 80 + 576), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

        if status == 1:
            frame_to_write = cv2.resize(frameResized, tuple(resolution_to_write))
            frame_to_write = cv2.cvtColor(frame_to_write, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(f"{folderpath}/frames/{frame_number}_frame.png", frame_to_write)

        cv2.putText(frameResized,
                    'Press "esc" to exit, "P" to pause the analysation and "R" to set a new reference frame',
                    (300, 700),
                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        # Resize windows for stack
        # gray_resized = cv2.resize(gray, (864, 486))
        # thresh_resized = cv2.resize(thresh_delta, (864, 486))
        # delta_resized = cv2.resize(delta_frame, (864, 486))
        # black_resized = cv2.resize(black, (864, 486))

        # Stack the Windows that provide extra detail
        # stack1 = numpy.hstack([gray_resized, thresh_resized])
        # stack2 = numpy.hstack([delta_resized, black_resized])
        # stack = numpy.vstack([stack1, stack2])
        # cv2.rectangle(stack, (0, 0), (864, 486), (255, 255, 255), 1)
        # cv2.rectangle(stack, (0, 486), (864, 971), (255, 255, 255), 1)
        # cv2.rectangle(stack, (864, 0), (1727, 486), (255, 255, 255), 1)
        # cv2.putText(stack, 'Difference', (350, 520), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        # cv2.putText(stack, 'Capturing', (350, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        # cv2.putText(stack, 'Threshold', (1250, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

        # Opening windows for visualization
        cv2.imshow('AMOS - Analysation', frameResized)

        try:
            cv2.imshow('AMOS - Difference', diff)
        except UnboundLocalError:
            pass
        # cv2.imshow('Additional details - AMOS', stack)

        key = cv2.waitKey(1)

        if key == 27 or Window.analysation_progressdialog.wasCanceled():
            if status == 1:
                times.append(time)

                current_meteor_end = base_time + timedelta(seconds=current_seconds)

                cell = sheet.cell(row_number, 5)
                cell.value = str(beginning_video_time + timedelta(seconds=current_seconds))[11:]

                cell = sheet.cell(row_number, 7)
                cell.value = str(current_meteor_end)[11:]

                cell = sheet.cell(row_number, 8)
                cell.value = str(current_meteor_end - current_meteor_start)
            Window.broke_frame = frame_number
            break

        if key == ord('r'):
            ref_frame = gray
            print("Frame reset because of key pressed.")

        if key == ord('p'):
            print(pause_analysation)
            pause_analysation = True

        frame_number += 1

    Window.analysation_progressdialog.setValue(100)

    video.stop()

    # Close all Windows
    cv2.destroyWindow('AMOS - Analysation')
    cv2.destroyWindow('AMOS - Additional details')
    cv2.destroyWindow('AMOS - Difference')

    print(sort_out_list)
    print(meteor_data)

    return True, meteor_data, sort_out_list, convert_datetime(base_time)


# def generate_diagram():
#     #Preparing the Pandas Dataframe
#     df=pandas.DataFrame(columns=["Start","End"])
#
#     #Calculating values and plotting the Chart
#     for i in range(0,len(times),2):
#         print('iteration')
#         df=df.append({"Start":times[i],"End":times[i+1],"Position":position_names[i],"MeteorID":MeteorID_List[i]},ignore_index=True)
#
#     df.to_csv(f'{folderpath}/Results.csv')
#
#     #try:
#     df["Start_string"]=df["Start"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
#     df["End_string"]=df["End"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
#
#     cds=ColumnDataSource(df)
#
#     p=figure(x_axis_type='datetime',height=100, Width=500, title='Meteors', toolbar_location="below")
#     p.axis.visible = False
#     p.yaxis.minor_tick_line_color=None
#     p.ygrid[0].ticker.desired_num_ticks=1
#
#     hover=HoverTool(tooltips=[("Meteor-ID", "@MeteorID"),("Position", "@Position"),
#                               ("Start", "@Start_string"),("End", "@End_string")])
#     p.add_tools(hover)
#
#     q=p.quad(left="Start", right="End", bottom=0, top=1, color="black", source=cds)
#
#     output_file("Meteor_diagram.html")
#     show(p)
#     #except AttributeError:
#         #print("No meteors found yet!")

def save_spreadsheet(Window):
    Window.wb.save(f'{Window.folderpath}/Results.xlsx')


def apply_defaults(Window):
    with open("files/defaults.txt", "r") as defaults_file:
        defaults = json.loads(defaults_file.read())

    if defaults[0] == [] or defaults[1] == [] or defaults[2] == "None":
        set_defaults_now = QMessageBox.question(Window, "No defaults yet!",
                                                "You have not set any defaults yet. Do you want to set them now?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if set_defaults_now == QMessageBox.Yes:
            set_defaults(Window)
    else:
        Window.videopath_list, Window.xmlpath_list, Window.folderpath = defaults
        Window.setup_video_selection(Window.videopath_list)
        Window.setup_xml_selection(Window.xmlpath_list)
        Window.setup_folder_selection(Window.folderpath)


def set_defaults(Window):
    select_video_info = QMessageBox(icon=QMessageBox.Information,
                                    text="In the following dialog, select your default video(s).")
    select_video_info.setWindowTitle("Info")
    select_video_info.exec_()

    Window.default_videopath_list = QFileDialog.getOpenFileNames(parent=Window, filter="MP4 Files (*.mp4)")
    Window.default_videopath_list = Window.default_videopath_list[0]
    if Window.default_videopath_list:  # If the user didn't cancel the selection
        select_xml_info = QMessageBox(icon=QMessageBox.Information,
                                      text="In the following dialog, select your default XML(s).")
        select_xml_info.setWindowTitle("Info")
        select_xml_info.exec_()

        Window.default_xmlpath_list = QFileDialog.getOpenFileNames(parent=Window, filter="XML Files (*.xml)")
        Window.default_xmlpath_list = Window.default_xmlpath_list[0]
        if Window.default_xmlpath_list:  # If the user didn't cancel the selection
            select_folder_info = QMessageBox(icon=QMessageBox.Information,
                                             text="In the following dialog, select your default folder to store "
                                                  "results in.")
            select_folder_info.setWindowTitle("Info")
            select_folder_info.exec_()

            Window.default_folderpath = QFileDialog.getExistingDirectory(parent=Window)
            if Window.default_folderpath != "":  # If the user didn't cancel the selection
                default_paths = [Window.default_videopath_list, Window.default_xmlpath_list, Window.default_folderpath]
                with open("files/defaults.txt", "w") as defaults_file:
                    defaults_file.write(json.dumps(default_paths))

                set_defaults_success_message = QMessageBox(icon=QMessageBox.Information,
                                                           text="Defaults set successfully!")
                set_defaults_success_message.setWindowTitle("Info")
                set_defaults_success_message.exec_()


def delete_defaults(Window):
    delete_continue = QMessageBox.question(Window, "Do you want to delete?",
                                           "Are you sure that you want to delete the defaults?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

    if delete_continue == QMessageBox.Yes:
        none_content = [[], [], "None"]
        with open("files/defaults.txt", "w") as defaults_file:
            defaults_file.write(json.dumps(none_content))

        set_defaults_success_message = QMessageBox(icon=QMessageBox.Information, text="Defaults deleted successfully!")
        set_defaults_success_message.setWindowTitle("Info")
        set_defaults_success_message.exec_()


def get_thumbnail(path):
    if os.path.isfile(path):
        vid = FileVideoStream(path).start()
    else:
        video_not_found = QMessageBox(icon=QMessageBox.Critical, text="One of the videos was not found!")
        video_not_found.setWindowTitle("Video not found")
        video_not_found.exec_()
        return numpy.array(None)
    thumbnail = vid.read()
    vid.stop()
    thumbnail = cv2.resize(thumbnail, (240, 135))
    return thumbnail


def generate_results(Window, meteor_data, sort_out_list, len_mul):
    if meteor_data == {}:
        return {}

    with open("files/settings.txt", "r") as settings_file:
        settings = json.loads(settings_file.read())
        min_length, max_length, _, max_distance, max_frames, delete_threshold, delete_percentage = settings[-7:]
    meteors = {}
    x_positions_list = []
    y_positions_list = []
    area_list = []
    rotation_list = []
    meteor_list_count = 1

    for key in meteor_data.keys():
        if key[0] == "V":
            continue
        if key == "signal_1":
            current_position = meteor_data[key]['position']
            current_frame = meteor_data[key]['frame']
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            area_list.append(meteor_data[key]['area'])
            rotation_list.append(meteor_data[key]['rotation'])
            signal_time = (datetime.datetime.fromtimestamp(current_frame[0] / Window.Fps) - timedelta(hours=1)).time()
            current_video_id = meteor_data[key]['VideoID']
            current_time = datetime.datetime(*meteor_data[current_video_id]) + timedelta(
                seconds=current_frame[0] / Window.Fps)
            meteors["M-" + "%07d" % meteor_list_count] = {
                "VideoID": current_video_id,
                "position": current_position,
                "frames": current_frame,
                "beginning": [convert_datetime(current_time.time()),
                              convert_datetime(signal_time)],
                "end": [],
                "duration": [],
                "area": meteor_data[key]['area'],
                "rotation": meteor_data[key]['rotation'],
                "date": convert_datetime(current_time.date())
            }
            continue
        previous_position = current_position
        current_position = meteor_data[key]['position']
        current_frame = meteor_data[key]['frame']
        if check_pos(current_position, previous_position, max_distance * len_mul):
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            area_list.append(meteor_data[key]['area'])
            rotation_list.append(meteor_data[key]['rotation'])
            meteors["M-" + "%07d" % meteor_list_count]["frames"].append(meteor_data[key]['frame'][0])
            signal_time = (datetime.datetime.fromtimestamp(current_frame[0] / Window.Fps) - timedelta(hours=1)).time()
            current_time = datetime.datetime(*meteor_data[current_video_id]) + timedelta(
                seconds=current_frame[0] / Window.Fps)
        else:
            meteors["M-" + "%07d" % meteor_list_count]["position"] = (
                int(statistics.mean(x_positions_list)), int(statistics.mean(y_positions_list)))
            meteors["M-" + "%07d" % meteor_list_count]["frames"] = sorted(
                set(meteors["M-" + "%07d" % meteor_list_count]["frames"]))
            meteors["M-" + "%07d" % meteor_list_count]["rotation"] = abs(round(statistics.mean(rotation_list)))
            meteors["M-" + "%07d" % meteor_list_count]["area"] = sorted(area_list)[-1]
            meteors["M-" + "%07d" % meteor_list_count]["end"] = [convert_datetime(current_time.time()),
                                                                 convert_datetime(signal_time)]
            current_duration = current_time - datetime.datetime(
                *meteors["M-" + "%07d" % meteor_list_count]["date"],
                *meteors["M-" + "%07d" % meteor_list_count]["beginning"][0]
            )
            meteors["M-" + "%07d" % meteor_list_count]["duration"] = [int(
                current_duration.total_seconds() * Window.Fps), convert_datetime(current_duration)]
            x_positions_list.clear()
            y_positions_list.clear()
            area_list.clear()
            rotation_list.clear()
            meteor_list_count += 1
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            area_list.append(meteor_data[key]['area'])
            rotation_list.append(meteor_data[key]['rotation'])
            signal_time = (datetime.datetime.fromtimestamp(current_frame[0] / Window.Fps) - timedelta(hours=1)).time()
            current_video_id = meteor_data[key]['VideoID']
            current_time = datetime.datetime(*meteor_data[current_video_id]) + timedelta(
                seconds=current_frame[0] / Window.Fps)
            meteors["M-" + "%07d" % meteor_list_count] = {
                "VideoID": current_video_id,
                "position": current_position,
                "frames": current_frame,
                "beginning": [convert_datetime(current_time.time()),
                              convert_datetime(signal_time)],
                "end": [],
                "duration": [],
                "area": meteor_data[key]['area'],
                "rotation": meteor_data[key]['rotation'],
                "date": convert_datetime(current_time.date())
            }

    meteors["M-" + "%07d" % meteor_list_count]["position"] = (
        int(statistics.mean(x_positions_list)), int(statistics.mean(y_positions_list)))
    meteors["M-" + "%07d" % meteor_list_count]["frames"] = sorted(
        set(meteors["M-" + "%07d" % meteor_list_count]["frames"]))
    meteors["M-" + "%07d" % meteor_list_count]["rotation"] = abs(round(statistics.mean(rotation_list)))
    meteors["M-" + "%07d" % meteor_list_count]["area"] = sorted(area_list)[-1]
    meteors["M-" + "%07d" % meteor_list_count]["end"] = [convert_datetime(current_time.time()),
                                                         convert_datetime(signal_time)]
    current_duration = current_time - datetime.datetime(
        *meteors["M-" + "%07d" % meteor_list_count]["date"],
        *meteors["M-" + "%07d" % meteor_list_count]["beginning"][0]
    )
    meteors["M-" + "%07d" % meteor_list_count]["duration"] = [int(current_duration.total_seconds() * Window.Fps),
                                                              convert_datetime(current_duration)]

    meteors_updated = {}
    delete_keys = []

    # Remove the sorted out meteor signals
    for key in meteors:
        indications = 0
        frames = meteors[key]["frames"]
        for frame in frames:
            if frame in sort_out_list:
                indications += 1
        if len(frames) <= max_frames and indications > 0:  # If it is a very short meteor with indications, delete it.
            delete_keys.append(key)
        elif indications > delete_threshold:
            delete_keys.append(key)
        elif indications / len(frames) >= delete_percentage:  # If more than 25% of the frames were marked, delete it.
            delete_keys.append(key)
        elif len(frames) <= min_length * Window.Fps or len(frames) > max_length * Window.Fps:
            delete_keys.append(key)

    for key in delete_keys:
        del meteors[key]

    for i, key in enumerate(meteors):
        meteors_updated["M-" + "%07d" % (i + 1)] = meteors[key]

    return meteors_updated


def convert_datetime(dobject):
    if type(dobject) == datetime.date:
        return [dobject.year, dobject.month, dobject.day]
    if type(dobject) == datetime.datetime:
        return [dobject.year, dobject.month, dobject.day, dobject.hour, dobject.minute, dobject.second,
                dobject.microsecond]
    if type(dobject) == datetime.time:
        return [dobject.hour, dobject.minute, dobject.second, dobject.microsecond]
    if type(dobject) == datetime.timedelta:
        temp_object = (datetime.datetime.fromtimestamp(dobject.total_seconds()) - timedelta(hours=1)).time()
        return [temp_object.hour, temp_object.minute, temp_object.second, temp_object.microsecond]


def write_amos_file(Window, amos_filepath, meteor_data, sort_out_list, len_mul, base_time_list, videopath_list,
                    xmlpath_list, folderpath, duration_list, fps_list, resolution_list):
    print(meteor_data)
    with open(amos_filepath, "w") as f:
        file_string = ""
        file_string += json.dumps([videopath_list, xmlpath_list, folderpath]) + "\n"
        file_string += json.dumps(base_time_list) + "\n"
        file_string += json.dumps(duration_list) + "\n"
        file_string += json.dumps(fps_list) + "\n"
        file_string += json.dumps(resolution_list) + "\n"
        file_string += json.dumps(generate_results(Window, meteor_data, sort_out_list, len_mul)) + "\n"
        f.write(file_string)


def print_table(input_data):
    for m in input_data.items():
        print(m[0])
        for k, v in m[1].items():
            print("{:<18} {:<25}".format(k, str(v)))
        print("\n")
