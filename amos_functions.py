#Importing all modules
import cv2, datetime, numpy, pandas, os, statistics, imutils, shutil, sys, json
from xml.dom import minidom
from datetime import timedelta
from imutils.video import FileVideoStream
from bokeh.plotting import figure, show, output_file
from bokeh.models import HoverTool, ColumnDataSource
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QCursor, QFont
    
def check_pos(first, second, thresh):
    f_x = first[0]
    f_y = first[1]
    s_x = second[0]
    s_y = second[1]
    if f_x - s_x <= thresh and f_x - s_x >= -thresh:
        if f_y - s_y <= thresh and f_y - s_y >= -thresh:
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

    #Reading Files
    if os.path.isfile(videopath):
        video = FileVideoStream(videopath).start()
    else:
        video_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected Video does not exist.")
        video_not_found.setWindowTitle("Video not found")
        video_not_found.exec_()
        return (False, {})

    black = cv2.imread('files/black.png', 0)

    try:
        os.rename(src=f'{folderpath}/frames', dst=f'{folderpath}/remove')
    except:
        pass

    shutil.rmtree(f'{folderpath}/remove', ignore_errors=True)

    try:
        os.mkdir(f'{folderpath}/frames')
    except FileExistsError:
        pass
    
    #Defining the variable for the reference frame
    ref_frame = None

    start_meteor = [[0,0]]
    global position_names
    position_names = []
    global MeteorID_List
    MeteorID_List = []
    rotation_list = []
    Meteor_area_list = []
    
    status_list=[None,None]
    times=[]

    length = Window.length
    Fps = Window.Fps
    Height = Window.Height
    Width = Window.Width
    
    if use_xml:
        #Reading and processing the XML-file
        try:
            XML_File = minidom.parse(xmlpath)
        except FileNotFoundError:
            xml_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected XML file does not exist.")
            xml_not_found.setWindowTitle("XML not found")
            xml_not_found.exec_()
            return (False, {})
        try:
            creationDate = XML_File.getElementsByTagName('CreationDate')
            creationDate = creationDate[0].attributes['value'].value

            year, month, day, hour, minute, second = int(creationDate[:4]), int(creationDate[5:7]), int(creationDate[8:10]), int(creationDate[11:13]), int(creationDate[14:16]), int(creationDate[17:19])
        except IndexError:
            xml_not_valid = QMessageBox(icon=QMessageBox.Critical, text='The selected XML file is not valid, the key "creationDate" and its value is missing.')
            xml_not_valid.setWindowTitle("XML not valid")
            xml_not_valid.exec_()
            return (False, {})

        base_time = datetime.datetime(year, month, day, hour, minute, second)
    else:
        base_time = Window.base_time
            
    beginning_video_time = datetime.datetime(1, 1, 1, 0, 0, 0)
    
    len_mul = Height//1080
    ar_mul = len_mul**2

    #Defining the variable for the current frame
    frame_number = 1
    
    #Processing the Excel-File
    sheet = Window.sheet
    detection_count = 0

    meteor_data = {}

    Window.analysation_status_image.setMovie(Window.loading_animation)
    Window.loading_animation.start()

    Window.analysation_progressdialog = QProgressDialog("Analysing the video... \n\nEstimated remaining time: \nCalculating...", "Exit", 1, 100, Window)

    t = QTime()
    t.start()
    frames_since_reset = 1
    
    for _ in range(length):
        frames_since_reset += 1
        if frame_number % 100 == 0:
            t.restart()
            frames_since_reset = 1
        progress_percent = frame_number / length * 100
        Window.analysation_progressdialog.setValue(progress_percent)
        Window.remaining_seconds = round((length-frame_number)*((t.elapsed()/frames_since_reset)/1000))+1
        Window.remaining_time = str(datetime.timedelta(seconds=Window.remaining_seconds))
        Window.analysation_progressdialog.setLabelText(f"Analysing the video... \n\nEstimated remaining time: \n{Window.remaining_time} s")

        #Reading current frame
        frame = video.read()

        #Reset variables
        status=0

        #Preparing the Video for calculations
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray,(20*len_mul+1, 20*len_mul+1),0)

        if ref_frame is None:
            ref_frame = gray
            status_list=[0]
            continue
        if frame_number%1000 == 0:
            ref_frame = gray

        #Draw the grid
        x_grid = 8
        y_grid = 5

        width = Width//x_grid
        height = Height//y_grid
        for v in range(y_grid):
            move = v*height
            for h in range(x_grid):
                cv2.rectangle(frame, (width*h,move), (width*(h+1),move+height), (100,100,100), 1)

        #Calculating the difference between the current frame and the reference frame
        delta_frame = cv2.absdiff(ref_frame, gray)

        thresh_delta = cv2.threshold(delta_frame, 20, 255, cv2.THRESH_BINARY)[1]

        thresh_delta = cv2.dilate(thresh_delta, None, iterations=2)

        (cnts,_) = cv2.findContours(thresh_delta.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

        #Calculating the time
        current_seconds = frame_number/Fps

        time = base_time + timedelta(seconds=current_seconds)

        #Drawing boxes around areas that are meteors
        if len(cnts) > 5:
            ref_frame = gray
            print("Frame was reset because more than 5 Meteors")
            continue
        else:
            for contour in cnts:
                if cv2.contourArea(contour) < 60*ar_mul or cv2.contourArea(contour) > 4000*ar_mul:
                    continue
                status=1
                detection_count += 1
                Meteor_area_list.append(cv2.contourArea(contour))
                rect = cv2.minAreaRect(contour)
                rotation_list.append(rect[2])
                (x, y, w, h) = cv2.boundingRect(contour)
                border = 10*len_mul
                text_border = 20*len_mul
                cv2.rectangle(frame, (x-border,y-border), (x+w+border,y+h+border),(255,255,255), 2)
                cv2.putText(frame, "Meteor", (x-border,y-text_border), cv2.FONT_HERSHEY_SIMPLEX, 1*len_mul,(100,255,0),1,cv2.LINE_AA)
                average_x = x+(w//2)
                average_y = y+(h//2)
                meteor_data[f"signal_{detection_count}"] = {"position" : (average_x, average_y), "frame" : [frame_number]}


        #Return if a meteor was detected
        status_list.append(status)
        status_list=status_list[-3:]

        #Return the Start and End time of the meteor
        if status_list[-1]==1 and status_list[-2]==0: #If the meteor appeared
            Window.meteor_count+=1
            times.append(time)

            start_meteor= [average_x, average_y]

            width_box = Width//x_grid
            height_box = Height//y_grid

            X_names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "L", "M", "N", "O", "P"]

            for i in range(x_grid):
                if start_meteor[0] > (i+1)*width_box:
                    continue
                X_position_name = X_names[i]
                break

            for i in range(y_grid):
                if start_meteor[1] > (i+1)*height_box:
                    continue
                Y_position_name = str(i+1)
                break

            Position_name = X_position_name + Y_position_name

            position_names.append(Position_name)
            position_names.append(Position_name)

            current_meteor_start = base_time + timedelta(seconds = current_seconds)

            row_number = Window.meteor_count+1
            cell = sheet.cell(row_number,1)
            MeteorID = "M-"+"%07d" % Window.meteor_count
            MeteorID_List.append(MeteorID)
            MeteorID_List.append(MeteorID)
            MeteorID_List.append(MeteorID)
            cell.value = MeteorID

            cell = sheet.cell(row_number,2)
            cell.value = str(base_time)[-8:]

            cell = sheet.cell(row_number,3)
            cell.value = VideoID

            cell = sheet.cell(row_number,4)
            cell.value = str(beginning_video_time + timedelta(seconds = current_seconds))[11:]

            cell = sheet.cell(row_number,6)
            cell.value = str(current_meteor_start)[11:]

            cell = sheet.cell(row_number,11)
            cell.value = Position_name

            cell = sheet.cell(row_number,12)
            cell.value = str(current_meteor_start)[:10]



        if status_list[-1]==0 and status_list[-2]==1: #If the meteor disappeared
            current_meteor_end = base_time + timedelta(seconds = current_seconds)
            meteor_length = current_meteor_end - current_meteor_start

            if meteor_length > timedelta(seconds=5) or meteor_length < timedelta(seconds=0.08):
                Window.meteor_count += -1
                times.pop() #Remove the beginning from the list
                position_names.pop()
                position_names.pop()
                sheet.delete_rows(row_number)
            else:
                times.append(time)

                cell = sheet.cell(row_number,5)
                cell.value = str(beginning_video_time + timedelta(seconds = current_seconds))[11:]

                cell = sheet.cell(row_number,7)
                cell.value = str(current_meteor_end)[11:]

                cell = sheet.cell(row_number,8)
                cell.value = str(current_meteor_end - current_meteor_start)

                cell = sheet.cell(row_number,9)
                Meteor_area_list = sorted(Meteor_area_list)
                Meteor_area = Meteor_area_list[-1]
                Meteor_area = round(Meteor_area)
                cell.value = Meteor_area

                cell = sheet.cell(row_number,10)
                rot_average = statistics.mean(rotation_list)
                cell.value = str(round(rot_average))+"°"

                rotation_list = []
                Meteor_area_list = []

        #Resize the main window to match the screen size
        frameResized = cv2.resize(frame, (1280, 720))

        #Writing the text for the time, date and frame number
        cv2.putText(frameResized, str(time)[:-5], (20, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5,(200,200,200),1,cv2.LINE_AA)
        cv2.putText(frameResized, str(frame_number), (1220, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5,(200,200,200),1,cv2.LINE_AA)

        #Drawing and writing the text for the grid
        cv2.putText(frameResized, 'A', (70, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, 'B', (70+160, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, 'C', (70+320, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, 'D', (70+480, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, 'E', (70+640, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, 'F', (70+800, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, 'G', (70+960, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, 'H', (70+1120, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, '1', (15, 80), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, '2', (15, 80+144), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, '3', (15, 80+288), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, '4', (15, 80+432), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(frameResized, '5', (15, 80+576), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)

        if status == 1:
            frame_to_write = cv2.resize(frameResized, (960, 540))
            frame_to_write = cv2.cvtColor(frame_to_write, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(f"{folderpath}/frames/{frame_number}_frame.png", frame_to_write)
        
        cv2.putText(frameResized, 'Press "esc" to exit and "R" to set a new reference frame', (400, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5,(200,200,200),1,cv2.LINE_AA)

        #Resize windows for stack
        gray_resized = cv2.resize(gray, (864, 486))
        thresh_resized = cv2.resize(thresh_delta, (864, 486))
        delta_resized = cv2.resize(delta_frame, (864, 486))
        black_resized = cv2.resize(black, (864, 486))

        #Stack the Windows that provide extra detail
        stack1 = numpy.hstack([gray_resized, thresh_resized])
        stack2 = numpy.hstack([delta_resized, black_resized])
        stack = numpy.vstack([stack1, stack2])
        cv2.rectangle(stack, (0,0), (864,486),(255,255,255), 1)
        cv2.rectangle(stack, (0,486), (864,971),(255,255,255), 1)
        cv2.rectangle(stack, (864,0), (1727,486),(255,255,255), 1)
        cv2.putText(stack, 'Difference', (350, 520), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(stack, 'Capturing', (350, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)
        cv2.putText(stack, 'Threshold', (1250, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8,(255,255,255),1,cv2.LINE_AA)

        #Opening windows for visualization
        cv2.imshow('AMOS - Analysation',frameResized)
        #cv2.imshow('Additional details - AMOS', stack)

        key = cv2.waitKey(1)

        if key == 27 or Window.analysation_progressdialog.wasCanceled():
            if status == 1:
                times.append(time)

                current_meteor_end = base_time + timedelta(seconds = current_seconds)

                cell = sheet.cell(row_number,5)
                cell.value = str(beginning_video_time + timedelta(seconds = current_seconds))[11:]

                cell = sheet.cell(row_number,7)
                cell.value = str(current_meteor_end)[11:]

                cell = sheet.cell(row_number,8)
                cell.value = str(current_meteor_end - current_meteor_start)
            break

        if key == ord('r'):
            ref_frame = gray
            print("Frame reset because of key pressed.")

        frame_number+=1

    Window.analysation_progressdialog.setValue(100)

    video.stop()
    
    #Close all Windows
    cv2.destroyWindow('AMOS - Analysation')
    cv2.destroyWindow('Additional details - AMOS')

    meteors = generate_results(meteor_data, len_mul, ar_mul)

    return (True, meteor_data)
    
def generate_diagram():
    #Preparing the Pandas Dataframe
    df=pandas.DataFrame(columns=["Start","End"])

    #Calculating values and plotting the Chart
    for i in range(0,len(times),2):
        print('iteration')
        df=df.append({"Start":times[i],"End":times[i+1],"Position":position_names[i],"MeteorID":MeteorID_List[i]},ignore_index=True)

    df.to_csv(f'{folderpath}/Results.csv')

    #try:
    df["Start_string"]=df["Start"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    df["End_string"]=df["End"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")

    cds=ColumnDataSource(df)

    p=figure(x_axis_type='datetime',height=100, width=500, title='Meteore', toolbar_location="below")
    p.axis.visible = False
    p.yaxis.minor_tick_line_color=None
    p.ygrid[0].ticker.desired_num_ticks=1

    hover=HoverTool(tooltips=[("Meteor-ID", "@MeteorID"),("Position", "@Position"),
                              ("Start", "@Start_string"),("End", "@End_string")])
    p.add_tools(hover)

    q=p.quad(left="Start", right="End", bottom=0, top=1, color="black", source=cds)

    output_file("Meteordiagramm.html")
    show(p)
    #except AttributeError:
        #print("No meteors found yet!")

def save_spreadsheet(Window):
    Window.wb.save(f'{Window.folderpath}/Results.xlsx')
    
def apply_defaults(Window):
    with open("files/defaults.txt", "r") as defaults_file:
        defaults = json.loads(defaults_file.read())
    
    if defaults[0] == [] or defaults[1] == [] or defaults[2] == "None":
        set_defaults_now = QMessageBox.question(Window, "No defaults yet!", "You have not set any defaults yet. Do you want to set them now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if set_defaults_now == QMessageBox.Yes:
            set_defaults(Window)
    else:
        Window.videopath_list, Window.xmlpath_list, Window.folderpath = defaults
        Window.setup_video_selection(Window.videopath_list)
        Window.setup_xml_selection(Window.xmlpath_list)
        Window.setup_folder_selection(Window.folderpath)

def set_defaults(Window):
    select_video_info = QMessageBox(icon=QMessageBox.Information, text="In the following dialog, select your default video(s).")
    select_video_info.setWindowTitle("Info")
    select_video_info.exec_()

    Window.default_videopath_list = QFileDialog.getOpenFileNames(parent=Window, filter="MP4 Files (*.mp4)")
    Window.default_videopath_list = Window.default_videopath_list[0]
    if Window.default_videopath_list != []: #If the user didn't cancel the selection
        select_xml_info = QMessageBox(icon=QMessageBox.Information, text="In the following dialog, select your default XML(s).")
        select_xml_info.setWindowTitle("Info")
        select_xml_info.exec_()

        Window.default_xmlpath_list = QFileDialog.getOpenFileNames(parent=Window, filter="XML Files (*.xml)")
        Window.default_xmlpath_list = Window.default_xmlpath_list[0]
        if Window.default_xmlpath_list != []: #If the user didn't cancel the selection
            select_folder_info = QMessageBox(icon=QMessageBox.Information, text="In the following dialog, select your default folder to store results in.")
            select_folder_info.setWindowTitle("Info")
            select_folder_info.exec_()

            Window.default_folderpath = QFileDialog.getExistingDirectory(parent=Window)
            if Window.default_folderpath != "": #If the user didn't cancel the selection
                default_paths = [Window.default_videopath_list, Window.default_xmlpath_list, Window.default_folderpath]
                with open("files/defaults.txt", "w") as defaults_file:
                    defaults_file.write(json.dumps(default_paths))

                set_defaults_success_message = QMessageBox(icon=QMessageBox.Information, text="Defaults set succesfully!")
                set_defaults_success_message.setWindowTitle("Info")
                set_defaults_success_message.exec_()

def delete_defaults(Window):
    delete_continue = QMessageBox.question(Window, "Do you want to delete?", "Are you sure that you want to delete the defaults?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

    if delete_continue == QMessageBox.Yes:
        none_content = [[], [], "None"]
        with open("files/defaults.txt", "w") as defaults_file:
            defaults_file.write(json.dumps(none_content))

        set_defaults_success_message = QMessageBox(icon=QMessageBox.Information, text="Defaults deleted succesfully!")
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
    vid = FileVideoStream(path).start()
    thumbnail = vid.read()
    vid.stop()
    thumbnail = cv2.resize(thumbnail, (240, 135))
    return thumbnail

def generate_results(meteor_data, len_mul, ar_mul):
    if meteor_data == {}:
        return {}
    meteors = {}
    x_positions_list = []
    y_positions_list = []
    meteor_list_count = 1
    for key in meteor_data.keys():
        if key == "signal_1":
            current_position = meteor_data[key]['position']
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            meteors["M-"+"%07d" % meteor_list_count] = {"position" : current_position, "frames" : meteor_data[key]['frame']}
            continue
        previous_position = current_position
        current_position = meteor_data[key]['position']
        if check_pos(current_position, previous_position, 200*len_mul):
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            meteors["M-"+"%07d" % meteor_list_count]["frames"].append(meteor_data[key]['frame'][0])
        else:
            meteors["M-"+"%07d" % meteor_list_count]["position"] = (int(statistics.mean(x_positions_list)),int(statistics.mean(y_positions_list)))
            meteors["M-"+"%07d" % meteor_list_count]["frames"] = sorted(set(meteors["M-"+"%07d" % meteor_list_count]["frames"]))
            x_positions_list.clear()
            y_positions_list.clear()
            meteor_list_count += 1
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            meteors["M-"+"%07d" % meteor_list_count] = {"position" : current_position, "frames" : meteor_data[key]['frame']}
    meteors["M-"+"%07d" % meteor_list_count]["position"] = (int(statistics.mean(x_positions_list)),int(statistics.mean(y_positions_list)))
    meteors["M-"+"%07d" % meteor_list_count]["frames"] = sorted(set(meteors["M-"+"%07d" % meteor_list_count]["frames"]))
    return meteors

def write_ama_file(ama_filepath, meteor_data, len_mul, ar_mul, base_time_list, videopath_list, xmlpath_list, folderpath, duration_list, fps_list, resolution_list):
    with open(ama_filepath, "w") as f:
        file_string = ""
        file_string += json.dumps([videopath_list, xmlpath_list, folderpath]) + "\n"
        file_string += json.dumps(base_time_list) + "\n"
        file_string += json.dumps(duration_list) + "\n"
        file_string += json.dumps(fps_list) + "\n"
        file_string += json.dumps(resolution_list) + "\n"
        file_string += json.dumps(generate_results(meteor_data, len_mul, ar_mul)) + "\n"
        f.write(file_string)


#temp_meteor_data = {'signal_1': {'position': (1410, 931), 'frame': [52]}, 'signal_2': {'position': (1425, 939), 'frame': [53]}, 'signal_3': {'position': (1440, 947), 'frame': [54]}, 'signal_4': {'position': (1456, 955), 'frame': [55]}, 'signal_5': {'position': (1473, 963), 'frame': [56]}, 'signal_6': {'position': (1490, 972), 'frame': [57]}, 'signal_7': {'position': (1507, 980), 'frame': [58]}, 'signal_8': {'position': (1525, 989), 'frame': [59]}, 'signal_9': {'position': (1461, 957), 'frame': [59]}, 'signal_10': {'position': (1474, 964), 'frame': [60]}, 'signal_11': {'position': (1475, 965), 'frame': [61]}, 'signal_12': {'position': (1475, 964), 'frame': [62]}, 'signal_13': {'position': (1474, 964), 'frame': [63]}, 'signal_14': {'position': (1473, 964), 'frame': [64]}, 'signal_15': {'position': (1471, 962), 'frame': [65]}, 'signal_16': {'position': (1482, 968), 'frame': [66]}, 'signal_17': {'position': (1455, 954), 'frame': [66]}, 'signal_18': {'position': (1484, 969), 'frame': [67]}, 'signal_19': {'position': (1457, 955), 'frame': [67]}, 'signal_20': {'position': (1484, 968), 'frame': [68]}, 'signal_21': {'position': (904, 480), 'frame': [245]}, 'signal_22': {'position': (909, 481), 'frame': [246]}, 'signal_23': {'position': (915, 482), 'frame': [247]}, 'signal_24': {'position': (921, 483), 'frame': [248]}, 'signal_25': {'position': (928, 484), 'frame': [249]}, 'signal_26': {'position': (934, 485), 'frame': [250]}, 'signal_27': {'position': (941, 486), 'frame': [251]}, 'signal_28': {'position': (948, 487), 'frame': [252]}, 'signal_29': {'position': (955, 488), 'frame': [253]}, 'signal_30': {'position': (962, 489), 'frame': [254]}, 'signal_31': {'position': (967, 491), 'frame': [255]}, 'signal_32': {'position': (964, 492), 'frame': [256]}, 'signal_33': {'position': (967, 493), 'frame': [257]}, 'signal_34': {'position': (972, 495), 'frame': [258]}, 'signal_35': {'position': (982, 496), 'frame': [259]}, 'signal_36': {'position': (988, 497), 'frame': [260]}, 'signal_37': {'position': (1012, 500), 'frame': [266]}, 'signal_38': {'position': (1009, 498), 'frame': [267]}, 'signal_39': {'position': (1008, 497), 'frame': [268]}, 'signal_40': {'position': (1008, 497), 'frame': [269]}, 'signal_41': {'position': (1009, 496), 'frame': [270]}, 'signal_42': {'position': (1008, 496), 'frame': [271]}, 'signal_43': {'position': (1009, 496), 'frame': [272]}, 'signal_44': {'position': (1008, 496), 'frame': [273]}, 'signal_45': {'position': (1007, 496), 'frame': [274]}, 'signal_46': {'position': (1006, 495), 'frame': [275]}, 'signal_47': {'position': (1006, 495), 'frame': [276]}, 'signal_48': {'position': (1006, 495), 'frame': [277]}, 'signal_49': {'position': (1006, 496), 'frame': [278]}, 'signal_50': {'position': (1005, 496), 'frame': [279]}, 'signal_51': {'position': (1004, 495), 'frame': [280]}, 'signal_52': {'position': (1004, 495), 'frame': [281]}, 'signal_53': {'position': (1003, 495), 'frame': [282]}, 'signal_54': {'position': (1003, 495), 'frame': [283]}, 'signal_55': {'position': (1006, 496), 'frame': [284]}, 'signal_56': {'position': (1005, 495), 'frame': [285]}, 'signal_57': {'position': (1002, 495), 'frame': [286]}, 'signal_58': {'position': (1003, 495), 'frame': [287]}, 'signal_59': {'position': (1002, 495), 'frame': [288]}, 'signal_60': {'position': (1002, 495), 'frame': [289]}, 'signal_61': {'position': (1000, 496), 'frame': [290]}, 'signal_62': {'position': (1001, 496), 'frame': [291]}, 'signal_63': {'position': (1000, 496), 'frame': [292]}, 'signal_64': {'position': (1061, 506), 'frame': [293]}, 'signal_65': {'position': (999, 496), 'frame': [293]}, 'signal_66': {'position': (999, 496), 'frame': [294]}, 'signal_67': {'position': (1001, 496), 'frame': [295]}, 'signal_68': {'position': (1000, 496), 'frame': [296]}, 'signal_69': {'position': (1000, 496), 'frame': [297]}, 'signal_70': {'position': (995, 495), 'frame': [298]}, 'signal_71': {'position': (994, 495), 'frame': [299]}, 'signal_72': {'position': (994, 495), 'frame': [300]}, 'signal_73': {'position': (995, 495), 'frame': [301]}, 'signal_74': {'position': (995, 495), 'frame': [302]}, 'signal_75': {'position': (995, 495), 'frame': [303]}, 'signal_76': {'position': (995, 495), 'frame': [304]}, 'signal_77': {'position': (994, 495), 'frame': [305]}, 'signal_78': {'position': (995, 495), 'frame': [306]}, 'signal_79': {'position': (996, 495), 'frame': [307]}, 'signal_80': {'position': (995, 494), 'frame': [308]}, 'signal_81': {'position': (994, 494), 'frame': [309]}, 'signal_82': {'position': (995, 495), 'frame': [310]}, 'signal_83': {'position': (994, 495), 'frame': [311]}, 'signal_84': {'position': (994, 495), 'frame': [312]}, 'signal_85': {'position': (994, 495), 'frame': [313]}, 'signal_86': {'position': (994, 494), 'frame': [314]}, 'signal_87': {'position': (995, 494), 'frame': [315]}, 'signal_88': {'position': (995, 495), 'frame': [316]}, 'signal_89': {'position': (994, 494), 'frame': [317]}, 'signal_90': {'position': (995, 495), 'frame': [318]}, 'signal_91': {'position': (995, 495), 'frame': [319]}, 'signal_92': {'position': (995, 494), 'frame': [320]}, 'signal_93': {'position': (994, 494), 'frame': [321]}, 'signal_94': {'position': (994, 494), 'frame': [322]}, 'signal_95': {'position': (992, 494), 'frame': [323]}}

#write_ama_file("D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/test_results.ama", temp_meteor_data, 1, 1, [[2020, 6, 8, 15, 10, 30],[2020, 6, 9, 10, 12, 10]], ["D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/V-0001.mp4", "D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/V-0002.mp4"], ["D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/V-0001.XML", "D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/V-0002.XML"], "D:/Jugend forscht/Jugend forscht 2021/AMOS/Tests/Results", [1000, 2000], [25, 50], [[3840, 2160], [1920, 1080]])