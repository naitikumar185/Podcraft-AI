import os
import time
import streamlit as st

from core import auth, models
from core.generator import generate_script, MODEL_OPTIONS

st.set_page_config(page_title="Generate Script", page_icon="✍️", layout="wide")
auth.require_login()
user = auth.current_user()

st.title("✍️ Generate a Podcast Script")

if user["credits"] <= 0:
    st.error("You're out of credits. Upgrade your plan to keep generating scripts.")
    if st.button("View Pricing"):
        st.switch_page("pages/4_Pricing.py")
    st.stop()

st.caption(f"You have **{user['credits']}** credits remaining on the **{user['plan']}** plan.")

with st.sidebar:
    st.subheader("AI Config")
    google_api_key = st.text_input(
        "GOOGLE_API_KEY", type="password",
        value=os.environ.get("GOOGLE_API_KEY", ""),
        help="Get a free key at https://aistudio.google.com/apikey",
    )
    model = st.selectbox("Gemini Model", options=MODEL_OPTIONS)

with st.form("generate_form"):
    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Podcast Title", placeholder="e.g. The Future of Remote Work")
        topic = st.text_input("Podcast Topic", placeholder="e.g. How AI is changing how teams collaborate remotely")
        category = st.selectbox("Genre / Category", [
            "Technology", "Business", "Education", "Health & Wellness",
            "Entertainment", "News & Politics", "True Crime", "Comedy", "Other",
        ])
        audience = st.text_input("Target Audience", placeholder="e.g. Early-career software engineers")
        language = st.selectbox("Language", ["English", "Hindi", "Hinglish"])

    with col2:
        tone = st.selectbox("Tone", ["Conversational", "Professional", "Humorous", "Inspirational", "Investigative"])
        duration = st.slider("Target Episode Length (minutes)", min_value=5, max_value=60, value=20, step=5)
        num_speakers = st.slider("Number of Speakers", min_value=1, max_value=4, value=2)
        speaker_names = st.text_input("Speaker Names (comma-separated)", placeholder="e.g. Alex, Priya")
        additional_instructions = st.text_area("Additional Instructions", placeholder="Optional — anything else the AI should know")

    submitted = st.form_submit_button("Generate Script", type="primary", use_container_width=True)

if submitted:
    if not google_api_key:
        st.error("Please provide a GOOGLE_API_KEY in the sidebar first.")
    elif not topic or not audience:
        st.error("Please fill in both the Topic and Target Audience fields.")
    else:
        with st.spinner("Writing your podcast script..."):
            try:
                script_text = generate_script(
                    api_key=google_api_key, model=model,
                    title=title, topic=topic, category=category, audience=audience,
                    tone=tone, duration=duration, num_speakers=num_speakers,
                    speaker_names=speaker_names, language=language,
                    additional_instructions=additional_instructions,
                )
            except Exception as err:
                # Generation failed: no credit is deducted, nothing is saved.
                st.error(f"Error generating script: {err}")
            else:
                # Success: save first, THEN deduct the credit.
                script_id = models.create_script(
                    user_id=user["id"], title=title, topic=topic, content=script_text,
                    category=category, duration=duration, num_speakers=num_speakers,
                    speaker_names=speaker_names, language=language, tone=tone,
                )
                models.deduct_credit(user["id"])
                auth.refresh_current_user()
                st.session_state["last_script"] = script_text
                st.session_state["last_script_id"] = script_id
                st.success("Script generated and saved to your history!")

if "last_script" in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state["last_script"])
    dl_col, hist_col = st.columns(2)
    with dl_col:
        st.download_button(
            "⬇️ Download Script (.md)",
            data=st.session_state["last_script"],
            file_name=f"podcast_script_{int(time.time())}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with hist_col:
        if st.button("📚 View in Script History", use_container_width=True):
            st.switch_page("pages/3_Script_History.py")
