from core.base_exercise import BaseExercise


class FrontRaiseDetector(BaseExercise):
    """
    Same angle math as LateralRaiseDetector (hip-shoulder-elbow), since the
    2D angle between torso and upper arm rises regardless of whether the
    arm is lifting sideways or forward. Most accurate with a side-on
    camera; front-facing works but forward arm movement can foreshorten.
    """

    UP_THRESHOLD = 80
    DOWN_THRESHOLD = 25
    MIN_VISIBILITY = 0.7
    ELBOW_BEND_TOLERANCE = 150
    SYMMETRY_TOLERANCE = 20

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    LEFT_HIP = 23
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    RIGHT_HIP = 24

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        left_visible = landmarks[self.LEFT_SHOULDER].visibility > self.MIN_VISIBILITY and landmarks[self.LEFT_ELBOW].visibility > self.MIN_VISIBILITY and landmarks[self.LEFT_WRIST].visibility > self.MIN_VISIBILITY
        right_visible = landmarks[self.RIGHT_SHOULDER].visibility > self.MIN_VISIBILITY and landmarks[self.RIGHT_ELBOW].visibility > self.MIN_VISIBILITY and landmarks[self.RIGHT_WRIST].visibility > self.MIN_VISIBILITY

        left_elevation = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_SHOULDER),
            self.get_point(landmarks, self.LEFT_ELBOW),
        ) if left_visible else None

        right_elevation = self.calculate_angle(
            self.get_point(landmarks, self.RIGHT_HIP),
            self.get_point(landmarks, self.RIGHT_SHOULDER),
            self.get_point(landmarks, self.RIGHT_ELBOW),
        ) if right_visible else None

        angles = [a for a in (left_elevation, right_elevation) if a is not None]

        if not angles:
            return {
                "reps": self.reps,
                "elevation_angle": 0,
                "elbow_status": "N/A",
                "symmetry_status": "N/A",
            }

        avg_elevation = sum(angles) / len(angles)

        if avg_elevation < self.DOWN_THRESHOLD:
            self.stage = "down"

        if avg_elevation > self.UP_THRESHOLD and self.stage == "down":
            self.stage = "up"
            self.reps += 1

        elbow_status = "STRAIGHT"

        if left_visible:
            left_elbow_angle = self.calculate_angle(
                self.get_point(landmarks, self.LEFT_SHOULDER),
                self.get_point(landmarks, self.LEFT_ELBOW),
                self.get_point(landmarks, self.LEFT_WRIST),
            )
            if left_elbow_angle < self.ELBOW_BEND_TOLERANCE:
                elbow_status = "TOO BENT"

        if right_visible:
            right_elbow_angle = self.calculate_angle(
                self.get_point(landmarks, self.RIGHT_SHOULDER),
                self.get_point(landmarks, self.RIGHT_ELBOW),
                self.get_point(landmarks, self.RIGHT_WRIST),
            )
            if right_elbow_angle < self.ELBOW_BEND_TOLERANCE:
                elbow_status = "TOO BENT"

        if left_elevation is not None and right_elevation is not None:
            symmetry_status = "EVEN" if abs(left_elevation - right_elevation) <= self.SYMMETRY_TOLERANCE else "UNEVEN"
        else:
            symmetry_status = "N/A"

        return {
            "reps": self.reps,
            "elevation_angle": int(avg_elevation),
            "elbow_status": elbow_status,
            "symmetry_status": symmetry_status,
        }