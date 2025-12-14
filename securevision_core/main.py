import os
import sys

def main():
    """
    Entry point to run the Streamlit application.
    """
    print("Starting SecureVision Dashboard...")
    
    # We need to run this script with 'streamlit run'
    # If executed directly with python, we can use subprocess or just tell the user.
    # But the prompt asks for 'main.py' as the project entry point.
    # Usually 'streamlit run main.py' is how you start it.
    # If this file IS the streamlit app, we can just put the code here.
    # But we separated it into ui/main_dashboard.py.
    # So this file will wrap it.
    
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ui', 'Home.py'))
    
    # Use subprocess to avoid shell quoting issues with spaces in paths
    cmd = [sys.executable, "-m", "streamlit", "run", file_path]
    print(f"Executing: {' '.join(cmd)}")
    
    import subprocess
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
