from core.base_exercise import BaseExercise


class LegRaiseDetector(BaseExercise):
    RAISE_THRESHOLD = 100
    REST_THRESHOLD = 160
    MIN_VISIBILITY = 0.7
    STRAIGHT_LEG_TOLERANCE = 160

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
            shoulder_idx, hip_idx, knee_idx, ankle_idx = self.LEFT_SHOULDER, self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE
        else:
            shoulder_idx, hip_idx, knee_idx, ankle_idx = self.RIGHT_SHOULDER, self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE

        hip_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, ankle_idx),
        )

        knee_angle = self.calculate_angle(
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
            self.get_point(landmarks, ankle_idx),
        )

        key_landmarks_visible = landmarks[shoulder_idx].visibility > self.MIN_VISIBILITY and landmarks[hip_idx].visibility > self.MIN_VISIBILITY and landmarks[knee_idx].visibility > self.MIN_VISIBILITY and landmarks[ankle_idx].visibility > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if hip_angle < self.RAISE_THRESHOLD:
                self.stage = "raised"

            if hip_angle > self.REST_THRESHOLD and self.stage == "raised":
                self.stage = "lowered"
                self.reps += 1

        knee_status = "STRAIGHT" if knee_angle >= self.STRAIGHT_LEG_TOLERANCE else "KEEP LEGS STRAIGHT"

        return {
            "reps": self.reps,
            "hip_angle": int(hip_angle),
            "knee_status": knee_status,
        }