import streamlit as st

def apply_custom_design():
    st.markdown("""
    <style>
        /* 1. Base Adaptive Theme */
        .stApp {
            background-color: var(--background-color);
            color: var(--text-color);
        }

        /* 2. FIXED: Uniform Metric Card Sizes */
        div[data-testid="stMetric"] {
            background-color: rgba(151, 166, 195, 0.1) !important;
            border: 1px solid rgba(151, 166, 195, 0.2) !important;
            border-radius: 10px !important;
            padding: 15px !important;
            
            /* The Fix: Force equal height and spacing */
            min-height: 130px !important; 
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }

        /* 3. Header Styling */
        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* 4. Tab Styling for Horizontal Nav */
        button[data-baseweb="tab"] {
            font-size: 16px !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)