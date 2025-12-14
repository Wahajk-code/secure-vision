import streamlit as st
from PIL import Image
import os

st.set_page_config(
    page_title="SecureVision Home",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ SecureVision Final Defense System")

# Load Custom CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    load_css(os.path.join(os.path.dirname(__file__), 'style.css'))
except FileNotFoundError:
    pass

st.markdown("""
### Welcome to the SecureVision Interface

This system provides real-time monitoring and advanced analytics for public safety.

#### Modules
- **📹 Live Monitor**: Real-time video feed with AI-powered detection for weapons, fights, and abandoned luggage.
- **📊 Analytics**: Historical data and trend analysis of detected security events.

---

**System Status**: 🟢 Online  
**Active AI Layers**:
- Layer 1: Object & Weapon Detection (YOLOv8)
- Layer 2: Behavioural Analysis (Fight Logic)
- Layer 3: Pose Estimation (Verification)
- Layer 4: Luggage Association (Anti-Abandonment)

Select a module from the **sidebar** to begin.
""")
