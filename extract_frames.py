import cv2
import os
video_path = 'output_videos/tacticam.mp4'
output_folder = 'frames/Tacticam'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
video_capture = cv2.VideoCapture(video_path)
if not video_capture.isOpened():
    print(f"Error: Could not open video file at {video_path}")
    exit()
frame_count = 0
while True:
    success, frame = video_capture.read()
    if not success:
        break
    output_path = os.path.join(output_folder, f"frame_{frame_count:04d}.jpg")
    cv2.imwrite(output_path, frame)
    frame_count += 1
video_capture.release()
print(f"Successfully extracted {frame_count} frames to the '{output_folder}' directory.")