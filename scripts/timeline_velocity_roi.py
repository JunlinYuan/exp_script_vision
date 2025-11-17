#!/usr/bin/env python3
"""
Timeline Velocity Detection with ROI Selection and Y-Averaging

Interactive ROI selection + vertical averaging for robust timeline tracking.
Removes border artifacts by letting user select clean region of interest.

Usage:
    python scripts/timeline_velocity_roi.py \
        --video videos/6cm.mp4 \
        --output outputs/timeline_roi
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
from pathlib import Path


# Global variables for mouse callback
clicks = []
frame_display = None


def mouse_callback(event, x, y, flags, param):
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
        roi: dict with 'x_min', 'x_max', 'y_min', 'y_max'
        first_frame: the frame used for selection
    """
    global clicks, frame_display

    print("="*70)
    print("INTERACTIVE ROI SELECTION")
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
    cv2.setMouseCallback('ROI Selection', mouse_callback)
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
    cv2.destroyAllWindows()

    return roi, first_frame


def extract_spatiotemporal_roi(video_path, roi, max_frames=None):
    """
    Extract ROI from each frame and average over y-direction.

    Args:
        video_path: Path to video file
        roi: ROI dictionary with x_min, x_max, y_min, y_max
        max_frames: Maximum number of frames to process (None = all)

    Returns:
        spatiotemporal_img: 2D array (num_frames, roi_width) for grayscale
                           or 3D array (num_frames, roi_width, 3) for RGB
        fps: Frames per second
        total_frames: Total frames processed
    """
    print("\n" + "="*70)
    print("EXTRACTING Y-AVERAGED SPATIOTEMPORAL DATA")
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
    # Shape: (num_frames, roi_width, 3) for RGB
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
        # Result: (roi_width, 3) array
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
    print(f"  - Frames (Y-axis): {spatiotemporal_img.shape[0]}")
    print(f"  - Horizontal pixels (X-axis): {spatiotemporal_img.shape[1]}")
    print(f"  - Color channels: {spatiotemporal_img.shape[2]}")

    return spatiotemporal_img, fps, len(spatiotemporal_img)


def create_visualizations(spatiotemporal_img, fps, roi, output_prefix, video_name):
    """
    Create and save high-contrast grayscale visualization of the spatiotemporal image.

    Process:
    1. Convert RGB spatiotemporal data to grayscale (single intensity channel)
    2. Use 'hot' colormap for high contrast (dark→red, bright→yellow/white)
    3. Display with pcolormesh for smooth 2D rendering
    """
    num_frames, width = spatiotemporal_img.shape[:2]

    # Convert BGR to RGB for matplotlib
    if len(spatiotemporal_img.shape) == 3:
        img_for_plot = cv2.cvtColor(spatiotemporal_img, cv2.COLOR_BGR2RGB)
    else:
        img_for_plot = spatiotemporal_img

    # Convert to grayscale for high-contrast visualization
    if len(img_for_plot.shape) == 3:
        gray_img = cv2.cvtColor(img_for_plot, cv2.COLOR_RGB2GRAY)
    else:
        gray_img = img_for_plot

    # Create single plot figure
    fig, ax = plt.subplots(1, 1, figsize=(16, 8))

    # High-contrast grayscale visualization
    # pcolormesh with 'hot' colormap: dark values→black/red, bright values→yellow/white
    im = ax.pcolormesh(gray_img, cmap='hot', shading='auto')
    plt.colorbar(im, ax=ax, label='Intensity')

    ax.set_xlabel('Horizontal Position (pixels within ROI)', fontsize=12)
    ax.set_ylabel('Frame Number', fontsize=12)
    ax.set_title(f'Y-Averaged Spatiotemporal Image - {video_name}\n' +
                 f'ROI: X=[{roi["x_min"]}:{roi["x_max"]}], Y=[{roi["y_min"]}:{roi["y_max"]}] (averaged over {roi["height"]} rows)\n' +
                 f'Timeline markers appear as diagonal dark streaks',
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add time axis on right side
    # Time is calculated from video FPS metadata (not an assumption!)
    ax_time = ax.twinx()
    ax_time.set_ylabel('Time (seconds)', fontsize=12)
    ax_time.set_ylim(0, num_frames / fps)

    # Add FPS info as text
    ax.text(0.02, 0.98, f'FPS: {fps:.2f} (from video metadata)\nFrames: {num_frames}',
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    output_path = f"{output_prefix}_spatiotemporal.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_path}")

    plt.close('all')


def main():
    parser = argparse.ArgumentParser(
        description='Timeline velocity detection with ROI selection and Y-averaging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - interactive ROI selection
  python scripts/timeline_velocity_roi.py --video videos/6cm.mp4 --output outputs/6cm_roi

  # Process only first 500 frames
  python scripts/timeline_velocity_roi.py --video videos/6cm.mp4 --output outputs/6cm_roi --max-frames 500

  # Use pre-defined ROI (skip interactive selection)
  python scripts/timeline_velocity_roi.py --video videos/6cm.mp4 --output outputs/6cm_roi --roi roi.json
        """
    )

    parser.add_argument('--video', required=True, help='Path to input video file')
    parser.add_argument('--output', required=True, help='Output prefix for results')
    parser.add_argument('--max-frames', type=int, default=None,
                       help='Maximum number of frames to process (default: all)')
    parser.add_argument('--roi', type=str, default=None,
                       help='Path to ROI JSON file (skip interactive selection)')

    args = parser.parse_args()

    # Validate video path
    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("="*70)
    print("TIMELINE VELOCITY DETECTION - ROI + Y-AVERAGING")
    print("="*70)

    # ROI selection
    if args.roi:
        # Load pre-defined ROI
        print(f"\nLoading ROI from: {args.roi}")
        with open(args.roi, 'r') as f:
            roi = json.load(f)
        first_frame = None
    else:
        # Interactive ROI selection
        roi, first_frame = select_roi_interactive(video_path)

        # Save ROI for future use
        roi_path = f"{args.output}_roi.json"
        with open(roi_path, 'w') as f:
            json.dump(roi, f, indent=2)
        print(f"\n✓ ROI saved to: {roi_path}")

        # Save visualization of ROI selection
        if first_frame is not None:
            roi_vis_path = f"{args.output}_roi_selection.png"
            cv2.imwrite(roi_vis_path, frame_display)
            print(f"✓ ROI visualization saved to: {roi_vis_path}")

    # Extract spatiotemporal data
    spatiotemporal_img, fps, num_frames = extract_spatiotemporal_roi(
        video_path,
        roi,
        max_frames=args.max_frames
    )

    # Save raw data
    data_output = f"{args.output}_data.npy"
    np.save(data_output, spatiotemporal_img)
    print(f"\n✓ Raw data saved to: {data_output}")

    # Create visualizations
    create_visualizations(spatiotemporal_img, fps, roi, args.output, video_path.name)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nResults:")
    print(f"  - ROI: {roi['width']}×{roi['height']} pixels (Y-averaged)")
    print(f"  - Frames processed: {num_frames}")
    print(f"  - FPS: {fps}")
    print(f"  - Duration: {num_frames/fps:.2f} seconds")
    print(f"\nLook for diagonal streaks in the visualization:")
    print(f"  - Vertical streaks = stationary timeline")
    print(f"  - Diagonal streaks = moving timeline")
    print(f"  - Slope = velocity (pixels/frame)")
    print(f"\nVelocity calculation:")
    print(f"  velocity [px/s] = (Δx / Δframes) × {fps:.1f}")
    print("="*70)


if __name__ == "__main__":
    main()
