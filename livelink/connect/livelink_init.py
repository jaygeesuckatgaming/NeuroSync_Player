import socket
from livelink.connect.pylivelinkface import PyLiveLinkFace, FaceBlendShape
import os            # --- NEW ---
import sys           # --- NEW ---

# --- NEW: Robust, portable method to find the project root ---
def find_project_root(marker_file='.project_root'):
    """Walks up from the script's location to find the project root."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        current_dir = os.getcwd()
    while True:
        if os.path.exists(os.path.join(current_dir, marker_file)):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            return None
        current_dir = parent_dir

root_dir = find_project_root()
if not root_dir:
    raise FileNotFoundError("Could not find the project root. Make sure a '.project_root' file exists in your main 'Gem-System' folder.")

# --- Read settings from config.py (single source of truth, same file the
#     control panel writes to), NOT mcp_settings.ini ---
UDP_IP = "127.0.0.1"
UDP_PORT = 11111

try:
    sys.path.insert(0, root_dir)
    import config as cfg
    UDP_IP = getattr(cfg, 'LIVELINK_IP', UDP_IP)
    UDP_PORT = getattr(cfg, 'LIVELINK_PORT', UDP_PORT)
    print(f"✅ livelink_init.py: Loaded LiveLink settings from config.py ({UDP_IP}:{UDP_PORT}).")
except Exception as e:
    print(f"⚠️ livelink_init.py WARNING: Could not read config.py. Using defaults. Error: {e}")

def create_socket_connection():
    # This function now uses the globally defined UDP_IP and UDP_PORT
    print(f"Attempting to connect to LiveLink at {UDP_IP}:{UDP_PORT}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((UDP_IP, UDP_PORT))
    print("✅ Socket connection established.")
    return s

def initialize_py_face():
    py_face = PyLiveLinkFace()
    initial_blendshapes = [0.0] * 61
    for i, value in enumerate(initial_blendshapes):
        py_face.set_blendshape(FaceBlendShape(i), float(value))
    return py_face