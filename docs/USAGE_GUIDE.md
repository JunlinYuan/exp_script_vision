# Ruler Calibration Tools - Usage Guide

## Overview

**Problem:** The current `manual.py` requires manually measuring pixel distances on the ruler for each experimental setup, which is time-consuming and error-prone.

**Solution:** Use the new **semi-automatic calibration tool** to calibrate once per setup, then reuse the calibration for all videos from that setup.

---

## Quick Start (Recommended Method)

### Step 1: Calibrate Your Setup (Do Once Per Setup)

**IMPORTANT:** The script works for ANY video! Just change the video filename and output filename.

```bash
# Activate virtual environment
source venv/bin/activate

# Example 1: Calibrate 6cm setup
python scripts/semi_auto_calibration.py --video videos/6cm.mp4 --output outputs/6cm_calibration.json

# Example 2: Calibrate 7cm setup
python scripts/semi_auto_calibration.py --video videos/7cm.mp4 --output outputs/7cm_calibration.json

# Example 3: Calibrate any new setup
python scripts/semi_auto_calibration.py --video videos/YOUR_VIDEO.mp4 --output outputs/YOUR_VIDEO_calibration.json
```

**Pattern:**
- `--video videos/YOUR_VIDEO.mp4` ← Your input video (put videos in `videos/` folder)
- `--output outputs/YOUR_NAME_calibration.json` ← Where to save calibration

**What happens:**
1. A window opens showing the clearest frame from your video
2. **Click on a ruler marking** (e.g., click on the "10" cm mark)
3. **Click on another ruler marking** (e.g., click on the "20" cm mark)
4. Enter the cm value for each click when prompted:
   ```
   What cm value is click 1 at (x, y)? 10
   What cm value is click 2 at (x, y)? 20
   ```
5. Script calculates and saves: **pixels per cm = 62.0** (or whatever your setup is)

**Output:**
- `6cm_calibration.json` - Contains calibration parameters
- `6cm_calibration_visualization.png` - Visual verification of clicks

**Time saved:** ~30 seconds vs 2-3 minutes of manual measurement

---

### Step 2: Use Calibration with Existing Code

Now that you have `6cm_calibration.json`, you can use it in two ways:

####  Manually Copy Value to manual.py

Edit `manual.py` and update the `CM_TO_PIXEL` dictionary:

```python
# In manual.py, line 6-12
CM_TO_PIXEL = {
    6: 62.15,  # Updated from calibration.json!
    7: 61.4,
    8: 61,
    10: 63,
    12: 59.6
}
```

Then run `manual.py` as normal.

<!-- #### Option B: Load from JSON (Future Enhancement)

Add this to `manual.py` to automatically load calibrations:

```python
import json

# Add at top of manual.py
def load_calibration(cm_value):
    """Load calibration from JSON file if it exists"""
    calib_file = f"{cm_value}cm_calibration.json"
    try:
        with open(calib_file, 'r') as f:
            calib = json.load(f)
        return calib['pixels_per_cm']
    except FileNotFoundError:
        return None

# Then in your code:
CM = int(input("input CM value: "))

# Try to load from calibration file first
pixels_per_cm = load_calibration(CM)
if pixels_per_cm:
    print(f"Loaded calibration: {pixels_per_cm:.2f} px/cm from {CM}cm_calibration.json")
else:
    # Fall back to hardcoded dictionary
    pixels_per_cm = CM_TO_PIXEL.get(CM)
``` -->

---

## Working with Multiple Videos

### General Workflow for ANY Video

The calibration tool is **completely general** - it works with any video or image file!

**Step-by-step:**

1. **Put your video in the `videos/` folder**
   ```bash
   cp /path/to/your/experiment_video.mp4 videos/
   ```

2. **Run calibration with your video name**
   ```bash
   source venv/bin/activate
   python scripts/semi_auto_calibration.py \
       --video videos/experiment_video.mp4 \
       --output outputs/experiment_calibration.json
   ```

3. **Click on 2 ruler marks, enter cm values**

4. **Done! Use the calibration**
   - Find `pixels_per_cm` value in `outputs/experiment_calibration.json`
   - Copy to `manual.py` or use in your analysis

**You DON'T need to modify any Python code!** Just change the command-line arguments.

---

## Detailed Workflow

### For New Experimental Setups

When you start a new experiment with a different camera position or ruler placement:

```bash
# 1. Record a short reference video showing the ruler clearly
#    (already done: 6cm.mp4, 7cm.mp4, etc.)

# 2. Run semi-automatic calibration
python scripts/semi_auto_calibration.py --video NEW_SETUP.mp4 --output NEW_SETUP_calibration.json

# 3. Click on 2 ruler marks and enter their cm values

# 4. Done! Use this calibration for ALL videos from this setup
```
---

## File Organization

Recommended structure:

```
exp_script_vision/
├── manual.py                      # Original script (still works!)
├── scripts/                       # NEW: Automated tools
│   └── semi_auto_calibration.py   # Semi-automatic calibration
│
├── 6cm.mp4                        # Reference videos
├── 6cm12hz.mp4                    # Bubble videos
│
├── 6cm_calibration.json           # NEW: Calibration files (reusable!)
├── calibration_visualization.png  # Visual verification
│
├── sample_frames/                 # Extracted frames
├── debug_output/                  # Debug images
│
└── USAGE_GUIDE.md                 # This guide
```

---

## Troubleshooting

### "Module not found" errors

```bash
# Install dependencies
source venv/bin/activate
pip install opencv-python numpy matplotlib scipy
```

### Window doesn't open (macOS)

If the calibration window doesn't appear, you may need to give Python permissions:
- System Preferences → Security & Privacy → Screen Recording
- Allow Terminal or Python

### Clicks not registering

- Make sure the window is in focus (click on it first)
- Click clearly on ruler markings
- If you make a mistake, press ESC and restart

### Want fully automatic detection?

The `auto_ruler_calibration_v3.py` attempts fully automatic detection, but it's not reliable for all ruler types. The semi-automatic method (2 clicks) is recommended for best results.

---

## Advanced: Batch Calibration

If you have many setups to calibrate:

```bash
# Create a simple batch script
for video in *cm.mp4; do
    name=$(basename "$video" .mp4)
    echo "Calibrating $video..."
    python semi_auto_calibration.py --video "$video" --output "${name}_calibration.json"
done
```

---

## Future Enhancements

Potential additions:
1. **Automatic timeline detection** (hard problem, but valuable)
2. **Batch video processing** with saved calibrations
3. **GUI interface** for easier use
4. **Calibration verification** tool

---
