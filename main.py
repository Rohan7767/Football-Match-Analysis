from utils import read_video, save_video
from trackers import Tracker
from trackers.broadcast_tracker import BroadcastTracker
def main():
    video_path = 'input_videos/tacticam.mp4'
    video_frames = read_video(video_path)
    if "input_videos/broadcast.mp4" in video_path:
        tracker = BroadcastTracker("models/best.pt")
    else:
        tracker = Tracker("models/best.pt")
    tracks = tracker.get_object_tracks(video_frames,read_from_stub=True,stub_path='stubs/track_stubs_tacticam.pkl')
    output_video_frames = tracker.draw_annotations(video_frames, tracks)
    save_video(output_video_frames, 'output_videos/tacticam.mp4')
if __name__ == '__main__':
    main()