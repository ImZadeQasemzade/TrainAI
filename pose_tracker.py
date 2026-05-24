import cv2
import mediapipe as mp
import numpy as np
from collections import deque

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class PoseTracker:
    def __init__(self):
        self.pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # Rep counters
        self.reps_left = 0
        self.reps_right = 0
        
        # States for up/down
        self.stage_left = None
        self.stage_right = None
        
        # For auto-detection (rolling window of angles)
        self.angle_history = {
            'left_elbow': deque(maxlen=30),
            'right_elbow': deque(maxlen=30),
            'left_knee': deque(maxlen=30),
            'right_knee': deque(maxlen=30),
            'left_shoulder': deque(maxlen=30),
            'right_shoulder': deque(maxlen=30)
        }
        
        self.detected_workout = "Unknown"
        
    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
            
        return angle
        
    def auto_detect(self):
        # Heuristics based on angle variance
        variances = {k: np.var(list(v)) if len(v) == 30 else 0 for k, v in self.angle_history.items()}
        
        # Check if we have enough data
        if any(len(v) < 30 for v in self.angle_history.values()):
            return "Auto-Detecting..."
            
        max_var_joint = max(variances, key=variances.get)
        max_var = variances[max_var_joint]
        
        if max_var < 50:
            return "Standing/Resting"
            
        if 'knee' in max_var_joint:
            return "Squat"
        elif 'elbow' in max_var_joint:
            # Could be bicep curl or push up. For now, just say Bicep Curl
            return "Bicep Curl"
        elif 'shoulder' in max_var_joint:
            return "Lateral Raise"
            
        return "Unknown"

    def process_frame(self, frame, workout_type):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = self.pose.process(image)
        
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Get coordinates
            l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            
            r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            
            l_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            l_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            l_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            
            r_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            r_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
            r_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
            
            # Calculate angles
            angle_l_elbow = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
            angle_r_elbow = self.calculate_angle(r_shoulder, r_elbow, r_wrist)
            
            angle_l_knee = self.calculate_angle(l_hip, l_knee, l_ankle)
            angle_r_knee = self.calculate_angle(r_hip, r_knee, r_ankle)
            
            angle_l_shoulder = self.calculate_angle(l_hip, l_shoulder, l_elbow)
            angle_r_shoulder = self.calculate_angle(r_hip, r_shoulder, r_elbow)
            
            # Update history
            self.angle_history['left_elbow'].append(angle_l_elbow)
            self.angle_history['right_elbow'].append(angle_r_elbow)
            self.angle_history['left_knee'].append(angle_l_knee)
            self.angle_history['right_knee'].append(angle_r_knee)
            self.angle_history['left_shoulder'].append(angle_l_shoulder)
            self.angle_history['right_shoulder'].append(angle_r_shoulder)
            
            if workout_type == "Auto-Detect":
                self.detected_workout = self.auto_detect()
                workout_to_track = self.detected_workout
            else:
                workout_to_track = workout_type
                
            # Logic for Specific Workouts
            if workout_to_track in ["Bicep Curl", "One arm curls", "Cable Bicep Curl", "Cable Hammer Curl"]:
                # Left
                if angle_l_elbow > 150: self.stage_left = "down"
                if angle_l_elbow < 45 and self.stage_left == 'down':
                    self.stage_left = "up"
                    self.reps_left += 1
                # Right
                if angle_r_elbow > 150: self.stage_right = "down"
                if angle_r_elbow < 45 and self.stage_right == 'down':
                    self.stage_right = "up"
                    self.reps_right += 1
                    
            elif workout_to_track in ["Squat", "Squats", "Jumping Squat", "Adv shrimp squat", "Archer squat", "Step up"]:
                # Track knee
                if angle_l_knee > 160: self.stage_left = "up"
                if angle_l_knee < 100 and self.stage_left == 'up':
                    self.stage_left = "down"
                    self.reps_left += 1
                    self.reps_right += 1 # Same for squats
                    
            elif workout_to_track in ["Lateral Raise"]:
                if angle_l_shoulder < 40: self.stage_left = "down"
                if angle_l_shoulder > 80 and self.stage_left == 'down':
                    self.stage_left = "up"
                    self.reps_left += 1
                if angle_r_shoulder < 40: self.stage_right = "down"
                if angle_r_shoulder > 80 and self.stage_right == 'down':
                    self.stage_right = "up"
                    self.reps_right += 1
            
            elif workout_to_track in ["Push-up", "Scapula push up", "Diamond push up", "Archer push up", "Ring push up", "One arm push up", "Dumbbell Bench Press", "Incline Dumbbell Press", "Standing Dumbbell Overhead Press", "Cable Shoulder Press", "Dip", "Wall hand stand push up"]:
                # Pressing movements (elbow)
                if angle_l_elbow > 150: self.stage_left = "up"
                if angle_l_elbow < 90 and self.stage_left == 'up':
                    self.stage_left = "down"
                    self.reps_left += 1
                if angle_r_elbow > 150: self.stage_right = "up"
                if angle_r_elbow < 90 and self.stage_right == 'up':
                    self.stage_right = "down"
                    self.reps_right += 1 # Only one for pushup, but we separate left/right for dumbbells

            elif workout_to_track in ["Pull up", "Chin up", "Cable Lat Pulldown", "Weighted Pull-Up", "Scapula pull up", "One arm row", "Cable Row", "Seated Cable Face Pull"]:
                # Pulling movements (elbow/shoulder)
                if angle_l_elbow > 150: self.stage_left = "down"
                if angle_l_elbow < 90 and self.stage_left == 'down':
                    self.stage_left = "up"
                    self.reps_left += 1
                if angle_r_elbow > 150: self.stage_right = "down"
                if angle_r_elbow < 90 and self.stage_right == 'down':
                    self.stage_right = "up"
                    self.reps_right += 1

            # Draw landmarks
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
        return image, self.detected_workout, self.reps_left, self.reps_right
        
    def reset_counters(self):
        self.reps_left = 0
        self.reps_right = 0
        self.stage_left = None
        self.stage_right = None
        for k in self.angle_history:
            self.angle_history[k].clear()
