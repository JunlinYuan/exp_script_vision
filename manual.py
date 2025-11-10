import cv2
import matplotlib.pyplot as plt

# Get reference first
GET_REF_SCALE = True # make it true to collect ref data, then make false
CM_TO_PIXEL = {
    6: 62,
    7:61.4,
    8: 61,
    10:63,
    12: 59.6
}


CM = int(input("input CM value: "))


# Fill these all up
CM_TO_FREQ = {
    (1,8): 2.19,(1,10) : 2.2,(1,12) : 2.2,(1,14) : 2.22,(1,16) : 2.22,(1,18) : 2.22,(1,20) : 2.22,(1,22) : 2.28,(1,24) : 2.28,(1,26) : 2.28,
    (2,8): 2.28,(2,10) : 2.28,(2,12) : 2.28,(2,14) : 2.27,(2,16) : 2.27,(2,18) : 2.27,(2,20) : 2.27,(2,22) : 2.27,(2,24) : 2.27,(2,26) : 2.27,
    (3,8): 2.27,(3,10) : 2.27,(3,12) : 2.27,(3,14) : 2.27,(3,16) : 2.27,(3,18) : 2.27,(3,20) : 2.27,(3,22) : 2.28,(3,24) : 2.28,(3,26) : 2.28,
    (4,8): 2.28,(4,10) : 2.29,(4,12) : 2.29,(4,14) : 2.29,(4,16) : 2.29,(4,18) : 2.29,(4,20) : 2.29,(4,22) : 2.29,(4,24) : 2.29,(4,26) : 2.29,
    (5,8): 2.29,(5,10) : 2.29,(5,12) : 2.29,(5,14) : 2.29,(5,16) : 2.29,(5,18) : 2.29,(5,20) : 2.29,(5,22) : 2.29,(5,24) : 2.29,(5,26) : 2.29,
    (6,8): 2.3,(6,10) : 2.3,(6,12) : 2.31,(6,14) : 2.31,(6,16) : 2.31,(6,18) : 2.31,(6,20) : 2.31,(6,22) : 2.31,(6,24) : 2.31,(6,26) : 2.31,
    (7,8): 2.31,(7,10) : 2.31,(7,12) : 2.31,(7,14) : 2.31,(7,16) : 2.31,(7,18) : 2.31,(7,20) : 2.31,(7,22) : 2.31,(7,24) : 2.31,(7,26) : 2.31,
    (8,8): 2.31,(8,10) : 2.31,(8,12) : 2.31,(8,14) : 2.31,(8,16) : 2.31,(8,18) : 2.31,(8,20) : 2.31,(8,22) : 2.31,(8,24) : 2.31,(8,26) : 2.31,
    (9,8): 2.31,(9,10) : 2.31,(9,12) : 2.31,(9,14) : 2.31,(9,16) : 2.31,(9,18) : 2.31,(9,20) : 2.31,(9,22) : 2.31,(9,24) : 2.31,(9,26) : 2.31,
    (10,8): 2.31,(10,10) : 2.31,(10,12) : 2.31,(10,14) : 2.31,(10,16) : 2.32,(10,18) : 2.32,(10,20) : 2.32,(10,22) : 2.32,(10,24) : 2.32,(10,26) : 2.32,
    (11,8): 2.31,(11,10) : 2.31,(11,12) : 2.31,(11,14) : 2.31,(11,16) : 2.31,(11,18) : 2.31,(11,20) : 2.28,(11,22) : 2.28,(11,24) : 2.28,(11,26) : 2.28,
    (12,8): 2.28,(12,10) : 2.28,(12,12) : 2.28,(12,14) : 2.28,(12,16) : 2.28,(12,18) : 2.28,(12,20) : 2.28,(12,22) : 2.28,(12,24) : 2.28,(12,26) : 2.28,
}

def read_video_frames(video_path):
    frames = []
    cap = cv2.VideoCapture(video_path)
    print(f"Reading video from: {video_path}")
    total_frames_meta = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total number of video frames (metadata): {total_frames_meta}")
    selected_frame_index = int(input("Choose the fram number: "))
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    print(f"Total frames extracted: {len(frames)}")

    selected_frame = frames[selected_frame_index]
    print(f"Shape of selected frame: {selected_frame.shape}")

    frame_with_lines = selected_frame.copy()
    height, width = frame_with_lines.shape[:2]
    total_width_cm = 45.0
    cm_positions = [18, 35]

    pixels_per_cm = width / total_width_cm
    for cm_position in cm_positions:
        x_px = int(round(cm_position * pixels_per_cm))
        x_px = max(0, min(width - 1, x_px))
        cv2.line(frame_with_lines, (x_px, 0), (x_px, height - 1), (0, 0, 255), 2)

    plt.imshow(cv2.cvtColor(frame_with_lines, cv2.COLOR_BGR2RGB))
    plt.show()


if GET_REF_SCALE:
    ref_path = fr"C:\Users\arnab\OneDrive\Desktop\bubble image processing\{CM}cm\{CM}cm.mp4"
    read_video_frames(ref_path) 
    dpixels = int(input("scale size in pixels: "))
    physicalscale = int(input("scale size in physical scale: "))
    dx = dpixels / physicalscale
    print( "pixel to physicalscale conversion factor=",dx)

else:
    HZ = int(input("input Hz value: "))
    video_path = fr"C:\Users\arnab\OneDrive\Desktop\bubble image processing\{CM}cm\{CM}cm{HZ}hz.mp4"
    read_video_frames(video_path) 
    dpixels = int(input("Wavelength in pixels: "))
    dx = dpixels / CM_TO_PIXEL[CM]
    freq = CM_TO_FREQ[(CM, HZ)]

    print("velocity = ", dx * freq, "cm/s")

