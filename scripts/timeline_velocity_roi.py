#!/usr/bin/env python3
"""
Timeline Velocity Detection with ROI Selection and Y-Averaging

Interactive workflow:
1. Select ROI on first frame
2. Extract and Y-average spatiotemporal data
3. Select 2 points on timeline streak to measure velocity
4. Save consolidated results (JSON + combined image)

Usage:
    python scripts/timeline_velocity_roi.py \
        --video videos/6cm12hz.mp4 \
        --output outputs/6cm12hz_analysis
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import argparse
import json
from pathlib import Path
from datetime import datetime


# Global variables for mouse callbacks
clicks = []
frame_display = None


def mouse_callback_roi(event, x, y, flags, param):
    """Handle mouse clicks to select ROI corners"""
    global clicks, frame_display

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicks) < 2:
            clicks.append((x, y))
            print(f"  Click {len(clicks)}: ({x}, {y})")

            # Draw the click on the display
            cv2.circle(frame_display, (x, y), 10, (0, 255, 0), -1)
            cv2.putText(frame_display, f"Corner {len(clicks)}", (x+15, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            if len(clicks) == 2:
                # Draw rectangle
                cv2.rectangle(frame_display, clicks[0], clicks[1], (0, 255, 0), 3)

                # Calculate and display ROI dimensions
                width = abs(clicks[1][0] - clicks[0][0])
                height = abs(clicks[1][1] - clicks[0][1])

                mid_x = (clicks[0][0] + clicks[1][0]) // 2
                mid_y = (clicks[0][1] + clicks[1][1]) // 2

                cv2.putText(frame_display, f"ROI: {width}x{height} pixels",
                           (mid_x - 100, mid_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)

            cv2.imshow('ROI Selection', frame_display)


def select_roi_interactive(video_path):
    """
    Display first frame and let user select ROI by clicking 2 diagonal corners.

    Returns:
        roi: dict with ROI coordinates and dimensions
        first_frame: the frame used for selection
        roi_frame: the annotated frame showing ROI selection
    """
    global clicks, frame_display

    print("="*70)
    print("STEP 1: INTERACTIVE ROI SELECTION")
    print("="*70)

    # Load first frame
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    ret, first_frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError("Cannot read first frame")

    frame_display = first_frame.copy()

    print("\nInstructions:")
    print("  1. Click on TOP-LEFT corner of the region you want to analyze")
    print("  2. Click on BOTTOM-RIGHT corner of the region")
    print("  3. This box should EXCLUDE borders with artifacts/reflections")
    print("  4. The region will be Y-AVERAGED for timeline detection")
    print("\nWaiting for clicks...")

    clicks = []

    cv2.namedWindow('ROI Selection')
    cv2.setMouseCallback('ROI Selection', mouse_callback_roi)
    cv2.imshow('ROI Selection', frame_display)

    # Wait for 2 clicks
    while len(clicks) < 2:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC to cancel
            cv2.destroyAllWindows()
            raise KeyboardInterrupt("ROI selection cancelled")

    print("\nGot 2 clicks! ROI selected.")

    # Calculate ROI bounds (handle any order of clicks)
    x_min = min(clicks[0][0], clicks[1][0])
    x_max = max(clicks[0][0], clicks[1][0])
    y_min = min(clicks[0][1], clicks[1][1])
    y_max = max(clicks[0][1], clicks[1][1])

    roi = {
        'x_min': x_min,
        'x_max': x_max,
        'y_min': y_min,
        'y_max': y_max,
        'width': x_max - x_min,
        'height': y_max - y_min
    }

    print(f"\nROI defined:")
    print(f"  X range: {roi['x_min']} to {roi['x_max']} ({roi['width']} pixels)")
    print(f"  Y range: {roi['y_min']} to {roi['y_max']} ({roi['height']} pixels)")
    print(f"  Area: {roi['width']} × {roi['height']} = {roi['width']*roi['height']:,} pixels")

    print("\nPress any key to continue...")
    cv2.waitKey(0)

    # Save the annotated frame
    roi_frame = frame_display.copy()
    cv2.destroyAllWindows()

    return roi, first_frame, roi_frame


def extract_spatiotemporal_roi(video_path, roi, max_frames=None):
    """
    Extract ROI from each frame and average over y-direction.

    Returns:
        spatiotemporal_img: 3D array (num_frames, roi_width, 3)
        fps: Frames per second
        total_frames: Total frames processed
    """
    print("\n" + "="*70)
    print("STEP 2: EXTRACTING Y-AVERAGED SPATIOTEMPORAL DATA")
    print("="*70)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames_in_video = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames_to_process = min(max_frames, total_frames_in_video) if max_frames else total_frames_in_video

    print(f"Video properties:")
    print(f"  - FPS: {fps}")
    print(f"  - Total frames: {total_frames_in_video}")
    print(f"  - Processing: {frames_to_process} frames")
    print(f"\nROI extraction:")
    print(f"  - X: {roi['x_min']}:{roi['x_max']} ({roi['width']} pixels)")
    print(f"  - Y: {roi['y_min']}:{roi['y_max']} ({roi['height']} pixels)")
    print(f"  - Y-averaging over {roi['height']} rows")

    # Initialize storage
    spatiotemporal_img = np.zeros((frames_to_process, roi['width'], 3), dtype=np.float32)

    print(f"\nExtracting and averaging...")
    for frame_idx in range(frames_to_process):
        ret, frame = cap.read()
        if not ret:
            print(f"Warning: Could only read {frame_idx} frames")
            spatiotemporal_img = spatiotemporal_img[:frame_idx]
            break

        # Extract ROI
        roi_crop = frame[roi['y_min']:roi['y_max'], roi['x_min']:roi['x_max'], :]

        # Average over y-direction (axis=0)
        y_averaged = np.mean(roi_crop, axis=0)

        spatiotemporal_img[frame_idx] = y_averaged

        # Progress indicator
        if (frame_idx + 1) % 100 == 0 or frame_idx == frames_to_process - 1:
            print(f"  Processed {frame_idx + 1}/{frames_to_process} frames")

    cap.release()

    # Convert to uint8 for visualization
    spatiotemporal_img = spatiotemporal_img.astype(np.uint8)

    print(f"\nExtraction complete!")
    print(f"  Final shape: {spatiotemporal_img.shape}")

    return spatiotemporal_img, fps, len(spatiotemporal_img)


def select_velocity_points_interactive(spatiotemporal_img, fps):
    """
    Display spatiotemporal image and let user select 2 points on a timeline streak.

    Returns:
        velocity_data: dict with points and calculated velocity
        annotated_img: grayscale image with velocity line drawn
    """
    global clicks, frame_display

    print("\n" + "="*70)
    print("STEP 3: INTERACTIVE VELOCITY MEASUREMENT")
    print("="*70)

    # Convert to grayscale for display
    if len(spatiotemporal_img.shape) == 3:
        img_rgb = cv2.cvtColor(spatiotemporal_img, cv2.COLOR_BGR2RGB)
        gray_img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    else:
        gray_img = spatiotemporal_img

    # Create color display image (map grayscale to hot colormap for visibility)
    gray_normalized = (gray_img - gray_img.min()) / (gray_img.max() - gray_img.min())
    display_img = plt.cm.hot(gray_normalized)
    display_img = (display_img[:, :, :3] * 255).astype(np.uint8)

    # Resize for better visibility if needed
    display_scale = 3
    display_height, display_width = gray_img.shape
    display_img_large = cv2.resize(display_img, (display_width * display_scale, display_height * display_scale),
                                   interpolation=cv2.INTER_NEAREST)

    frame_display = display_img_large.copy()

    print("\nInstructions:")
    print("  1. Click on the FIRST point along a diagonal timeline streak")
    print("  2. Click on the SECOND point along the SAME diagonal streak")
    print("  3. The velocity will be calculated from these two points")
    print(f"  Note: Image is scaled {display_scale}x for easier selection")
    print("\nWaiting for clicks...")

    clicks = []

    def mouse_callback_velocity(event, x, y, flags, param):
        """Handle mouse clicks for velocity point selection"""
        global clicks, frame_display

        if event == cv2.EVENT_LBUTTONDOWN:
            if len(clicks) < 2:
                # Convert display coordinates back to original image coordinates
                orig_x = x // display_scale
                orig_y = y // display_scale

                clicks.append((orig_x, orig_y))
                print(f"  Click {len(clicks)}: x={orig_x} pixels, frame={orig_y}, time={orig_y/fps:.3f}s")

                # Draw on display image (scaled coordinates)
                cv2.circle(frame_display, (x, y), 8, (0, 255, 0), -1)
                cv2.putText(frame_display, f"P{len(clicks)}", (x+15, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                if len(clicks) == 2:
                    # Draw line between points (scaled coordinates)
                    pt1_scaled = (clicks[0][0] * display_scale, clicks[0][1] * display_scale)
                    pt2_scaled = (clicks[1][0] * display_scale, clicks[1][1] * display_scale)
                    cv2.line(frame_display, pt1_scaled, pt2_scaled, (0, 255, 255), 3)

                cv2.imshow('Velocity Measurement', frame_display)

    cv2.namedWindow('Velocity Measurement')
    cv2.setMouseCallback('Velocity Measurement', mouse_callback_velocity)
    cv2.imshow('Velocity Measurement', frame_display)

    # Wait for 2 clicks
    while len(clicks) < 2:
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC to cancel
            cv2.destroyAllWindows()
            raise KeyboardInterrupt("Velocity measurement cancelled")

    print("\nGot 2 clicks! Calculating velocity...")

    # Calculate velocity
    x1, frame1 = clicks[0]
    x2, frame2 = clicks[1]

    t1 = frame1 / fps
    t2 = frame2 / fps

    delta_x = x2 - x1
    delta_t = t2 - t1

    if delta_t == 0:
        print("Warning: Same frame selected for both points!")
        velocity = 0
    else:
        velocity = delta_x / delta_t

    velocity_data = {
        'point1': {
            'x_position_pixels': int(x1),
            'frame_number': int(frame1),
            'time_seconds': float(t1)
        },
        'point2': {
            'x_position_pixels': int(x2),
            'frame_number': int(frame2),
            'time_seconds': float(t2)
        },
        'delta_x_pixels': float(delta_x),
        'delta_t_seconds': float(delta_t),
        'velocity_pixels_per_second': float(velocity)
    }

    print(f"\nVelocity calculation:")
    print(f"  Point 1: x={x1} px, t={t1:.3f}s")
    print(f"  Point 2: x={x2} px, t={t2:.3f}s")
    print(f"  Δx = {delta_x:.1f} pixels")
    print(f"  Δt = {delta_t:.3f} seconds")
    print(f"  Velocity = {velocity:.2f} pixels/second")

    print("\nPress any key to continue...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Create annotated image at original scale
    annotated_img = display_img.copy()
    cv2.circle(annotated_img, (x1, frame1), 5, (0, 255, 0), -1)
    cv2.circle(annotated_img, (x2, frame2), 5, (0, 255, 0), -1)
    cv2.line(annotated_img, (x1, frame1), (x2, frame2), (0, 255, 255), 2)

    return velocity_data, annotated_img, gray_img


def create_combined_visualization(roi_frame, gray_img, annotated_img, roi, fps, velocity_data,
                                  video_name, num_frames):
    """
    Create combined visualization with ROI selection and spatiotemporal image.

    Returns:
        fig: matplotlib figure object
    """
    # Create figure with 2 subplots
    fig, axes = plt.subplots(2, 1, figsize=(16, 12))

    # ===== Top plot: ROI Selection =====
    ax1 = axes[0]

    # Convert BGR to RGB for display
    roi_frame_rgb = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2RGB)
    ax1.imshow(roi_frame_rgb)
    ax1.set_xlabel('X Position (pixels)', fontsize=12)
    ax1.set_ylabel('Y Position (pixels)', fontsize=12)
    ax1.set_title(f'ROI Selection - {video_name}\n' +
                  f'ROI: X=[{roi["x_min"]}:{roi["x_max"]}], Y=[{roi["y_min"]}:{roi["y_max"]}] ' +
                  f'({roi["width"]}×{roi["height"]} pixels, averaged over {roi["height"]} rows)',
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # ===== Bottom plot: Spatiotemporal with velocity measurement =====
    ax2 = axes[1]

    # Display annotated spatiotemporal image
    im2 = ax2.pcolormesh(gray_img, cmap='hot', shading='auto')
    plt.colorbar(im2, ax=ax2, label='Intensity')

    # Draw velocity line
    x1 = velocity_data['point1']['x_position_pixels']
    f1 = velocity_data['point1']['frame_number']
    x2 = velocity_data['point2']['x_position_pixels']
    f2 = velocity_data['point2']['frame_number']

    ax2.plot([x1, x2], [f1, f2], 'c-', linewidth=3, label='Velocity measurement')
    ax2.plot([x1, x2], [f1, f2], 'go', markersize=8)

    # Add velocity annotation
    mid_x = (x1 + x2) / 2
    mid_y = (f1 + f2) / 2
    velocity = velocity_data['velocity_pixels_per_second']
    ax2.text(mid_x, mid_y - 10, f'v = {velocity:.2f} px/s',
            fontsize=12, color='white', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
            ha='center')

    ax2.set_xlabel('Horizontal Position (pixels within ROI)', fontsize=12)
    ax2.set_ylabel('Frame Number', fontsize=12)
    ax2.set_title(f'Y-Averaged Spatiotemporal Image with Velocity Measurement\n' +
                  f'Velocity = {velocity:.2f} pixels/second',
                  fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')

    # Add time axis
    ax2_time = ax2.twinx()
    ax2_time.set_ylabel('Time (seconds)', fontsize=12)
    ax2_time.set_ylim(0, num_frames / fps)

    # Add metadata box
    metadata_text = f'FPS: {fps:.2f}\nFrames: {num_frames}\nDuration: {num_frames/fps:.2f}s'
    ax2.text(0.02, 0.98, metadata_text,
            transform=ax2.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

    plt.tight_layout()

    return fig


def save_consolidated_results(output_prefix, roi, video_path, fps, num_frames,
                              velocity_data, fig, spatiotemporal_img):
    """
    Save consolidated JSON and combined image.
    """
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)

    # Create consolidated JSON
    results = {
        'case_name': Path(output_prefix).name,
        'timestamp': datetime.now().isoformat(),
        'video_path': str(video_path),
        'roi': roi,
        'video_info': {
            'fps': float(fps),
            'total_frames': int(num_frames),
            'duration_seconds': float(num_frames / fps)
        },
        'velocity': velocity_data
    }

    # Save JSON
    json_path = f"{output_prefix}.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✓ Results saved to: {json_path}")

    # Save combined image
    image_path = f"{output_prefix}.png"
    fig.savefig(image_path, dpi=150, bbox_inches='tight')
    print(f"✓ Visualization saved to: {image_path}")

    # Save raw data
    data_path = f"{output_prefix}_data.npy"
    np.save(data_path, spatiotemporal_img)
    print(f"✓ Raw data saved to: {data_path}")

    plt.close(fig)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nGenerated files:")
    print(f"  1. {json_path} - All metadata and results")
    print(f"  2. {image_path} - Combined visualization")
    print(f"  3. {data_path} - Raw spatiotemporal data")
    print(f"\nVelocity: {velocity_data['velocity_pixels_per_second']:.2f} pixels/second")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Timeline velocity detection with ROI selection and Y-averaging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full interactive workflow
  python scripts/timeline_velocity_roi.py \\
      --video videos/6cm12hz.mp4 \\
      --output outputs/6cm12hz_analysis

  # Process only first 500 frames
  python scripts/timeline_velocity_roi.py \\
      --video videos/6cm12hz.mp4 \\
      --output outputs/6cm12hz_test \\
      --max-frames 500

Output files:
  - <output>.json         All metadata and results
  - <output>.png          Combined ROI + spatiotemporal visualization
  - <output>_data.npy     Raw spatiotemporal data array
        """
    )

    parser.add_argument('--video', required=True, help='Path to input video file')
    parser.add_argument('--output', required=True, help='Output prefix for results (without extension)')
    parser.add_argument('--max-frames', type=int, default=None,
                       help='Maximum number of frames to process (default: all)')

    args = parser.parse_args()

    # Validate inputs
    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("="*70)
    print("TIMELINE VELOCITY DETECTION - INTERACTIVE WORKFLOW")
    print("="*70)
    print(f"Video: {video_path}")
    print(f"Output: {args.output}")
    print("="*70)

    # Step 1: ROI Selection
    roi, first_frame, roi_frame = select_roi_interactive(video_path)

    # Step 2: Extract spatiotemporal data
    spatiotemporal_img, fps, num_frames = extract_spatiotemporal_roi(
        video_path, roi, max_frames=args.max_frames
    )

    # Step 3: Velocity measurement
    velocity_data, annotated_img, gray_img = select_velocity_points_interactive(
        spatiotemporal_img, fps
    )

    # Step 4: Create combined visualization
    fig = create_combined_visualization(
        roi_frame, gray_img, annotated_img, roi, fps, velocity_data,
        video_path.name, num_frames
    )

    # Step 5: Save consolidated results
    save_consolidated_results(
        args.output, roi, video_path, fps, num_frames,
        velocity_data, fig, spatiotemporal_img
    )


if __name__ == "__main__":
    main()
