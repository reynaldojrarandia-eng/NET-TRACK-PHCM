import streamlit as st
import time

def render_auth(supabase):
    # --- SIMPLE PASSWORD RESET (Email-Based, No OTP) ---
    if st.session_state['forgot_mode']:
        _, col2, _ = st.columns([1, 1.5, 1])
        with col2:
            st.markdown('<div class="dark-panel">', unsafe_allow_html=True)
            st.header("🔑 Reset Password")
            st.caption("Enter your registered email to set a new password.")

            target_email = st.text_input("Registered Email")
            new_p = st.text_input("New Password", type="password")
            confirm_p = st.text_input("Confirm New Password", type="password")

            if st.button("Update Password", type="primary", use_container_width=True):
                if not target_email or not new_p:
                    st.error("Please fill in all fields.")
                elif new_p != confirm_p:
                    st.error("Passwords do not match!")
                else:
                    try:
                        check = supabase.table("profiles").select("email").eq("email", target_email).execute()
                        if check.data:
                            supabase.table("profiles").update({"password": new_p}).eq("email", target_email).execute()
                            st.success(f"✅ Password for {target_email} updated!")
                            time.sleep(2)
                            st.session_state['forgot_mode'] = False
                            st.rerun()
                        else:
                            st.error("🚨 Email not found in our records.")
                    except Exception as e:
                        st.error(f"Update failed: {str(e)}")

            if st.button("← Back to Login", key="cancel_reset"):
                st.session_state['forgot_mode'] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # --- LOGIN UI ---
    if not st.session_state['logged_in']:
        _, col2, _ = st.columns([1, 1.5, 1])
        with col2:
            st.markdown('<div class="dark-panel">', unsafe_allow_html=True)
            st.markdown('<h1 class="main-header">NET-TRACK Access</h1>', unsafe_allow_html=True)

            t1, t2 = st.tabs(["Login", "Register"])

            with t1:
                with st.form("login_form"):
                    u = st.text_input("Student ID or Email")
                    p = st.text_input("Password", type="password")

                    c_log, c_forgot = st.columns(2)
                    login_submitted = c_log.form_submit_button("Sign In", use_container_width=True)
                    forgot_submitted = c_forgot.form_submit_button("Forgot Password?", use_container_width=True)
                    
                    if forgot_submitted:
                        st.session_state['forgot_mode'] = True
                        st.rerun()
                        
                    if login_submitted:
                        if u and p:
                            res = supabase.table("profiles") \
                                .select("*") \
                                .or_(f"username.eq.{u},email.eq.{u}") \
                                .eq("password", p) \
                                .execute()

                            if res.data:
                                st.session_state.update({
                                    'logged_in': True,
                                    'user_role': res.data[0]['role'],
                                    'username': res.data[0]['username']
                                })
                                st.rerun()
                            else:
                                st.error("🚨 Invalid Credentials")
                        else:
                            st.warning("Please enter your credentials.")

            with t2:
                st.markdown('<br>', unsafe_allow_html=True)
                c1, c2 = st.columns([3, 1])
                f_name = c1.text_input("First Name", placeholder="Juan")
                m_i = c2.text_input("M.I.", max_chars=2, placeholder="A")

                c3, c4 = st.columns(2)
                l_name = c3.text_input("Last Name", placeholder="Cruz")
                email = c4.text_input("Email Address", placeholder="user@manila.uphsl.edu.ph")
                phone = st.text_input("Phone Number", placeholder="09123456789")
                
                new_r = st.selectbox("Registering as:", ["Student", "Teacher"])

                if new_r == "Teacher":
                    id_label = "Faculty / Employee ID"
                    dept_label = "Handling Department"
                    placeholder_id = "e.g. 2024-FAC-123"
                else:
                    id_label = "Student ID"
                    dept_label = "Enrolled Course"
                    placeholder_id = "e.g. m21-1234-567"
                    
                dept_options = ["BSCS", "BSIT", "BSBA", "BA COMM", "CIHM", "BSN", "BSOT", "BSPT", "BSRT", "BS RADTECH", "JHS", "SHS"]
                dept = st.selectbox(dept_label, dept_options)

                new_u = st.text_input(id_label, placeholder=placeholder_id)
                new_p = st.text_input("Set Password", type="password")

                auth_gate = True
                if new_r == "Teacher":
                    admin_code = st.text_input("Teacher Authorization Code", type="password")
                    if admin_code != "PHCM_ADMIN_2026":
                        auth_gate = False

                st.markdown('<br>', unsafe_allow_html=True)

                if st.button("COMPLETE REGISTRATION", use_container_width=True, type="primary"):
                    if not all([f_name, m_i, l_name, email, new_u, new_p, phone]):
                        st.error("🚨 Please complete all fields.")
                    elif not auth_gate:
                        st.error("🚨 Invalid Teacher Authorization Code.")
                    else:
                        try:
                            supabase.auth.sign_up({"email": email, "password": new_p})
                            full_name = f"{f_name} {m_i}. {l_name}".strip()
                            supabase.table("profiles").insert({
                                "username": new_u, "password": new_p, "role": new_r,
                                "full_name": full_name, "email": email, "phone": phone, "department": dept
                            }).execute()

                            if new_r == "Student":
                                supabase.table("student_analytics").insert({
                                    "student_id": new_u, "accuracy_score": 0, "status": "New"
                                }).execute()

                            st.success(f"Welcome to NET-TRACK, {f_name}!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Registration failed: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)