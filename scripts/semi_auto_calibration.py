"""
Semi-Automatic Ruler Calibration

User clicks on 2 ruler markings (e.g., 10cm and 20cm marks),
script automatically calculates pixels per cm.

This is MUCH faster than the current manual method while being more reliable
than fully automatic detection.

Usage:
    python semi_auto_calibration.py --video 6cm.mp4 --output calibration.json
"""

import cv2
import numpy as np
import json
import argparse


# Global variables for mouse callback
clicks = []
frame_display = None


def mouse_callback(event, x, y, flags, param):
    """Handle mouse clicks to select ruler markings"""
    global clicks, frame_display

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicks) < 2:
            clicks.append((x, y))
            print(f"  Click {len(clicks)}: ({x}, {y})")

            # Draw the click on the display
            cv2.circle(frame_display, (x, y), 8, (0, 255, 0), -1)
            cv2.putText(frame_display, f"Click {len(clicks)}", (x+15, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if len(clicks) == 2:
                # Draw line between the two points
                cv2.line(frame_display, clicks[0], clicks[1], (0, 255, 0), 2)

                # Calculate and display pixel distance
                pixel_dist = np.sqrt((clicks[1][0] - clicks[0][0])**2 +
                                    (clicks[1][1] - clicks[0][1])**2)
                mid_x = (clicks[0][0] + clicks[1][0]) // 2
                mid_y = (clicks[0][1] + clicks[1][1]) // 2

                cv2.putText(frame_display, f"{pixel_dist:.1f} pixels",
                           (mid_x, mid_y - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            cv2.imshow('Ruler Calibration', frame_display)


def extract_best_frame(video_path, sample_size=10):
    """Extract the clearest frame from video or load image"""
    # Check if it's an image file
    if video_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        print(f"Loading image: {video_path}")
        frame = cv2.imread(video_path)
        if frame is None:
            raise ValueError(f"Could not load image: {video_path}")
        print(f"Image loaded successfully: {frame.shape[1]}x{frame.shape[0]} pixels")
        return frame

    # It's a video file
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video: {video_path}")
    print(f"Total frames: {total_frames}")

    if total_frames <= 0:
        raise ValueError(f"Invalid video file or could not read frames: {video_path}")

    frame_indices = np.linspace(0, total_frames-1, sample_size, dtype=int)
    frames = []
    sharpness_scores = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            frames.append(frame)
            sharpness_scores.append(sharpness)

    cap.release()

    best_idx = np.argmax(sharpness_scores)
    best_frame = frames[best_idx]

    print(f"Selected frame {frame_indices[best_idx]} (sharpness: {sharpness_scores[best_idx]:.2f})")
    return best_frame


def calibrate_semi_auto(video_path, output_json='calibration.json'):
    """
    Semi-automatic calibration:
    1. Display frame with ruler
    2. User clicks on 2 cm markings
    3. User enters the cm values of those markings
    4. Script calculates pixels per cm
    """
    global clicks, frame_display

    print("="*70)
    print("SEMI-AUTOMATIC RULER CALIBRATION")
    print("="*70)

    # Extract best frame
    print("\n[1/3] Extracting frame...")
    frame = extract_best_frame(video_path)
    frame_display = frame.copy()

    # Get user clicks
    print("\n[2/3] Click on 2 ruler markings...")
    print("  Instructions:")
    print("    1. Click on a cm marking (e.g., the '10' mark on the ruler)")
    print("    2. Click on another cm marking (e.g., the '20' mark)")
    print("    3. The script will calculate pixels per cm")
    print("\n  Waiting for clicks...")

    clicks = []

    cv2.namedWindow('Ruler Calibration')
    cv2.setMouseCallback('Ruler Calibration', mouse_callback)
    cv2.imshow('Ruler Calibration', frame_display)

    # Wait for 2 clicks
    while len(clicks) < 2:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC to cancel
            cv2.destroyAllWindows()
            print("\nCalibration cancelled")
            return None

    print("\n  Got 2 clicks!")

    # Get cm values
    print("\n[3/3] Enter the cm values...")
    try:
        cm1 = float(input(f"  What cm value is click 1 at ({clicks[0][0]}, {clicks[0][1]})? "))
        cm2 = float(input(f"  What cm value is click 2 at ({clicks[1][0]}, {clicks[1][1]})? "))
    except ValueError:
        print("Error: Invalid input")
        cv2.destroyAllWindows()
        return None

    # Calculate calibration
    pixel_dist = np.sqrt((clicks[1][0] - clicks[0][0])**2 +
                        (clicks[1][1] - clicks[0][1])**2)
    cm_dist = abs(cm2 - cm1)

    if cm_dist == 0:
        print("Error: cm values must be different")
        cv2.destroyAllWindows()
        return None

    pixels_per_cm = pixel_dist / cm_dist

    print("\n" + "="*70)
    print("CALIBRATION RESULTS")
    print("="*70)
    print(f"  Click 1: ({clicks[0][0]}, {clicks[0][1]}) = {cm1} cm")
    print(f"  Click 2: ({clicks[1][0]}, {clicks[1][1]}) = {cm2} cm")
    print(f"  Pixel distance: {pixel_dist:.2f} pixels")
    print(f"  Physical distance: {cm_dist:.2f} cm")
    print(f"  Pixels per cm: {pixels_per_cm:.2f}")
    print("="*70)

    # Create calibration data
    calibration = {
        'pixels_per_cm': float(pixels_per_cm),
        'method': 'semi_automatic',
        'click1': {'x': int(clicks[0][0]), 'y': int(clicks[0][1]), 'cm': float(cm1)},
        'click2': {'x': int(clicks[1][0]), 'y': int(clicks[1][1]), 'cm': float(cm2)},
        'pixel_distance': float(pixel_dist),
        'physical_distance': float(cm_dist),
        'video_path': str(video_path)
    }

    # Save to JSON
    with open(output_json, 'w') as f:
        json.dump(calibration, f, indent=2)
    print(f"\n✓ Saved calibration to {output_json}")

    # Update display with final result
    result_text = f"Calibration: {pixels_per_cm:.2f} px/cm"
    cv2.putText(frame_display, result_text, (10, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

    cv2.imshow('Ruler Calibration', frame_display)
    print("\nPress any key to save and close...")
    cv2.waitKey(0)

    # Save visualization
    vis_output = output_json.replace('.json', '_visualization.png')
    cv2.imwrite(vis_output, frame_display)
    print(f"✓ Saved visualization to {vis_output}")

    cv2.destroyAllWindows()

    return calibration


def main():
    parser = argparse.ArgumentParser(description='Semi-automatic ruler calibration')
    parser.add_argument('--video', type=str, required=True,
                       help='Path to reference video')
    parser.add_argument('--output', type=str, default='calibration.json',
                       help='Output calibration JSON file')

    args = parser.parse_args()

    calibration = calibrate_semi_auto(args.video, args.output)

    if calibration:
        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"Calibration: {calibration['pixels_per_cm']:.2f} pixels/cm")
        print(f"Saved to: {args.output}")
        print("\nYou can now use this calibration file for all videos from this setup!")
        print("="*70)
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
