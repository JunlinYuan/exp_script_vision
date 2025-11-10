# Automatic Timeline Detection - Technical Options

## Problem Statement

**Current State:** Semi-automatic calibration requires human to click on two ruler markings.

**Desired State:** Automatically detect and read timeline/ruler markings in video frames without human intervention.

**Use Cases:**
1. Frame-by-frame tracking: Track which cm marking is at a specific location in each frame
2. Cross-frame analysis: Measure displacement by detecting the same markings across different frames
3. Batch processing: Process multiple videos automatically

---

## Approach 1: Classical Computer Vision (Recommended Starting Point)

### Method: Hough Transform + Edge Detection + OCR

**How it works:**
1. **Edge Detection**: Use Canny edge detection to find ruler edges and tick marks
2. **Line Detection**: Apply Hough Line Transform to detect the ruler's main line
3. **Tick Mark Extraction**: Find perpendicular lines (tick marks) along the ruler
4. **Spacing Analysis**: Measure distances between tick marks to identify major marks (cm) vs minor marks (mm)
5. **OCR for Numbers**: Use OCR (Tesseract, EasyOCR) to read the numbers near major tick marks

**Advantages:**
- No training data needed
- Fast processing (real-time capable)
- Explainable and debuggable
- Works well with clear, high-contrast rulers

**Disadvantages:**
- Sensitive to lighting and blur
- Requires well-defined ruler edges
- May struggle with perspective distortion
- OCR can fail on small/unclear numbers

**Implementation Complexity:** Medium
**Best For:** Clean experimental setups with good lighting and fixed camera angles

**Key Libraries:**
- OpenCV (cv2.HoughLinesP, cv2.Canny)
- Tesseract OCR or EasyOCR
- scikit-image (skimage.transform.hough_line)

**Reference Implementation Pattern:**
```python
# High-level pseudocode
1. Preprocess: Mean shift filtering + adaptive thresholding
2. Edge detection: Canny edge detector
3. Line detection: Hough transform to find ruler main line
4. Tick detection: Find perpendicular short lines (tick marks)
5. Measure tick spacing: Group ticks by spacing (major = cm, minor = mm)
6. Number extraction: Crop regions near major ticks → OCR
7. Build mapping: pixel location → cm value
```

---

## Approach 2: ArUco Markers (Practical Alternative)

### Method: Replace ruler with computer-readable markers

**How it works:**
1. Place **ArUco markers** at known cm positions (e.g., at 5cm, 10cm, 15cm)
2. Use OpenCV's ArUco detection (cv2.aruco.detectMarkers)
3. Automatically identify each marker's ID and pixel location
4. No OCR needed - markers have built-in IDs

**Advantages:**
- Extremely reliable detection
- No OCR required
- Works in poor lighting
- Handles perspective distortion well
- OpenCV has built-in robust detection

**Disadvantages:**
- Requires modifying the experimental setup
- Need to print and place ArUco markers
- Takes up visual space in the frame
- Can't be used retroactively on existing videos

**Implementation Complexity:** Low
**Best For:** New experimental setups where you can control the environment

**Key Libraries:**
- OpenCV ArUco module (cv2.aruco)

**Reference Implementation Pattern:**
```python
# High-level pseudocode
import cv2
import cv2.aruco as aruco

# Define ArUco dictionary
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
parameters = aruco.DetectorParameters()

# Detect markers in frame
corners, ids, rejected = aruco.detectMarkers(frame, aruco_dict, parameters=parameters)

# Map detected IDs to cm values
# ID 0 = 5cm, ID 1 = 10cm, ID 2 = 15cm, etc.
```

---

## Approach 3: Deep Learning Object Detection

### Method: YOLO or Mask R-CNN to detect ruler and markings

**How it works:**
1. **Train object detector** (YOLOv8, YOLOv11, or Mask R-CNN) on labeled ruler images
2. Detect ruler region in each frame
3. Detect individual tick marks and number regions
4. Use OCR or classification network to read numbers
5. Build spatial mapping from detections

**Advantages:**
- Robust to lighting, blur, perspective
- Can handle complex backgrounds
- Works with partial ruler visibility
- State-of-the-art accuracy (98%+ for pointer meters in research)

**Disadvantages:**
- Requires large labeled dataset (hundreds of images)
- Training takes time and computational resources
- Model size may be large for real-time processing
- Overkill for simple, clean experimental setups

