# ==============================================================================
#  MERGED watcher_to_face + NeuroSync Local API (TEST)
# ==============================================================================
# This is a single-process experiment that combines the NeuroSync Local API
# (audio -> blendshapes inference) with watcher_to_face (file watching + audio
# playback + LiveLink UDP to Unreal).
#
# It replaces the HTTP round-trip (port 9000) with a direct in-process call to
# generate_facial_data_from_bytes(), so there is no Flask server, no JSON
# serialization, and no cross-process hop.
#
# This file is NEW. It does NOT modify any existing files. To run it manually:
#     python merged_watcher_to_face.py
# ==============================================================================

import os
import sys
import time
import warnings

# --- Locate project directories -------------------------------------------------
PLAYER_DIR = os.path.dirname(os.path.abspath(__file__))                 # .../NeuroSync_Player
LOCAL_API_DIR = os.path.join(os.path.dirname(PLAYER_DIR), "NeuroSync_Local_API")


def find_project_root(marker_file=".project_root"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.exists(os.path.join(current_dir, marker_file)):
            return current_dir
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent
    return None


ROOT_DIR = find_project_root()
if not ROOT_DIR:
    raise FileNotFoundError("Could not find the project root (.project_root).")

# --- sys.path: order matters to avoid 'utils' / 'config' collisions --------------
# Root dir must come FIRST so `import config` resolves to the project's single
# source of truth (which defines TTS_OUTPUT_PATH, NEUROSYNC_*, LIVELINK_*, etc.).
# The 'utils' package is a NAMESPACE package in BOTH NeuroSync projects (no
# __init__.py), so putting both dirs on sys.path lets their submodules coexist:
#   - utils.model.model / utils.config / utils.generate_face_shapes  -> Local API
#   - utils.audio.play_audio / utils.generated_runners / utils.files -> Player
for d in (LOCAL_API_DIR, PLAYER_DIR, ROOT_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)
# Ensure ROOT_DIR ends up in front (last insert wins position 0).
sys.path.insert(0, ROOT_DIR)

# --- Model inference side (from the Local API) ----------------------------------
import torch

from utils.config import config as MODEL_CONFIG                       # dict of hyperparams
from utils.model.model import load_model
from utils.generate_face_shapes import generate_facial_data_from_bytes

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = os.path.join(LOCAL_API_DIR, "utils", "model", "model.pth")

# --- Player side (audio + LiveLink + orchestration) ----------------------------
import pygame
from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation
from utils.audio.play_audio import read_audio_file_as_bytes
from utils.generated_runners import run_audio_animation
from utils.files.file_utils import initialize_directories, save_generated_data_from_wav

import config as cfg  # project root single source of truth

try:
    import sounddevice as sd  # noqa: F401  (kept for parity with watcher)
except ImportError:
    pass

warnings.filterwarnings(
    "ignore",
    message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work",
)


def get_playback_device_from_config(cfg):
    try:
        device_str = getattr(cfg, "AUDIO_OUTPUT_DEVICE", "")
        if not device_str or device_str.lower() == "none" or "]" not in device_str:
            return None
        return device_str.split("] ", 1)[1]
    except Exception:
        return None


def delete_file_with_retry(filepath, max_retries=5, delay=0.2):
    for _ in range(max_retries):
        try:
            os.remove(filepath)
            print(f"✅ Deleted '{os.path.basename(filepath)}'. Waiting for next file...")
            return True
        except PermissionError:
            time.sleep(delay)
        except FileNotFoundError:
            return True
        except Exception:
            return False
    print(f"❌ FAILED to delete file '{os.path.basename(filepath)}'.")
    return False


if __name__ == "__main__":
    print("=== MERGED watcher_to_face (local inference) ===")

    # Resolve settings from project config (same as watcher_to_face.py)
    target_file_path = getattr(cfg, "TTS_OUTPUT_PATH", "tts_output/server_output.wav")
    if not os.path.isabs(target_file_path):
        target_file_path = os.path.join(ROOT_DIR, target_file_path)
    requested_name = get_playback_device_from_config(cfg)

    # --- Load the model ONCE (same as the Local API did at startup) ---
    print(f"[MODEL] Loading model from {MODEL_PATH} on {DEVICE} ...")
    blendshape_model = load_model(MODEL_PATH, MODEL_CONFIG, DEVICE)
    print("[MODEL] Model loaded.")

    # --- Smart audio device init (parity with watcher_to_face.py) ---
    print("\n" + "=" * 60)
    print(f"🔍  Searching for audio device match for: '{requested_name}'")
    try:
        pygame.init()
        from pygame._sdl2 import get_audio_device_names
        available_devices = get_audio_device_names(False)
        final_device_name = None
        if requested_name:
            for device in available_devices:
                if requested_name == device or requested_name in device:
                    final_device_name = device
                    print(f"✅  MATCH FOUND: Using '{final_device_name}'")
                    break
        pygame.quit()
        if final_device_name:
            pygame.mixer.pre_init(44100, -16, 2, 512, devicename=final_device_name)
        else:
            print("⚠️  NO MATCH / FALLBACK: Using System Default Audio Device.")
            pygame.mixer.pre_init(44100, -16, 2, 512, devicename=None)
        pygame.init()
        pygame.mixer.init()
        if pygame.mixer.get_init():
            print("🔊  Audio Engine is Ready.")
        else:
            print("❌  Audio Engine failed to start.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ CRITICAL AUDIO ERROR: {e} -> defaulting.")
        try:
            pygame.quit()
            pygame.init()
            pygame.mixer.init()
        except Exception:
            pass
    print("=" * 60 + "\n")

    # --- Face / socket / idle animation ---
    initialize_directories()
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()

    default_animation_thread = __import__("threading").Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()

    print("--- Merged processor started ---")
    print(f"Watching for file: {target_file_path}")

    try:
        while True:
            if os.path.exists(target_file_path):
                print(f"\n✅ File detected: '{os.path.basename(target_file_path)}'")

                # Wait for the file write to complete (size stable)
                last_size = -1
                while last_size != os.path.getsize(target_file_path):
                    last_size = os.path.getsize(target_file_path)
                    time.sleep(0.1)

                try:
                    audio_bytes = read_audio_file_as_bytes(target_file_path)
                    if audio_bytes is None:
                        print("❌ Failed to read audio bytes.")
                    else:
                        # --- THE MERGE: direct in-process inference (no HTTP) ---
                        blendshapes = generate_facial_data_from_bytes(
                            audio_bytes, blendshape_model, DEVICE, MODEL_CONFIG
                        )

                        if blendshapes is None or len(blendshapes) == 0:
                            print("❌ Failed to generate blendshapes.")
                        else:
                            run_audio_animation(
                                target_file_path, blendshapes,
                                py_face, socket_connection, default_animation_thread,
                            )
                            # Optional: still persist the result (parity with watcher)
                            save_generated_data_from_wav(target_file_path, blendshapes)
                            print("✅ Processing complete.")
                except Exception as e:
                    print(f"❌ Error during processing: {e}")
                finally:
                    try:
                        if pygame.mixer.get_init():
                            pygame.mixer.music.stop()
                            pygame.mixer.music.unload()
                    except Exception:
                        pass
                    delete_file_with_retry(target_file_path)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        stop_default_animation.set()
        if default_animation_thread and default_animation_thread.is_alive():
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()
        print("Exiting.")
