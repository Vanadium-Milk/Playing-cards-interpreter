'''
Scan each card one by one and store their corners in a CSV file.\n
press the R key to register a card when it is in correctly framed.\n
Author: Leah Castro.\n
No copiar, no distribuír y definitivamente refactoricen antes de subirlo
'''

import cv2 as cv
import csv
from cards import *

CAP_DEVICE = 0
SYMBOLS = ('♠','♥','♦','♣')
CHARS = ('A','2','3','4','5','6','7','8','9','10','J','Q','K')

#Make sure to use the same scan parameters when identifying cards
card_scan = scanner(200, 0.3, 0.1, 0.142)
cap = initiate_capture(CAP_DEVICE)

rows = []

#Iterate all combinations
for char in CHARS:
    for sym in SYMBOLS:
        c_name = f"{char}{sym}"
        print(f"\nReady to scan card: {c_name}")
        while True:
            frame = get_frame(cap)
            card_scan.get_frame_modes(frame)
            
            #Proceed only when a card is found
            if not card_scan.get_card_edges(frame):
                frame_corners = []
                rec_frames = 0
            else:
                frame_corners = card_scan.get_card_corners(frame)
                if cv.waitKey(1) == ord('r') and frame_corners:
                    corner_count = len(frame_corners)
                    relative_place = card_scan.get_relative_corner_place(frame_corners)
                    rows.append([[char, sym], corner_count, relative_place])
                    print(f"corners: {corner_count}")
                    break

            cv.imshow('frame', frame)
            if cv.waitKey(1) == ord('q'):
                exit()
    
#Order rows by corner amount ascendingly
corners = [row[1] for row in rows]
sortedd = corners.copy()
sortedd.sort()

last = 0
start_i = 0
with open('sorted_corners.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    for i in range (len(rows)):
        num = sortedd[i]
        if num != last:
            last = num
            start_i = 0
        else:
            start_i = row_num + 1
        row_num = corners.index(num, start_i)

        writer.writerow(rows[row_num])

print(f"All cards scan finished, stored: {len(rows)}")
# When everything done, release the capture
cap.release()
cv.destroyAllWindows()