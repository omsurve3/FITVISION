from core.base_exercise import BaseExercise


class JumpingJackDetector(BaseExercise):
    """
    Jumping jacks don't reduce to a single joint angle like the other
    exercises, so this tracks two independent signals - arms overhead
    (wrist above shoulder) and leg spread (ankle distance relative to hip
    width) - and combines them into one open/closed state machine.
    """

    LEG_SPREAD_OPEN = 1.6
    LEG_SPREAD_CLOSED = 1.2
    MIN_VISIBILITY = 0.7

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        key_indices = [
            self.LEFT_SHOULDER, self.RIGHT_SHOULDER,
            self.LEFT_WRIST, self.RIGHT_WRIST,
            self.LEFT_HIP, self.RIGHT_HIP,
            self.LEFT_ANKLE, self.RIGHT_ANKLE,
        ]

        key_landmarks_visible = all(landmarks[i].visibility > self.MIN_VISIBILITY for i in key_indices)

        arms_up = landmarks[self.LEFT_WRIST].y < landmarks[self.LEFT_SHOULDER].y and landmarks[self.RIGHT_WRIST].y < landmarks[self.RIGHT_SHOULDER].y

        hip_width = abs(landmarks[self.LEFT_HIP].x - landmarks[self.RIGHT_HIP].x)
        ankle_spread = abs(landmarks[self.LEFT_ANKLE].x - landmarks[self.RIGHT_ANKLE].x)
        spread_ratio = ankle_spread / hip_width if hip_width > 0 else 0.0

        legs_apart = spread_ratio >= self.LEG_SPREAD_OPEN
        legs_together = spread_ratio <= self.LEG_SPREAD_CLOSED

        if key_landmarks_visible:
            if arms_up and legs_apart:
                self.stage = "open"

            if not arms_up and legs_together and self.stage == "open":
                self.stage = "closed"
                self.reps += 1

        sync_status = "SYNCED" if arms_up == legs_apart else "OUT OF SYNC"

        return {
            "reps": self.reps,
            "spread_ratio": round(spread_ratio, 2),
            "arm_position": "UP" if arms_up else "DOWN",
            "sync_status": sync_status,
        }