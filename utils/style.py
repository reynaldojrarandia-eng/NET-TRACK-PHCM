import streamlit as st

def apply_custom_design():
    st.markdown("""
    <style>
        /* 1. Base Theme Overrides */
        .stApp {
            background-color: #0b0e14;
            color: #e6edf3;
        }

        /* 2. Unified Card Design (Metrics & Containers) */
        div[data-testid="stMetric"], .stChatMessage, div[data-testid="stExpander"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 10px !important;
            padding: 15px !important;
        }

        /* 3. High-Contrast Headers */
        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -1px;
            background: linear-gradient(90deg, #58a6ff, #bc8cff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        /* 4. Sleek Buttons */
        div.stButton > button {
            background-color: #238636; /* Success Green */
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            width: 100%;
        }

        div.stButton > button:hover {
            background-color: #2ea043;
            border: none;
            color: white;
        }

        /* 5. Custom Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0d1117 !important;
            border-right: 1px solid #30363d;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header(title="PERPY: CORE", subtitle="Multi-Subject Adaptive Intelligence"):
    st.markdown(f'<h1 class="main-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #8b949e; font-size: 1.1rem; margin-bottom: 2rem;">{subtitle}</p>', unsafe_allow_html=True)