**Implementation Complexity:** High
**Best For:** Industrial applications, complex environments, high-volume processing

**Key Libraries:**
- Ultralytics YOLOv8/YOLOv11
- Detectron2 (Mask R-CNN)
- PyTorch or TensorFlow
- EasyOCR or PaddleOCR for number reading

**Training Requirements:**
- 500-1000+ labeled images of rulers in various conditions
- Data augmentation (rotation, lighting changes, blur)
- GPU for training (several hours)

**Reference Implementation Pattern:**
```python
# High-level pseudocode
1. Collect dataset: ruler images with labeled tick marks and numbers
2. Train YOLOv8 model to detect:
   - Class 0: ruler main body
   - Class 1: major tick marks
   - Class 2: minor tick marks
   - Class 3: numbers
3. Run inference on video frames
4. Post-process detections → build cm mapping
5. Track across frames using object tracking
```

**Recent Research Results:**
- Pointer meter detection: 98.65% accuracy
- Reading error: 0.67-0.76% for different scales
- YOLOv8-based systems deployable on edge devices

---

## Approach 4: Template Matching

### Method: Match known ruler patterns

**How it works:**
1. Create **templates** of ruler tick marks and numbers
2. Use cv2.matchTemplate to find matches in frames
3. Detect repetitive pattern of tick marks
4. Match number templates to identify cm values

**Advantages:**
- Simple to implement
- No training data needed
- Fast processing
- Good for identical rulers across videos

**Disadvantages:**
- Requires identical ruler appearance
- Fails with rotation, scale changes, or lighting variation
- Not robust to perspective distortion
- Need separate template for each ruler type

**Implementation Complexity:** Low
**Best For:** Fixed experimental setup with same ruler, same angle, same lighting

**Key Libraries:**
- OpenCV (cv2.matchTemplate)
- NumPy for correlation analysis

---

## Approach 5: Hybrid: Classical CV + OCR

### Method: Combine edge detection with modern OCR

**How it works:**
1. **Ruler localization**: Use color thresholding or edge detection to find ruler region
2. **Orientation correction**: Detect ruler angle and rotate to horizontal
3. **Tick detection**: Use vertical edge detection to find tick marks
4. **Number reading**: Use modern OCR (EasyOCR, PaddleOCR) for number recognition
5. **Spatial mapping**: Associate numbers with nearby tick marks

**Advantages:**
- More robust than pure classical methods
- Modern OCR handles various fonts and conditions
- No deep learning training required
- Moderate computational requirements

**Disadvantages:**
- OCR can still fail on small/blurry text
- Requires good ruler contrast
- Complex pipeline with multiple failure points

**Implementation Complexity:** Medium-High
**Best For:** General-purpose solution balancing robustness and simplicity

**Key Libraries:**
- OpenCV for ruler and tick detection
- EasyOCR or PaddleOCR for number reading
- NumPy for spatial analysis

---

## Approach 6: Temporal Tracking

### Method: Detect once, track across frames

**How it works:**
1. **Initial detection**: Use any of the above methods on first frame
2. **Object tracking**: Use optical flow or tracking algorithms to follow ruler in subsequent frames
3. **Re-detection**: Periodically re-detect to correct drift
4. **Motion analysis**: Use frame-to-frame motion to infer displacement without re-reading every time

**Advantages:**
- Very fast after initial detection (real-time capable)
- Robust to temporary occlusions
- Leverages temporal information
- Reduces computational load

**Disadvantages:**
- Tracking can drift over time
- Requires periodic re-detection
- Fails if ruler moves significantly

**Implementation Complexity:** Medium
**Best For:** Video processing where ruler is mostly static

**Key Libraries:**
- OpenCV tracking algorithms (cv2.TrackerKCF, cv2.TrackerCSRT)
- Optical flow (cv2.calcOpticalFlowPyrLK)

---

## Recommended Strategy

### For Your Current Project (Fish Bubble Experiments):

**Phase 1: Proof of Concept (Start Here)**
Use **Approach 1 (Classical CV + Hough Transform)**:
- Quick to implement
- Works with existing videos
- No training data needed
- Good for clean experimental setup

**Implementation Steps:**
1. Extract clear frame from video
2. Apply adaptive thresholding
3. Detect ruler main line with Hough transform
4. Find tick marks perpendicular to main line
5. Measure tick spacing to identify cm marks
6. Use EasyOCR to read numbers near major ticks
7. Build pixel → cm mapping

