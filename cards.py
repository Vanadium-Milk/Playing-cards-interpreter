'''
Cards
=====
Uses image processing to tell apart card shaped object.\n
The library uses OpenCV to find a list of keypoints (corners) of an object and can compare it
to a collection of such data to find matches.\n
This module works best when analizing images in a dark or preferably black background.\n
Author: Leah Castro.\n
No copiar, no distribuír y definitivamente refactoricen antes de subirlo
'''

import numpy as np
import cv2 as cv
from csv import reader
from ast import literal_eval

#import luma.core.render as luma    For use with ssd1306 on raspberry

class scanner:
    '''
    Class for the image processing object responsible for finding keypoints.
    Important: Do not confuse corners with edges, corners are the sharp angles in the card imprint,
    for a given drawing or imprint corners are "key features". 
    
    Attributes:
    max_corn (int): The maximum amount of corners to search in a card image.
    quality_lvl (float): Filters corners depending on their sharpness.
    min_dist (float): The minimum (euclidean) distance corners shall have from each other.
    scan_range (float): The horizontal portion of the card to be ignored (proportional to its size).

    Methods:
    get_frame_modes(source image): Run this function at the beginning. Transforms the input image for processing.
    get_card_edges(draw_in): Finds the location of the card edges. Necessary for corner finding.
    get_card_corners(draw_in): Returns a list of corners and their position for the current card.
    get_relative_corner_place(corner_list): For a list of corners returns the position of each one based on the upper left corner.
    '''

    max_corn: int
    quality_lvl: float 
    min_dist: float
    scan_range: float

    gray: cv.typing.MatLike
    edged: cv.typing.MatLike

    card_edges: list[int]

    def __init__(self, max_corners: int, quality_level: float, min_distance: float, scan_margin: float):
        
        self.max_corn = max_corners
        self.quality_lvl = quality_level
        self.min_dist = min_distance
        self.scan_range = scan_margin

    def get_frame_modes(self, source_image) -> None:
        #Altered image modes to make scanning easier
        self.gray = cv.cvtColor(source_image, cv.COLOR_BGR2GRAY) 
        self.edged = cv.Canny(self.gray, 30, 200)

    def get_card_edges(self, draw_in = None) -> cv.typing.MatLike:
        contours, hierarchy = cv.findContours(self.edged,  
        cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        if not contours:
            return False
        
        else:
            lenghts = [len(i) for i in contours]
            card_contour = lenghts.index(max(lenghts))

            unid_cont = contours[card_contour].ravel()
            x_arr = unid_cont[::2]
            y_arr = unid_cont[1::2]

            min_x = min(x_arr)
            max_x = max(x_arr)
            min_y = min(y_arr)
            max_y = max(y_arr)

            #x1, y1, x2, y2
            self.card_edges = [min_x, min_y, max_x, max_y]

            if not draw_in is None:
                if type(draw_in) is np.ndarray:
                    cv.drawContours(draw_in, contours,card_contour, (0, 255, 0), 2)
                    cv.rectangle(draw_in, (self.card_edges[0], self.card_edges[1]),
                                (self.card_edges[2], self.card_edges[3]), (0,0,255))
                
                
                #elif type(draw_in) is luma.ImageDraw.ImageDraw:
                 #   ratio_x = 128 / len(self.edged)
                  #  ratio_y = 64 / len(self.edged[0])
                   # screen_dots = [(x_arr[i] * ratio_x, y_arr[i] * ratio_y) for i in range(len(contours[card_contour]))]

                    #draw_in.point(screen_dots, fill="white")

            return True

    def get_card_corners(self, draw_in: cv.typing.MatLike = None) -> list:
        try:
            cor = cv.goodFeaturesToTrack(self.gray, self.max_corn, self.quality_lvl, self.min_dist)
            cor = np.intp(cor)
        
        except Exception as error:
            print("Error, in corner detection, retrying...")
            print(error.args)
            return None

        else:
            good = []
            deadzone = (self.card_edges[2] - self.card_edges[0]) * self.scan_range
            self.card_edges[0] += deadzone
            self.card_edges[2] -= deadzone
            for i in cor:
                x,y = i.ravel()
                if self.__is_inbounds(x, y):
                    good.append(i)
                    
                    if not draw_in is None:
                        cv.circle(draw_in,(x,y),2,(255,255,255),-1)
            
            return good
    
    def get_relative_corner_place(self, corner_list):
        frame_w = self.card_edges[2] - self.card_edges[0]
        frame_h = self.card_edges[3] - self.card_edges[1]
        corners = [arr.ravel() for arr in corner_list]
        relative_place = [[format((cor[0] - self.card_edges[0]) / frame_w,".2f"),
                           format((cor[1] - self.card_edges[1]) / frame_h,".2f")] for cor in corners]

        return relative_place

    #Check if a point is inside a rectange
    def __is_inbounds(self, x: int, y:int) -> bool:
        if x > self.card_edges[0] and x < self.card_edges[2]:
            if y > self.card_edges[1] and y < self.card_edges[3]:
                return True
        
        return False

class card_interpreter:
    '''
    Class for identifying cards from corner lists.

    Attributes:
    _cards_list (list): Stored information of the previously scanned cards.
    __scanr (scanner): scanner object to find edges of the card.

    Methods:
    identify_card(corners_list, corner_amount): Use a list of corners to perform a comparison with stored data.
    corner amount overrides the length of the corner list, to make the card finding more precise.

    '''
    _cards_list: list
    __scanr: scanner

    def __init__(self, csv_file: str, card_scanner: scanner):
        with open(csv_file, 'r') as file:
            self.cards_list = list(reader(file))

        #convert to needed dataTypes
        for row in self.cards_list:
            row[0] = literal_eval(row[0])
            row[1] = int(row[1])
            row[2] = literal_eval(row[2])
            row[2] = [[float(num[0]), float(num[1])] for num in row[2]]

        self.__scanr = card_scanner

    #Use corners from csv and capture device to determine the actual card
    def identify_card(self, corners_list: list, corner_amount: int = None):
        if not corner_amount:
            corner_amount = len(corners_list)
        range = 3
        if corner_amount > 80:
            range = 6
        check_list = self.__find_matches(corner_amount,range, self.cards_list)
        dist = []
        for ind in check_list:
            card_corners = self.cards_list[ind][2]
            #print(f"testing card {cards[ind][0]}")
            dist.append(self.__match_corners(corners_list, card_corners, self.__scanr.card_edges))
        
        fittest = check_list[dist.index(min(dist))]
        return self.cards_list[fittest][0]

    #Find cards in csv with close corner amount
    def __find_matches(self, num, val_range, cards):
        #Remove indexes of cards that doesn't exist
        def remove_outlimits(num, max_ind):
            return (num >= 0 and num < max_ind)
        
        total_cards = len(cards)
        for i in range(total_cards):
            if num <= cards[i][1]:
                indexes = [i]
                for j in range(1, val_range):
                    indexes.append(i + j)
                    indexes.append(i - j)

                return list(filter(lambda x: remove_outlimits(x, total_cards), indexes))
        return total_cards -1

    #Match corners in captured card with sourced card
    def __match_corners(self, cap_corners, source_corners, limits):
        
        point_dist = []
        for i in source_corners:
            x,y = limits[0] + (i[0] * (limits[2] - limits[0])), limits[1] + (i[1] * (limits[3] - limits[1]))
            point_dist.append(self.__radio_search(x,y, cap_corners))
        return sum(point_dist) / len(point_dist)

    #Find the needed radius for a specific point to find any point in an array
    def __radio_search(self, x,y, arr):
        goal = np.array((x,y))
        arr = np.array(arr)
        distances = [np.linalg.norm(goal - p) for p in arr]

        return min(distances)

#Initialize capture device
def initiate_capture(device: int) -> cv.VideoCapture:
    '''
    Shortcut to initiate recording

    Parameters:
    device (int): camera device as numbered in your OS.
    '''
    cap_d = cv.VideoCapture(device)
    if cap_d.isOpened():
        return cap_d
    else:
        raise RuntimeError(f"Couldn't initiate recording device {device}")

#Get a single frame from the capture source
def get_frame(video_cap: cv.VideoCapture) -> cv.typing.MatLike:
    '''
    Shortcut to get frame by frame from the recording.

    Parameters(video_cap): VideoCapture object that shall be previously initialized
    '''
    # Capture frame-by-frame
    ret, frame = video_cap.read()

    # if frame is read correctly ret is True
    if not ret:
        raise RuntimeError("Can't receive frame (stream end?). Exiting ...")
    else:
        return frame