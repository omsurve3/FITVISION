import random
import streamlit as st
from services.persistence.exercise_repository import get_or_create_user
import base64
from pathlib import Path

def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    # Placeholder banner image — swap this for a fixed branded image/URL
    # whenever one is available. Random each load for now, as requested.
    banner_path = Path(__file__).resolve().parents[2] / "assets" / "login_banner1.png"

    with open(banner_path, "rb") as img_file:
     banner_image = base64.b64encode(img_file.read()).decode()

    st.markdown(
        f"""
        <div class="fv-login-image-col">
        <img src="data:image/png;base64,{banner_image}" alt="FitVision" />
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="fv-login-hero">
            <div class="fv-login-badge">⚡ AI-Powered Personal Gym Trainer</div>
            <div class="fv-login-icon">🏋️‍♂️</div>
            <h1 class="fv-login-title">FitVision AI Coach</h1>
            <p class="fv-login-sub">Welcome! Please enter a username to start.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        st.markdown('<div class="fv-login-field-label">Name (unique)</div>', unsafe_allow_html=True)
        username = st.text_input(
            "Name (unique)",
            placeholder="e.g. omsurve",
            label_visibility="collapsed",
        )
        submit_button = st.form_submit_button("🚀  Start Session", width="stretch")

    if submit_button:
        if not username:
            st.error("⚠️ Name cannot be empty.")
            return False
        
        user = get_or_create_user(username)
    
        st.session_state["user_id"] = user["id"]
        st.session_state["username"] = user["username"]

        st.rerun()

    return False