**Estimated Time:** 2-3 days of development

---

**Phase 2: Improve Robustness (If Phase 1 works but needs improvement)**
Add **Approach 6 (Temporal Tracking)**:
- Detect timeline once in first frame
- Track across subsequent frames
- Re-detect every N frames to prevent drift

**Estimated Time:** 1-2 days additional development

---

**Phase 3: Production Solution (If processing many videos)**
Consider **Approach 2 (ArUco Markers)** for future experiments:
- Place ArUco markers at known cm positions
- 100% reliable detection
- No complex CV pipeline needed
- Can still use old method for existing videos

**Estimated Time:** 1 day to implement, requires physical setup modification

---

**Phase 4: If All Else Fails**
Train **Approach 3 (YOLO)**:
- Collect 200-500 labeled ruler images
- Train YOLOv8 to detect ruler and markings
- Highest robustness, but most effort

**Estimated Time:** 1-2 weeks (data collection + training + testing)

---

## Key Considerations

### Accuracy Requirements
- **High precision needed** (±0.5mm): Use ArUco markers or deep learning
- **Moderate precision OK** (±1-2mm): Classical CV methods sufficient

### Video Characteristics
- **Clean, well-lit, fixed camera**: Classical CV works great
- **Variable lighting, motion blur**: Consider deep learning
- **Ruler always visible**: Template matching or tracking viable
- **Ruler sometimes occluded**: Need robust detection each frame

### Development Resources
- **Quick prototype needed**: Classical CV + OCR
- **Have time to label data**: Deep learning
- **Can modify setup**: ArUco markers
- **Working with existing videos only**: Must use CV or deep learning

### Processing Speed
- **Real-time required**: Tracking + periodic detection, or ArUco
- **Batch processing OK**: Any method works, optimize for accuracy

---

## Technical Implementation Notes

### Common Preprocessing Steps (All Approaches)
```python
# 1. Color space conversion for better contrast
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

# 2. Denoising while preserving edges
denoised = cv2.bilateralFilter(gray, 9, 75, 75)
# OR mean shift filtering for stronger smoothing

# 3. Adaptive thresholding for uneven lighting
thresh = cv2.adaptiveThreshold(gray, 255,
                               cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 11, 2)

# 4. Morphological operations to clean up
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
```

### OCR Best Practices
```python
# Use EasyOCR for better accuracy on small text
import easyocr
reader = easyocr.Reader(['en'])

# Preprocess number regions
roi = cv2.resize(roi, None, fx=2, fy=2)  # Upscale
roi = cv2.GaussianBlur(roi, (3,3), 0)    # Slight blur helps

results = reader.readtext(roi, allowlist='0123456789.')
```

### Tracking Integration
```python
# Initialize tracker on first frame
tracker = cv2.TrackerCSRT_create()
bbox = detect_ruler_bbox(first_frame)  # Your detection method
tracker.init(first_frame, bbox)

# Track in subsequent frames
for frame in video_frames[1:]:
    success, bbox = tracker.update(frame)

    if not success or frame_count % 30 == 0:  # Re-detect every 30 frames
        bbox = detect_ruler_bbox(frame)
        tracker.init(frame, bbox)
```

---

## Next Steps

1. **Start with Approach 1** (Classical CV + Hough Transform)
2. **Test on 5-10 representative frames** from different videos
3. **Measure accuracy** against manual ground truth
4. **If accuracy > 90%**: Great! Implement tracking for speed
5. **If accuracy < 90%**:
   - Try Approach 5 (better OCR)
   - Consider Approach 2 (ArUco) for new experiments
   - If processing many videos, invest in Approach 3 (YOLO)

---

## Questions for Discussion

Before implementing, clarify:

1. **Accuracy needed?** ±0.5mm, ±1mm, or ±2mm acceptable?
2. **Video volume?** Processing 10 videos or 1000 videos?
3. **Ruler consistency?** Same ruler in all videos, or different rulers?
4. **Camera setup?** Fixed position or variable?
5. **Can modify setup?** Willing to add ArUco markers for future experiments?
6. **Timeline type?** Vertical ruler, horizontal ruler, or other measuring device?
7. **Occlusion?** Is ruler sometimes blocked by objects (fish, bubbles)?
8. **Frame-by-frame needed?** Or just need initial calibration?

These answers will guide which approach is most suitable for your specific use case.
