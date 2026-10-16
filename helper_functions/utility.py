import streamlit as st
import random
import hmac

# """
# This file contains the common components used in the Streamlit App.
# This includes the sidebar, the title, the footer, and the password check.
# """


def _credentials_valid(username, password):
    """Checks the username and password against the [users] table in secrets.toml."""
    users = st.secrets.get("users", {})
    expected_password = users.get(username)
    if expected_password is None:
        # Compare anyway so an unknown username takes the same time as a wrong password
        hmac.compare_digest(password, password)
        return False
    return hmac.compare_digest(password, expected_password)


def _logout():
    for key in ("password_correct", "username"):
        st.session_state.pop(key, None)


def check_password():
    """Returns `True` if the user is logged in, otherwise shows the login form."""
    if st.session_state.get("password_correct", False):
        with st.sidebar:
            st.markdown(f"👤 Signed in as **{st.session_state['username']}**")
            st.button("Log out", on_click=_logout, use_container_width=True)
        return True

    # Hide the page list in the sidebar until the user has logged in
    st.markdown(
        "<style>[data-testid='stSidebarNav']{display:none;}</style>",
        unsafe_allow_html=True,
    )

    _, centre, _ = st.columns([1, 2, 1])
    with centre:
        st.markdown(
            "<div style='text-align:center; padding-top:2rem;'>"
            "<div style='font-size:3rem;'>🎓</div>"
            "<h2 style='margin-bottom:0;'>Welcome back</h2>"
            "<p style='opacity:0.7;'>Sign in to find your next course</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.warning("Please enter both your username and password.")
            elif _credentials_valid(username.strip(), password):
                st.session_state["password_correct"] = True
                st.session_state["username"] = username.strip()
                st.rerun()
            else:
                st.error("😕 Incorrect username or password.")

        st.caption("Need access? Contact your administrator.")

    return False
