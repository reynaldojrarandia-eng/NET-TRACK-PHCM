import streamlit as st

def apply_custom_design():
    st.markdown("""
    <style>
        /* Use Streamlit Variables to support Light/Dark mode */
        .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
        }

        /* Metric Cards & Expanders */
        div[data-testid="stMetric"], .stChatMessage, div[data-testid="stExpander"] {
            background-color: rgba(151, 166, 195, 0.1) !important;
            border: 1px solid rgba(151, 166, 195, 0.2) !important;
            border-radius: 10px !important;
            backdrop-filter: blur(10px);
        }

        /* Title Gradient (Works on both modes) */
        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Fix Tabs to look like your reference image */
        button[data-baseweb="tab"] {
            font-size: 18px !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header(title="PERPY: CORE", subtitle="Multi-Subject Adaptive Intelligence"):
    st.markdown(f'<h1 class="main-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: gray; opacity: 0.8;">{subtitle}</p>', unsafe_allow_html=True)