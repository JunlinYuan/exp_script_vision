# High-Level Walkthrough: Semi-Automatic Calibration

## What Problem Are We Solving?

When measuring things in videos (like bubble motion), we need to convert **pixels** (what the camera sees) into **real-world measurements** (like centimeters). This conversion factor is called "pixels per cm."

**The old way:** Manually measure pixel distances on screen, manually count, manually calculate. This is:
- Time-consuming (2-3 minutes per setup)
- Error-prone (easy to miscount pixels or misread the ruler)
- Different for each person doing it

**The new way:** Let the computer do the calculation, you just point at two places. This is:
- Fast (30 seconds)
- Consistent (everyone gets the same answer)
- Reusable (calibrate once, use for all videos from that camera setup)

---

## How Does It Work? (The Big Picture)

Think of it like calibrating a scale in the kitchen:

### Step 1: Find a Clear Reference Image
The script automatically looks through your video and picks the **sharpest, clearest frame** to work with. This is like making sure you can clearly see the scale's markings before you start weighing.

**How it picks the best frame:**
- Samples 10 frames evenly throughout the video
- Measures how "sharp" each frame is (using a mathematical sharpness score)
- Picks the sharpest one

### Step 2: You Mark Two Known Points
You click on **two ruler markings** that you can clearly see and identify. For example:
- Click on the "10 cm" mark → Tell the computer "this is 10"
- Click on the "20 cm" mark → Tell the computer "this is 20"

**Why two points?**
- We know the real-world distance (20 cm - 10 cm = 10 cm)
- The computer can measure the pixel distance (e.g., 620 pixels)
- Simple division: 620 pixels ÷ 10 cm = **62 pixels per cm**

This is like putting a known weight (say, 100 grams) on a scale to verify it's working correctly.

### Step 3: Computer Calculates the Conversion
The computer does the math:
- Measures the pixel distance between your two clicks using the Pythagorean theorem (√((x₂-x₁)² + (y₂-y₁)²))
- Divides by the real-world distance you told it
- Saves the result as **pixels per cm**

### Step 4: Save and Reuse
The calibration is saved to a file (JSON format) so you can:
- Use it for **all videos** recorded with that same camera setup
- Share it with other people analyzing the same videos
- Verify the calibration later by looking at the saved visualization

---

## Why Might Your Measurement Be Wrong?

If your measurements aren't matching what's expected, here are the most common reasons:

### 1. **Camera Moved Between Videos**
If the camera was repositioned even slightly between recording the calibration video and your experimental video, the pixels-per-cm ratio will be different.

**Solution:** Always calibrate using a video from the exact same camera position.

### 2. **Clicking on Wrong Points**
If you accidentally clicked on the wrong ruler markings (e.g., thought you clicked on "10" but it was actually "9.5"), your calibration will be off.

**Solution:** Zoom in if needed, and make sure you're clicking exactly on the cm markings you intend.

### 3. **Perspective/Angle Issues**
If the ruler is at an angle to the camera, or if things you're measuring are at a different depth than the ruler, distances will appear distorted.

**Solution:**
- Make sure the ruler is in the same plane as what you're measuring
- If measuring 3D motion, you need separate calibrations for each depth plane

### 4. **Using the Wrong Calibration File**
If you have multiple setups (6cm, 7cm, 8cm, etc.) and use the wrong calibration file, measurements will be incorrect.

**Solution:** Double-check which calibration file corresponds to which experimental video.

---

## The Complete Process (Visual Summary)

```
📹 Video Recording
    ↓
[Step 1] Extract clearest frame
    ↓
[Step 2] Click on 2 ruler marks → Enter their cm values
    ↓
[Step 3] Computer calculates: pixels ÷ cm = pixels_per_cm
    ↓
[Step 4] Save calibration.json
    ↓
[Step 5] Use for all videos from same setup
    ↓
🎯 Accurate measurements!
```

---

## Key Advantages Over Manual Method

| Aspect | Manual Method | Semi-Auto Method |
|--------|--------------|------------------|
| **Time** | 2-3 minutes per setup | 30 seconds per setup |
| **Accuracy** | Depends on person | Consistent |
| **Reusability** | Must re-measure | Calibrate once, use forever |
| **Verification** | Hard to verify | Saves visualization image |
| **Sharing** | Hard to reproduce | Share JSON file |

---

## What You Need to Know for Your Measurements

When you're calibrating for your experiment:

1. **Record a clear reference video** showing the ruler in the same position as your experiment
2. **Run the calibration script** and click on two ruler markings you can clearly identify
3. **Verify the result** by looking at the saved visualization image
4. **Use the same calibration** for all videos from that camera setup
5. **If measurements seem wrong**, re-calibrate with a new reference video

---

## Questions to Ask Yourself When Debugging

If your measurements don't look right:

- [ ] Did the camera position change between calibration and experiment?
- [ ] Are you measuring at the same depth/plane as the ruler?
- [ ] Did you click on the correct ruler markings?
- [ ] Are you using the correct calibration file for this video?
- [ ] Is the ruler clearly visible in your reference video?

---

## What Makes This "Semi-Automatic"?

- **Automatic part:**
  - Finds the clearest frame
  - Measures pixel distances
  - Calculates the conversion factor
  - Saves and visualizes results

- **Manual part (you do):**
  - Click on 2 ruler markings
  - Tell the computer what cm values those are

This hybrid approach combines the **speed and consistency of automation** with the **reliability of human visual recognition**. Humans are still better at identifying "this is the 10 cm mark" than computers are!

---

## Next Steps

After understanding calibration, the next challenge is **automatic timeline detection** - can we teach the computer to automatically find and read ruler markings in every frame? This is a harder problem we're working on next.
