from core.base_exercise import BaseExercise


class DeadliftDetector(BaseExercise):
    UP_THRESHOLD = 160
    DOWN_THRESHOLD = 90
    MIN_VISIBILITY = 0.7
    KNEE_BEND_TOLERANCE = 140
    LOCKOUT_TOLERANCE = 165

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
            shoulder_idx = self.LEFT_SHOULDER
            hip_idx = self.LEFT_HIP
            knee_idx = self.LEFT_KNEE
            ankle_idx = self.LEFT_ANKLE
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            hip_idx = self.RIGHT_HIP
            knee_idx = self.RIGHT_KNEE
            ankle_idx = self.RIGHT_ANKLE

        # Hip hinge angle drives rep counting - a deadlift is a hip hinge,
        # not a knee-dominant squat.
        hip_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
        )

        knee_angle = self.calculate_angle(
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
            self.get_point(landmarks, ankle_idx),
        )

        key_landmarks_visible = landmarks[shoulder_idx].visibility > self.MIN_VISIBILITY and landmarks[hip_idx].visibility > self.MIN_VISIBILITY and landmarks[knee_idx].visibility > self.MIN_VISIBILITY and landmarks[ankle_idx].visibility > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if hip_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if hip_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        if self.stage == "down" and knee_angle < self.KNEE_BEND_TOLERANCE:
            form_status = "TOO MUCH KNEE BEND"
        elif self.stage == "up" and knee_angle < self.LOCKOUT_TOLERANCE:
            form_status = "INCOMPLETE LOCKOUT"
        elif self.stage == "up":
            form_status = "LOCKED OUT"
        else:
            form_status = "HINGING"

        return {
            "reps": self.reps,
            "hip_angle": int(hip_angle),
            "knee_angle": int(knee_angle),
            "form_status": form_status,
        }