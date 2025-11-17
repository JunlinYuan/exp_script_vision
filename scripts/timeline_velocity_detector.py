#!/usr/bin/env python3
"""
Timeline Velocity Detection via Spatiotemporal Analysis

Extracts a horizontal line from each video frame and stacks them to create
a 2D spatiotemporal image (kymograph). Timeline markers appear as diagonal
streaks whose slope indicates velocity.

Usage:
    python scripts/timeline_velocity_detector.py \
        --video videos/6cm.mp4 \
        --output outputs/timeline_velocity \
        --height 0.5
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import argparse
from pathlib import Path


def extract_spatiotemporal_slice(video_path, height_fraction=0.5, max_frames=None):
    """
    Extract horizontal line from each frame and stack to create spatiotemporal image.

    Args:
        video_path: Path to video file
        height_fraction: Vertical position to extract (0=top, 1=bottom, 0.5=middle)
        max_frames: Maximum number of frames to process (None = all frames)

    Returns:
        spatiotemporal_img: 2D array (num_frames, frame_width) for grayscale
                           or 3D array (num_frames, frame_width, 3) for RGB
        fps: Frames per second of the video
        total_frames: Total number of frames processed
    """
    print(f"Opening video: {video_path}")
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames_in_video = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Determine extraction height (pixel row)
    extraction_row = int(frame_height * height_fraction)

    print(f"Video properties:")
    print(f"  - Resolution: {frame_width}x{frame_height}")
    print(f"  - FPS: {fps}")
    print(f"  - Total frames: {total_frames_in_video}")
    print(f"  - Extracting row {extraction_row} (height fraction: {height_fraction})")

    # Determine how many frames to process
    frames_to_process = min(max_frames, total_frames_in_video) if max_frames else total_frames_in_video

    # Read first frame to determine if we'll use color or grayscale
    ret, first_frame = cap.read()
    if not ret:
        raise ValueError("Cannot read first frame")

    # Extract the line from first frame
    first_line = first_frame[extraction_row, :, :]  # Keep RGB

    # Initialize storage for all lines
    # Shape: (num_frames, frame_width, 3) for RGB
    spatiotemporal_img = np.zeros((frames_to_process, frame_width, 3), dtype=np.uint8)
    spatiotemporal_img[0] = first_line

    # Reset video to beginning
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # Extract lines from all frames
    print(f"Extracting horizontal slices from {frames_to_process} frames...")
    for frame_idx in range(frames_to_process):
        ret, frame = cap.read()
        if not ret:
            print(f"Warning: Could only read {frame_idx} frames")
            spatiotemporal_img = spatiotemporal_img[:frame_idx]
            break

        # Extract the horizontal line at specified height
        line = frame[extraction_row, :, :]  # RGB
        spatiotemporal_img[frame_idx] = line

        # Progress indicator
        if (frame_idx + 1) % 100 == 0 or frame_idx == frames_to_process - 1:
            print(f"  Processed {frame_idx + 1}/{frames_to_process} frames")

    cap.release()

    print(f"Extraction complete! Shape: {spatiotemporal_img.shape}")
    return spatiotemporal_img, fps, len(spatiotemporal_img)


def create_visualizations(spatiotemporal_img, fps, output_prefix, video_name):
    """
    Create and save visualizations of the spatiotemporal image.

    Args:
        spatiotemporal_img: 2D or 3D numpy array
        fps: Frames per second
        output_prefix: Prefix for output files
        video_name: Name of the video for title
    """
    num_frames, width = spatiotemporal_img.shape[:2]

    # Convert BGR (OpenCV) to RGB (matplotlib) if needed
    if len(spatiotemporal_img.shape) == 3:
        img_for_plot = cv2.cvtColor(spatiotemporal_img, cv2.COLOR_BGR2RGB)
    else:
        img_for_plot = spatiotemporal_img

    # Create figure with multiple subplots
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))

    # ===== Plot 1: Full spatiotemporal image =====
    ax1 = axes[0]

    # Use imshow for RGB, pcolormesh for grayscale
    if len(img_for_plot.shape) == 3:
        im1 = ax1.imshow(img_for_plot, aspect='auto', origin='upper')
    else:
        im1 = ax1.pcolormesh(img_for_plot, cmap='gray', shading='auto')
        plt.colorbar(im1, ax=ax1, label='Intensity')

    ax1.set_xlabel('Horizontal Position (pixels)', fontsize=12)
    ax1.set_ylabel('Frame Number', fontsize=12)
    ax1.set_title(f'Spatiotemporal Image - {video_name}\n(Timeline markers should appear as vertical/diagonal streaks)',
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Add secondary y-axis for time
    ax1_time = ax1.twinx()
    ax1_time.set_ylabel('Time (seconds)', fontsize=12)
    ax1_time.set_ylim(0, num_frames / fps)

    # ===== Plot 2: Grayscale version for better contrast =====
    ax2 = axes[1]

    # Convert to grayscale if RGB
    if len(img_for_plot.shape) == 3:
        gray_img = cv2.cvtColor(img_for_plot, cv2.COLOR_RGB2GRAY)
    else:
        gray_img = img_for_plot

    im2 = ax2.pcolormesh(gray_img, cmap='gray', shading='auto')
    plt.colorbar(im2, ax=ax2, label='Intensity')

    ax2.set_xlabel('Horizontal Position (pixels)', fontsize=12)
    ax2.set_ylabel('Frame Number', fontsize=12)
    ax2.set_title('Grayscale Spatiotemporal Image (Enhanced Contrast)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Add secondary y-axis for time
    ax2_time = ax2.twinx()
    ax2_time.set_ylabel('Time (seconds)', fontsize=12)
    ax2_time.set_ylim(0, num_frames / fps)

    plt.tight_layout()

    # Save figure
    output_path = f"{output_prefix}_spatiotemporal.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved to: {output_path}")

    # Also save a high-contrast version
    fig2, ax = plt.subplots(figsize=(16, 8))
    im = ax.pcolormesh(gray_img, cmap='hot', shading='auto')  # 'hot' colormap for high contrast
    plt.colorbar(im, ax=ax, label='Intensity')
    ax.set_xlabel('Horizontal Position (pixels)', fontsize=12)
    ax.set_ylabel('Frame Number', fontsize=12)
    ax.set_title(f'High-Contrast Spatiotemporal Image - {video_name}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add time axis
    ax_time = ax.twinx()
    ax_time.set_ylabel('Time (seconds)', fontsize=12)
    ax_time.set_ylim(0, num_frames / fps)

    plt.tight_layout()
    output_path_hc = f"{output_prefix}_spatiotemporal_highcontrast.png"
    plt.savefig(output_path_hc, dpi=150, bbox_inches='tight')
    print(f"High-contrast version saved to: {output_path_hc}")

    plt.close('all')


def main():
    parser = argparse.ArgumentParser(
        description='Timeline velocity detection via spatiotemporal analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from middle of frame
  python scripts/timeline_velocity_detector.py --video videos/6cm.mp4 --output outputs/6cm_timeline

  # Extract from 60% height (closer to bottom)
  python scripts/timeline_velocity_detector.py --video videos/6cm.mp4 --output outputs/6cm_timeline --height 0.6

  # Process only first 500 frames
  python scripts/timeline_velocity_detector.py --video videos/6cm.mp4 --output outputs/6cm_timeline --max-frames 500
        """
    )

    parser.add_argument('--video', required=True, help='Path to input video file')
    parser.add_argument('--output', required=True, help='Output prefix for results (without extension)')
    parser.add_argument('--height', type=float, default=0.5,
                       help='Vertical position to extract (0=top, 1=bottom, 0.5=middle)')
    parser.add_argument('--max-frames', type=int, default=None,
                       help='Maximum number of frames to process (default: all)')

    args = parser.parse_args()

    # Validate inputs
    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not 0 <= args.height <= 1:
        raise ValueError("Height must be between 0 and 1")

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("TIMELINE VELOCITY DETECTION")
    print("="*60)

    # Extract spatiotemporal slice
    spatiotemporal_img, fps, num_frames = extract_spatiotemporal_slice(
        video_path,
        height_fraction=args.height,
        max_frames=args.max_frames
    )

    # Save raw data
    data_output = f"{args.output}_data.npy"
    np.save(data_output, spatiotemporal_img)
    print(f"\nRaw data saved to: {data_output}")

    # Create visualizations
    create_visualizations(spatiotemporal_img, fps, args.output, video_path.name)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"\nLook for diagonal streaks in the visualization:")
    print(f"  - Vertical streaks = stationary timeline")
    print(f"  - Diagonal streaks = moving timeline")
    print(f"  - Slope of diagonal = velocity (pixels/frame)")
    print(f"\nTo calculate velocity:")
    print(f"  velocity = (horizontal_displacement / vertical_displacement) * fps")
    print(f"  where fps = {fps}")
    print("="*60)


if __name__ == "__main__":
    main()
