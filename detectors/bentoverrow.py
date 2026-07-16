import math
from core.base_exercise import BaseExercise


class BentOverRowDetector(BaseExercise):
    UP_THRESHOLD = 90
    DOWN_THRESHOLD = 150
    MIN_VISIBILITY = 0.7
    MIN_HINGE_ANGLE = 30

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        left_vis = landmarks[self.LEFT_ELBOW].visibility
        right_vis = landmarks[self.RIGHT_ELBOW].visibility

        if left_vis >= right_vis:
            shoulder_idx, elbow_idx, wrist_idx = self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_WRIST
        else:
            shoulder_idx, elbow_idx, wrist_idx = self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx),
        )

        key_landmarks_visible = landmarks[shoulder_idx].visibility > self.MIN_VISIBILITY and landmarks[elbow_idx].visibility > self.MIN_VISIBILITY and landmarks[wrist_idx].visibility > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if elbow_angle < self.UP_THRESHOLD:
                self.stage = "up"

            if elbow_angle > self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

        shoulder_mid_x = (landmarks[self.LEFT_SHOULDER].x + landmarks[self.RIGHT_SHOULDER].x) / 2
        shoulder_mid_y = (landmarks[self.LEFT_SHOULDER].y + landmarks[self.RIGHT_SHOULDER].y) / 2
        hip_mid_x = (landmarks[self.LEFT_HIP].x + landmarks[self.RIGHT_HIP].x) / 2
        hip_mid_y = (landmarks[self.LEFT_HIP].y + landmarks[self.RIGHT_HIP].y) / 2

        dx = shoulder_mid_x - hip_mid_x
        dy = shoulder_mid_y - hip_mid_y
        torso_angle_from_vertical = math.degrees(math.atan2(abs(dx), abs(dy))) if dy != 0 else 0.0

        hinge_status = "STAND UP - STAY HINGED" if torso_angle_from_vertical < self.MIN_HINGE_ANGLE else "HINGE OK"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "hinge_status": hinge_status,
        }