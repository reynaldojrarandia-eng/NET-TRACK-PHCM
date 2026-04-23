import streamlit as st

def apply_custom_design():
    st.markdown("""
    <style>
        /* 1. Base Adaptive Theme */
        .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
        }

        /* 2. THE FIX: Force Metrics to have the same fixed height */
        div[data-testid="stMetric"] {
            background-color: rgba(151, 166, 195, 0.1) !important;
            border: 1px solid rgba(151, 166, 195, 0.2) !important;
            border-radius: 10px !important;
            padding: 15px !important;
            
            /* Forces all cards to match the height of the tallest one */
            min-height: 150px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }

        /* 3. Title Gradient */
        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* 4. Tab Styling */
        button[data-baseweb="tab"] {
            font-size: 16px !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header(title="PERPY: CORE", subtitle="Multi-Subject Adaptive Intelligence"):
    st.markdown(f'<h1 class="main-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: gray; opacity: 0.8; font-size: 1.1rem; margin-bottom: 2rem;">{subtitle}</p>', unsafe_allow_html=True)