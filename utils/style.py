import streamlit as st

def apply_custom_design():
    # This CSS uses variables that change based on Streamlit's Light/Dark setting
    design_css = """
    <style>
        /* 1. Global App Background */
        .stApp {
            background: var(--background-color);
            color: var(--text-color);
        }

        /* 2. Glass-morphism Cards */
        /* Works on both modes by using semi-transparent neutral tones */
        div[data-testid="stMetricValue"], .stImage, .css-1r698wo {
            background-color: rgba(150, 150, 150, 0.1) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(150, 150, 150, 0.2) !important;
            border-radius: 15px !important;
            padding: 20px !important;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1) !important;
        }

        /* 3. The Main Title Gradient */
        .main-header {
            background: linear-gradient(90deg, #11998e, #38ef7d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 20px;
        }

        /* 4. Adaptive Input Fields */
        /* Softens the bright white inputs in Dark Mode */
        div[data-baseweb="input"] {
            background-color: rgba(150, 150, 150, 0.05) !important;
            border-radius: 8px !important;
        }

        /* 5. Custom Sidebar Polish */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(150, 150, 150, 0.1);
        }
    </style>
    """
    st.markdown(design_css, unsafe_allow_html=True)