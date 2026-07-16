from core.base_exercise import BaseExercise


class CalfRaiseDetector(BaseExercise):
    UP_THRESHOLD = 160
    DOWN_THRESHOLD = 110
    MIN_VISIBILITY = 0.7
    KNEE_LOCK_TOLERANCE = 165
    SYMMETRY_TOLERANCE = 15

    LEFT_HIP = 23
    LEFT_KNEE = 25
    LEFT_ANKLE = 27
    LEFT_FOOT_INDEX = 31
    RIGHT_HIP = 24
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28
    RIGHT_FOOT_INDEX = 32

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        left_visible = landmarks[self.LEFT_KNEE].visibility > self.MIN_VISIBILITY and landmarks[self.LEFT_ANKLE].visibility > self.MIN_VISIBILITY and landmarks[self.LEFT_FOOT_INDEX].visibility > self.MIN_VISIBILITY
        right_visible = landmarks[self.RIGHT_KNEE].visibility > self.MIN_VISIBILITY and landmarks[self.RIGHT_ANKLE].visibility > self.MIN_VISIBILITY and landmarks[self.RIGHT_FOOT_INDEX].visibility > self.MIN_VISIBILITY

        left_ankle_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_KNEE),
            self.get_point(landmarks, self.LEFT_ANKLE),
            self.get_point(landmarks, self.LEFT_FOOT_INDEX),
        ) if left_visible else None

        right_ankle_angle = self.calculate_angle(
            self.get_point(landmarks, self.RIGHT_KNEE),
            self.get_point(landmarks, self.RIGHT_ANKLE),
            self.get_point(landmarks, self.RIGHT_FOOT_INDEX),
        ) if right_visible else None

        angles = [a for a in (left_ankle_angle, right_ankle_angle) if a is not None]

        if not angles:
            return {
                "reps": self.reps,
                "ankle_angle": 0,
                "knee_status": "N/A",
                "symmetry_status": "N/A",
            }

        avg_ankle_angle = sum(angles) / len(angles)

        if avg_ankle_angle > self.UP_THRESHOLD:
            self.stage = "up"

        if avg_ankle_angle < self.DOWN_THRESHOLD and self.stage == "up":
            self.stage = "down"
            self.reps += 1

        knee_status = "LOCKED"

        if left_visible and landmarks[self.LEFT_HIP].visibility > self.MIN_VISIBILITY:
            left_knee_angle = self.calculate_angle(
                self.get_point(landmarks, self.LEFT_HIP),
                self.get_point(landmarks, self.LEFT_KNEE),
                self.get_point(landmarks, self.LEFT_ANKLE),
            )
            if left_knee_angle < self.KNEE_LOCK_TOLERANCE:
                knee_status = "KNEES BENT - KEEP LEGS STRAIGHT"

        if right_visible and landmarks[self.RIGHT_HIP].visibility > self.MIN_VISIBILITY:
            right_knee_angle = self.calculate_angle(
                self.get_point(landmarks, self.RIGHT_HIP),
                self.get_point(landmarks, self.RIGHT_KNEE),
                self.get_point(landmarks, self.RIGHT_ANKLE),
            )
            if right_knee_angle < self.KNEE_LOCK_TOLERANCE:
                knee_status = "KNEES BENT - KEEP LEGS STRAIGHT"

        if left_ankle_angle is not None and right_ankle_angle is not None:
            symmetry_status = "EVEN" if abs(left_ankle_angle - right_ankle_angle) <= self.SYMMETRY_TOLERANCE else "UNEVEN"
        else:
            symmetry_status = "N/A"

        return {
            "reps": self.reps,
            "ankle_angle": int(avg_ankle_angle),
            "knee_status": knee_status,
            "symmetry_status": symmetry_status,
        }