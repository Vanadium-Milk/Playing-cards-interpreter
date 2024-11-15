# Playing-cards-interpreter
Uses computer vision to differentiate playing cards with low resource consumption.

This is a school project nothing fancy, however, if you want to improve it you're more than welcome to do so.
You can also use it to implement computer vision in trading card games or maybe role playing tabletop games.

# Dependencies
-OpenCV `pip install opencv-python`
-Matplotlib `pip install matplotlib`
-Numpy 1.26.4 `pip install "numpy<2.0"`

# Usage
1. Connect a webcam with a good image resoultion and 
2. scan your cards using the scan_cards.py script, this will generate a csv file to identify the cards.
3. Use the card scanner class to process the image, then the card_interpreter class to compare it with your csv and determine the card. you can use detect_from_scanned.py as an example

To use the raspy_play_21.py script just make sure you have an SSD1306 Oled screen with the luma oled library `pip install luma.oled` and a few buttons.
