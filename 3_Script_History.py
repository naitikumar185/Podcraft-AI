import time
import streamlit as st

from core import auth, models

st.set_page_config(page_title="Script History", page_icon="📚", layout="wide")
auth.require_login()
user = auth.current_user()

st.title("📚 Script History")

CATEGORIES = ["All", "Technology", "Business", "Education", "Health & Wellness",
              "Entertainment", "News & Politics", "True Crime", "Comedy", "Other"]

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search = st.text_input("Search by title or topic", placeholder="Search...")
with col2:
    category = st.selectbox("Category", CATEGORIES)
with col3:
    sort = st.selectbox("Sort", ["newest", "oldest"], format_func=lambda x: x.capitalize())

scripts = models.get_scripts_for_user(user["id"], search=search, category=category, sort=sort)

if not scripts:
    st.info("No scripts found. Try adjusting your filters, or generate a new script.")
    st.stop()

st.caption(f"{len(scripts)} script(s) found")

for s in scripts:
    with st.expander(f"**{s['title'] or 'Untitled'}** — {s['topic']}  ·  {s['created_at'][:16]}"):
        st.caption(f"Category: {s['category']} · Duration: {s['duration']} min · Speakers: {s['num_speakers']} · Tone: {s['tone']}")

        edit_key = f"editing_{s['id']}"
        editing = st.session_state.get(edit_key, False)

        if editing:
            new_title = st.text_input("Title", value=s["title"] or "", key=f"title_{s['id']}")
            new_content = st.text_area("Script Content", value=s["content"], height=400, key=f"content_{s['id']}")
            save_col, cancel_col = st.columns(2)
            with save_col:
                if st.button("💾 Save Changes", key=f"save_{s['id']}", use_container_width=True):
                    models.update_script(s["id"], user["id"], new_title, new_content)
                    st.session_state[edit_key] = False
                    st.success("Script updated.")
                    st.rerun()
            with cancel_col:
                if st.button("Cancel", key=f"cancel_{s['id']}", use_container_width=True):
                    st.session_state[edit_key] = False
                    st.rerun()
        else:
            st.markdown(s["content"])

            btn_edit, btn_copy, btn_download, btn_delete = st.columns(4)
            with btn_edit:
                if st.button("✏️ Edit", key=f"edit_{s['id']}", use_container_width=True):
                    st.session_state[edit_key] = True
                    st.rerun()
            with btn_copy:
                st.code(s["content"], language=None)  # provides Streamlit's built-in copy icon
            with btn_download:
                st.download_button(
                    "⬇️ Download", data=s["content"],
                    file_name=f"{(s['title'] or 'script').replace(' ', '_')}_{int(time.time())}.md",
                    mime="text/markdown", key=f"dl_{s['id']}", use_container_width=True,
                )
            with btn_delete:
                confirm_key = f"confirm_delete_{s['id']}"
                if not st.session_state.get(confirm_key, False):
                    if st.button("🗑️ Delete", key=f"del_{s['id']}", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("Delete this script permanently?")
                    yes_col, no_col = st.columns(2)
                    with yes_col:
                        if st.button("Yes, delete", key=f"confirm_yes_{s['id']}", use_container_width=True):
                            models.delete_script(s["id"], user["id"])
                            st.session_state[confirm_key] = False
                            st.rerun()
                    with no_col:
                        if st.button("Cancel", key=f"confirm_no_{s['id']}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()
