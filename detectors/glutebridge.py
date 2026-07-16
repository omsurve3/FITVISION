from core.base_exercise import BaseExercise


class GluteBridgeDetector(BaseExercise):
    DOWN_THRESHOLD = 140
    UP_THRESHOLD = 165
    MIN_VISIBILITY = 0.7
    KNEE_CAVE_RATIO = 0.8

    LEFT_SHOULDER = 11
    LEFT_HIP = 23
    LEFT_KNEE = 25
    LEFT_ANKLE = 27
    RIGHT_SHOULDER = 12
    RIGHT_HIP = 24
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        left_vis = landmarks[self.LEFT_HIP].visibility
        right_vis = landmarks[self.RIGHT_HIP].visibility

        if left_vis >= right_vis:
            shoulder_idx, hip_idx, knee_idx = self.LEFT_SHOULDER, self.LEFT_HIP, self.LEFT_KNEE
        else:
            shoulder_idx, hip_idx, knee_idx = self.RIGHT_SHOULDER, self.RIGHT_HIP, self.RIGHT_KNEE

        hip_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
        )

        key_landmarks_visible = landmarks[shoulder_idx].visibility > self.MIN_VISIBILITY and landmarks[hip_idx].visibility > self.MIN_VISIBILITY and landmarks[knee_idx].visibility > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if hip_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if hip_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        knee_width = abs(landmarks[self.LEFT_KNEE].x - landmarks[self.RIGHT_KNEE].x)
        ankle_width = abs(landmarks[self.LEFT_ANKLE].x - landmarks[self.RIGHT_ANKLE].x)
        knee_ratio = knee_width / ankle_width if ankle_width > 0 else 1.0

        knee_status = "KNEES CAVING IN" if knee_ratio < self.KNEE_CAVE_RATIO else "ALIGNED"

        return {
            "reps": self.reps,
            "hip_angle": int(hip_angle),
            "knee_status": knee_status,
        }