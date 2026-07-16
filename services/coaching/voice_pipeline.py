import time
import streamlit as st


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    def _find_form_issue(self, exercise, metrics):
        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)
            
            if depth == "TOO HIGH":
                return "The user's squat is not deep enough — knees are not bending sufficiently."

            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")
            
            if alignment == "Poor Form":
                return "The user's body is not straight during the push-up."

            if hip_status == "SAGGING":
                return "The user's hips are sagging down during the push-up."

            if hip_status == "PIKED UP":
                return "The user's hips are too high — lower them to form a straight line."

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")
            
            if swing == "SWINGING":
                return "The user is swinging their torso during the curl — keep the body still."

            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from their side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            extension = metrics.get("extension_status", "")
            
            if back_arch == "Excessive Arch":
                return "The user is arching their lower back excessively during the press."

            if back_arch == "Slight Arch":
                return "Slight back arch detected — encourage the user to brace their core."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")
            
            if balance == "OFF BALANCE":
                return "The user is losing balance during the lunge — feet should be hip-width apart."

        elif exercise == "Deadlifts":
            form_status = metrics.get("form_status", "")

            if form_status == "TOO MUCH KNEE BEND":
                return "The user is bending their knees too much — this is turning into a squat instead of a hip hinge."

            if form_status == "INCOMPLETE LOCKOUT":
                return "The user is not fully locking out their hips and knees at the top of the deadlift."

        elif exercise == "Lateral Raises":
            elbow_status = metrics.get("elbow_status", "")
            symmetry_status = metrics.get("symmetry_status", "")

            if elbow_status == "TOO BENT":
                return "The user's elbows are bending too much during the lateral raise — arms should stay nearly straight."

            if symmetry_status == "UNEVEN":
                return "The user is raising one arm higher than the other — encourage even, controlled movement on both sides."

        elif exercise == "Jumping Jacks":
            sync_status = metrics.get("sync_status", "")

            if sync_status == "OUT OF SYNC":
                return "The user's arms and legs are not moving together during the jumping jack."

        elif exercise == "Mountain Climbers":
            hip_status = metrics.get("hip_status", "")

            if hip_status == "SAGGING":
                return "The user's hips are sagging during mountain climbers — encourage them to engage their core."

            if hip_status == "PIKED UP":
                return "The user's hips are too high during mountain climbers — lower into a straight plank line."

        elif exercise == "Glute Bridges":
            knee_status = metrics.get("knee_status", "")

            if knee_status == "KNEES CAVING IN":
                return "The user's knees are caving inward during the glute bridge — push them out in line with the hips."

        elif exercise == "Leg Raises":
            knee_status = metrics.get("knee_status", "")

            if knee_status == "KEEP LEGS STRAIGHT":
                return "The user is bending their knees during the leg raise — keep the legs straight throughout."

        elif exercise == "Front Raises":
            elbow_status = metrics.get("elbow_status", "")
            symmetry_status = metrics.get("symmetry_status", "")

            if elbow_status == "TOO BENT":
                return "The user's elbows are bending too much during the front raise — arms should stay nearly straight."

            if symmetry_status == "UNEVEN":
                return "The user is raising one arm higher than the other during the front raise."

        elif exercise == "Standing Calf Raises":
            knee_status = metrics.get("knee_status", "")
            symmetry_status = metrics.get("symmetry_status", "")

            if knee_status == "KNEES BENT - KEEP LEGS STRAIGHT":
                return "The user is bending their knees during the calf raise — legs should stay straight."

            if symmetry_status == "UNEVEN":
                return "The user is raising one heel higher than the other — encourage an even lift on both sides."

        elif exercise == "Overhead Tricep Extension":
            elbow_status = metrics.get("elbow_status", "")

            if elbow_status == "ELBOW FLARING":
                return "The user's elbow is flaring outward during the tricep extension — keep it pointed forward, close to the head."

        elif exercise == "Bent-over Rows":
            hinge_status = metrics.get("hinge_status", "")

            if hinge_status == "STAND UP - STAY HINGED":
                return "The user is standing too upright during the row — stay hinged forward at the hips."

        elif exercise == "Triceps Pushdown":
            elbow_status = metrics.get("elbow_status", "")

            if elbow_status == "ELBOW DRIFTING":
                return "The user's elbows are drifting away from their sides during the pushdown — keep them pinned in place."

        elif exercise == "Chest Press Machine":
            torso_status = metrics.get("torso_status", "")

            if torso_status == "LEANING FORWARD - KEEP BACK ON PAD":
                return "The user is leaning forward off the pad during the chest press — keep the back flat against it."

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)

        now = time.time()

        is_major_issue = event in ["workout_started", "set_completed", "workout_completed"]

        if not is_major_issue:
            if not issue:
                return None
            
            if now - self.last_spoken_at < 5:
                return None
            
        text = self.llm.give_feedback(event, issue)
        voice = self.tts.speak(text)

        self.last_spoken_at = now

        return voice, text
    

def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return
    
    st.markdown("<style>[data-testid='stAudio'] {display: none;}</style>", unsafe_allow_html=True)
    
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)