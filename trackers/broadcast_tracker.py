from ultralytics import YOLO
import supervision as sv
import pickle
import os
import numpy as np
import cv2
import sys
sys.path.append('../')
from utils import get_center_of_bbox, get_bbox_width
class BroadcastTracker:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.tracker = sv.ByteTrack()
    def detect_frames(self, frames):
        batch_size = 20
        detections = []
        for i in range(0, len(frames), batch_size):
            detections_batch = self.model.predict(frames[i:i + batch_size], conf=0.1)
            detections += detections_batch
        return detections
    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            with open(stub_path, 'rb') as f:
                tracks = pickle.load(f)
            return tracks
        detections = self.detect_frames(frames)
        tracks = {"players": [], "referees": [], "ball": []}
        for frame_num, detection in enumerate(detections):
            cls_names = detection.names
            cls_names_inv = {v: k for k, v in cls_names.items()}
            detection_supervision = sv.Detections.from_ultralytics(detection)
            for object_ind, class_id in enumerate(detection_supervision.class_id):
                if cls_names[class_id] == "goalkeeper":
                    detection_supervision.class_id[object_ind] = cls_names_inv["player"]
            detection_with_tracks = self.tracker.update_with_detections(detection_supervision)
            tracks["players"].append({})
            tracks["referees"].append({})
            tracks["ball"].append({})
            for frame_detection in detection_with_tracks:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]
                track_id = frame_detection[4]
                if cls_id == cls_names_inv['player']:
                    tracks["players"][frame_num][track_id] = {"bbox": bbox}
                if cls_id == cls_names_inv['referee']:
                    tracks["referees"][frame_num][track_id] = {"bbox": bbox}
            for frame_detection in detection_supervision:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]
                if cls_id == cls_names_inv['ball']:
                    tracks["ball"][frame_num][1] = {"bbox": bbox}
        if stub_path is not None:
            with open(stub_path, 'wb') as f:
                pickle.dump(tracks, f)
        return tracks
    def draw_ellipse(self, frame, bbox, color, label=None, track_id=None):
        y2 = int(bbox[3])
        x_center, _ = get_center_of_bbox(bbox)
        width = get_bbox_width(bbox)
        if track_id == 2:
            ellipse_axes = (int(width * 5.5), int(2.5 * width))
            thickness = 3
            ellipse_center = (x_center - 100, y2 + 70 + int(3.5 * width))
            angle = 0.0
            start_angle = -82
            end_angle = 229
        else:
            ellipse_axes = (int(width * 0.9), int(0.4 * width))
            thickness = 2
            ellipse_center = (x_center, y2)
            angle = 0.0
            start_angle = -45
            end_angle = 245
        cv2.ellipse(
            frame,
            center=ellipse_center,
            axes=ellipse_axes,
            angle=angle,
            startAngle=start_angle,
            endAngle=end_angle,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_4
        )
        if label is not None:
            rectangle_width = 150
            rectangle_height = 35
            x1_rect = x_center - rectangle_width // 2
            x2_rect = x_center + rectangle_width // 2
            y1_rect = (y2 - rectangle_height // 2) + 15
            y2_rect = (y2 + rectangle_height // 2) + 15
            cv2.rectangle(
                frame,
                (int(x1_rect), int(y1_rect)),
                (int(x2_rect), int(y2_rect)),
                color,
                cv2.FILLED
            )
            cv2.putText(
                frame,
                label,
                (int(x1_rect + 10), int(y1_rect + 22)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 0),
                2
            )
        return frame
    def draw_traingle(self, frame, bbox, color):
        y = int(bbox[1])
        x, _ = get_center_of_bbox(bbox)
        triangle_points = np.array([
            [x, y],
            [x - 18, y - 35],
            [x + 18, y - 35]
        ])
        cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
        cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)
        return frame
    def draw_annotations(self, video_frames, tracks):
        output_video_frames = []
        skip_ball_triangle_frames = {
            18, 23, 24, 25, 26, 27, 28, 31, 32, 34, 35, 
            36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 
            49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 
            62, 63, 64, 65, 66, 67, 68, 69, 71, 75, 79, 80, 81, 82, 
            83, 85, 87, 95, 97, 98, 105, 106, 107, 114
        }
        white_ids = {2, 17, 16, 14, 11, 12, 58, 70, 106}
        red_ids = {13, 20, 21, 15, 18, 25, 104, 139}
        yellow_ids = {19, 22, 33, 47, 42}
        exclude_ids = {131, 65, 84, 123, 1, 3, 138, 119}
        referee_exclude_ids = {33, 42, 76, 133, 141}
        name_map = {
            2: "Valverde", 16: "Carvajal", 70: "Carvajal", 14: "Benzema", 12: "Vinicius Jr",
            106: "Vinicius Jr", 11: "Kroos", 13: "Van Dijk", 20: "Fabinho", 21: "Henderson",
            15: "Konate", 18: "Trent", 25: "Allison", 104: "Allison", 139: "Fabinho", 58: "Valverde"
        }
        fps = 24
        for frame_num, frame in enumerate(video_frames):
            time_sec = frame_num / fps
            frame = frame.copy()
            player_dict = tracks["players"][frame_num]
            ball_dict = tracks["ball"][frame_num]
            referee_dict = tracks["referees"][frame_num]
            if 0.0 <= time_sec < 1.8:
                name_map[17] = "Valverde"
            if time_sec <= 2.8:
                name_map[14] = "Benzema"
                name_map[15] = "Konate"
            if time_sec >= 2.9:
                red_ids.discard(15)
                white_ids.add(15)
                name_map[15] = "Benzema"
                white_ids.discard(14)
                red_ids.add(14)
                name_map[14] = "Konate"
            if 2.2 <= time_sec <= 3.0:
                name_map[16] = "Valverde"
            if time_sec >= 3.0:
                name_map[17] = "Valverde"
            if time_sec >= 3.5:
                name_map[20] = "Van Dijk"
                red_ids.add(16)
                name_map[16] = "Fabinho"
            for track_id, player in player_dict.items():
                if track_id in exclude_ids:
                    continue
                if track_id in yellow_ids:
                    frame = self.draw_ellipse(frame, player["bbox"], (0, 255, 255), label=None, track_id=track_id)
                else:
                    color = (0, 0, 255) if track_id in red_ids else \
                            (255, 255, 255) if track_id in white_ids else \
                            (0, 255, 255) if track_id in yellow_ids else \
                            (200, 200, 200)
                    label = name_map.get(track_id, f"ID: {track_id}")
                    frame = self.draw_ellipse(frame, player["bbox"], color, label, track_id)
                if player.get('has_ball', False):
                    frame = self.draw_traingle(frame, player["bbox"], (0, 0, 255))
            for track_id, referee in referee_dict.items():
                if track_id in referee_exclude_ids:
                    continue
                frame = self.draw_ellipse(frame, referee["bbox"], (0, 255, 255), label=None, track_id=track_id)
            for _, ball in ball_dict.items():
                if frame_num not in skip_ball_triangle_frames:
                    frame = self.draw_traingle(frame, ball["bbox"], (0, 255, 0))
            output_video_frames.append(frame)
        return output_video_frames
