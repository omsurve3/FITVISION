import streamlit as st
import os
import time
import pandas as pd
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# VISUAL-ONLY EXTRAS
# Additive CSS + markup helpers. None of this touches
# session_state, callbacks, auth, WebRTC, or DB logic.
# =========================================================

def render_status_badge(workout_started: bool) -> None:
    """Purely presentational status pill. Reads workout_started, changes nothing."""
    if workout_started:
        st.markdown(
            '<div class="fv-status-badge fv-status-live">'
            '<span class="fv-status-dot"></span>SESSION LIVE</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="fv-status-badge fv-status-idle">'
            '<span class="fv-status-dot"></span>STANDING BY</div>',
            unsafe_allow_html=True,
        )


def render_section_label(text: str, accent: str = "") -> None:
    if accent:
        st.markdown(
            f'<div class="fv-section-label">{text}<span class="fv-accent">{accent}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div class="fv-section-label">{text}</div>', unsafe_allow_html=True)


def render_section_heading(icon: str, title: str, subtitle: str = "") -> None:
    """Full section header: icon + title + optional subtitle + trailing rule."""
    subtitle_html = f'<p class="fv-section-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="fv-section-heading">
            <div class="fv-section-title">{icon} {title}</div>
            {subtitle_html}
            <div class="fv-section-rule"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="FITVISION",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()
    # print("MAIN EXECUTED")

    if not render_login_wall():
        # print("LOGIN WALL RETURNED FALSE")
        return 

    initial_session_defaults()
    

    if "voice_pipeline" not in st.session_state:
        try:
            api_key = os.environ.get("GROQ_API_KEY", "")

            if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
                
            print("GROQ KEY FOUND:", bool(api_key))
            print("API KEY LENGTH:", len(api_key))
            groq_client = Groq(api_key=api_key)
            
            llm_coach = LLMCoach(groq_client)
            tts = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
        except Exception as e:
            # print("VOICE PIPELINE ERROR:", e)
            import traceback
            # traceback.print_exc()
            st.session_state.voice_pipeline = None

    workout_started = st.session_state.get("workout_started", False)
    
    with st.sidebar:
        st.markdown(
            '<div class="fv-sidebar-brand">'
            '<span class="fv-sidebar-brand-icon">🏋️</span>'
            'FITVISION <span class="fv-brand-tag">Coach</span></div>',
            unsafe_allow_html=True,
        )

        if st.session_state.username:
            st.markdown(
                f'<div class="fv-sidebar-user">👤 Logged in as {st.session_state.username}</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        st.markdown(
            '<div class="fv-sidebar-section-title">⚡ Workout Setup</div>',
            unsafe_allow_html=True,
        )

        sidebar_card = st.container(border=True)

        if not workout_started:
            with sidebar_card:
                plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

                plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)

                plan_reps = st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)

                st.markdown("")

                start_session_button = st.button("▶  Start Workout", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )
                    
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            with sidebar_card:
                st.markdown(
                    f'<div class="fv-active-chip">🏋️ <b>{exercise}</b><br>{sets} Sets &nbsp;•&nbsp; {reps} Reps</div>',
                    unsafe_allow_html=True,
                )

                end_session_button = st.button("⏹  End Workout", key="end_session_button", width="stretch")

            if end_session_button:
                st.session_state.workout_started = False
                
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()

        if workout_started:
            st.divider()

            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets")

            render_section_label("📊 Progress")

            st.metric("🔥 Total Reps", f"{total_reps}")
            st.metric("🔁 Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("✅ Sets Completed", f"{sets_completed} / {target_sets}")

            st.divider()

            if exercise == "Squats":
                render_section_label("📐 Squat Analysis")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            elif exercise == "Push-ups":
                render_section_label("📐 Push-up Analysis")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Biceps Curls (Dumbbell)":
                render_section_label("📐 Curl Analysis")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                render_section_label("📐 Shoulder Press Analysis")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                render_section_label("📐 Lunge Analysis")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)

    st.markdown(
        """
        <div class="fv-hero">
            <div class="fv-hero-badge">⚡ AI-Powered Personal Gym Trainer</div>
            <div class="fv-hero-top">
                <div class="fv-hero-icon">🏋️</div>
                <div>
                    <h1 class="fv-hero-title">FitVision AI Coach</h1>
                    <p class="fv-hero-sub">
                        Real-time posture analysis, rep counting and voice
                        coaching using computer vision.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_status_badge(workout_started)
 
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown(
            f"""
            <div class="fv-coach-callout">
                <div class="fv-coach-label">🤖 AI Coach</div>
                {st.session_state.coach_feedback}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not workout_started:
        st.markdown(
            """
            <div class="fv-empty-state">
                <div class="fv-empty-icon">🎥</div>
                <div class="fv-empty-kicker">Camera Preview</div>
                <h2>Waiting for workout...</h2>
                <p>
                    Choose your exercise, sets and reps in the sidebar,<br>
                    then activate the camera and AI coach.
                </p>
                <div class="fv-empty-steps">
                    <div class="fv-empty-step"><b>1.</b> Choose workout from sidebar</div>
                    <div class="fv-empty-step"><b>2.</b> Press <b>Start Workout</b></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        render_section_heading("🎥", "Live Camera", "AI Posture Analysis")
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=False
        )

        sync_metrics_update(context)

        # if context.state.playing:
        #     time.sleep(0.25)
        #     st.rerun()

        inject_webrtc_styles()

    st.divider()

    render_section_heading("📊", "Workout History", "Review previous sessions")

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": row['time'],
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            agg_df = df.groupby(["Exercise", "Date"]).agg({
                "Reps": 'sum',
                "Sets": "sum",
                "Time (sec)": "sum"
            }).reset_index()
            agg_df.index += 1
            st.table(agg_df, border="horizontal")
            st.markdown(
                '<div class="fv-footer-note">Totals aggregated per exercise, per day</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="fv-empty-state fv-empty-state-compact">
                    <div class="fv-empty-icon">📁</div>
                    <h2>No workouts yet</h2>
                    <p>Complete your first workout to build your history.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()