from core.base_exercise import BaseExercise


class MountainClimberDetector(BaseExercise):
    """
    Tracks both hip angles (shoulder-hip-knee) each frame. Whichever leg is
    currently being driven toward the chest has the smaller hip angle, so
    that value drives rep counting; the other (planted) leg's angle is used
    for the plank hip-sag check.
    """

    DRIVE_THRESHOLD = 100
    EXTEND_THRESHOLD = 160
    MIN_VISIBILITY = 0.7
    HIP_SAG_TOLERANCE = 0.08

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    LEFT_KNEE = 25
    LEFT_ANKLE = 27
    RIGHT_HIP = 24
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        left_hip_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_SHOULDER),
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_KNEE),
        )

        right_hip_angle = self.calculate_angle(
            self.get_point(landmarks, self.RIGHT_SHOULDER),
            self.get_point(landmarks, self.RIGHT_HIP),
            self.get_point(landmarks, self.RIGHT_KNEE),
        )

        key_landmarks_visible = landmarks[self.LEFT_HIP].visibility > self.MIN_VISIBILITY and landmarks[self.RIGHT_HIP].visibility > self.MIN_VISIBILITY and landmarks[self.LEFT_KNEE].visibility > self.MIN_VISIBILITY and landmarks[self.RIGHT_KNEE].visibility > self.MIN_VISIBILITY

        active_hip_angle = min(left_hip_angle, right_hip_angle)
        plank_hip_angle = max(left_hip_angle, right_hip_angle)

        if key_landmarks_visible:
            if active_hip_angle < self.DRIVE_THRESHOLD:
                self.stage = "driven"

            if active_hip_angle > self.EXTEND_THRESHOLD and self.stage == "driven":
                self.stage = "extended"
                self.reps += 1

        planted_is_left = left_hip_angle >= right_hip_angle
        plank_shoulder_idx = self.LEFT_SHOULDER if planted_is_left else self.RIGHT_SHOULDER
        plank_hip_idx = self.LEFT_HIP if planted_is_left else self.RIGHT_HIP
        plank_ankle_idx = self.LEFT_ANKLE if planted_is_left else self.RIGHT_ANKLE

        shoulder_y = landmarks[plank_shoulder_idx].y
        ankle_y = landmarks[plank_ankle_idx].y
        hip_y = landmarks[plank_hip_idx].y
        expected_hip_y = (shoulder_y + ankle_y) / 2
        hip_deviation = hip_y - expected_hip_y

        if abs(hip_deviation) <= self.HIP_SAG_TOLERANCE:
            hip_status = "LEVEL"
        elif hip_deviation > self.HIP_SAG_TOLERANCE:
            hip_status = "SAGGING"
        else:
            hip_status = "PIKED UP"

        return {
            "reps": self.reps,
            "active_knee_angle": int(active_hip_angle),
            "plank_hip_angle": int(plank_hip_angle),
            "hip_status": hip_status,
        }