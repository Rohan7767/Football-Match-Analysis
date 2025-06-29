from ultralytics import YOLO
import supervision as sv
import pickle
import os
import numpy as np
import cv2
import sys
sys.path.append('../')
from utils import get_center_of_bbox, get_bbox_width
class Tracker:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.tracker = sv.ByteTrack()
        self.red_team_ids = {
            1: "Trent", 9: "Konate", 17: "Van Dijk", 3: "Salah",
            12: "Henderson", 16: "Fabinho", 6: "Mane", 42: "Allison",
            67: "Allison", 21: "Luis Diaz", 86: "Luis Diaz", 15: "Robertson",
            59: "Robertson", 4: "Thiago"
        }
        self.white_team_ids = {
            10: "Vinicius Jr", 11: "Benzema", 19: "Valverde", 8: "Mendy",
            5: "Kroos", 18: "Modric", 20: "Carvajal", 61: "Carvajal",
            7: "Rudiger", 2: "Militao", 14: "Casemiro"
        }
    def detect_frames(self, frames):
        batch_size = 20
        detections = []
        for i in range(0, len(frames), batch_size):
            detections_batch = self.model.predict(frames[i:i+batch_size], conf=0.1)
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
    def draw_ellipse(self, frame, bbox, color, label=None):
        y2 = int(bbox[3])
        x_center, _ = get_center_of_bbox(bbox)
        width = get_bbox_width(bbox)
        cv2.ellipse(
            frame,
            center=(x_center, y2),
            axes=(int(width), int(0.33 * width)),
            angle=0.0,
            startAngle=-45,
            endAngle=245,
            color=color,
            thickness=2,
            lineType=cv2.LINE_4
        )
        if label is not None:
            rectangle_width = 90
            rectangle_height = 20
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
                (int(x1_rect + 5), int(y1_rect + 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                2
            )
        return frame
    def draw_traingle(self, frame, bbox, color):
        y = int(bbox[1])
        x, _ = get_center_of_bbox(bbox)
        triangle_points = np.array([
            [x, y],
            [x - 10, y - 20],
            [x + 10, y - 20]
        ])
        cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
        cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)
        return frame
    def draw_annotations(self, video_frames, tracks):
        output_video_frames = []
        skip_ball_triangle_frames = {
            60, 72, 73, 75, 79, 81, 89, 127, 135, 136, 142, 143, 149, 
            150, 155, 156, 157, 158, 162, 163, 164, 184, 185, 186, 188, 189, 190
        }
        for frame_num, frame in enumerate(video_frames):
            frame = frame.copy()
            player_dict = tracks["players"][frame_num]
            ball_dict = tracks["ball"][frame_num]
            referee_dict = tracks["referees"][frame_num]
            for track_id, player in player_dict.items():
                if track_id in [77, 87, 78, 92, 71, 76, 51]:
                    continue
                if track_id in [56, 13, 23, 44]:
                    frame = self.draw_ellipse(frame, player["bbox"], (0, 255, 255))
                    continue
                if track_id in self.red_team_ids:
                    color = (0, 0, 255)
                    label = self.red_team_ids[track_id]
                elif track_id in self.white_team_ids:
                    color = (255, 255, 255)
                    if track_id == 20 and frame_num >= 100.8:
                        label = "Valverde"
                    else:
                        label = self.white_team_ids[track_id]
                else:
                    color = (128, 128, 128)
                    label = str(track_id)
                frame = self.draw_ellipse(frame, player["bbox"], color, label)
                if player.get('has_ball', False):
                    frame = self.draw_traingle(frame, player["bbox"], (0, 0, 255))
            for _, referee in referee_dict.items():
                frame = self.draw_ellipse(frame, referee["bbox"], (0, 255, 255))
            for _, ball in ball_dict.items():
                if frame_num not in skip_ball_triangle_frames:
                    frame = self.draw_traingle(frame, ball["bbox"], (0, 255, 0))
            output_video_frames.append(frame)
        return output_video_frames