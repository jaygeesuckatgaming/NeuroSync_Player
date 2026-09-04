import os
import sys

def load_blendshape_settings():
    """Load blendshape scaling settings from config.py (single source of truth)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))

    settings = {
        'mouth_scale': 1.0,
        'eye_scale': 1.0,
        'eyebrow_scale': 0.6,
        'eyewide_scale': 0.4,
        'eyesquint_scale': 1.0
    }

    try:
        sys.path.insert(0, root_dir)
        import config as cfg
        settings['mouth_scale'] = float(getattr(cfg, 'BLENDSHAPE_MOUTH_SCALE', 1.0))
        settings['eye_scale'] = float(getattr(cfg, 'BLENDSHAPE_EYE_SCALE', 1.0))
        settings['eyebrow_scale'] = float(getattr(cfg, 'BLENDSHAPE_EYEBROW_SCALE', 0.6))
        settings['eyewide_scale'] = float(getattr(cfg, 'BLENDSHAPE_EYEWIDE_SCALE', 0.4))
        settings['eyesquint_scale'] = float(getattr(cfg, 'BLENDSHAPE_EYESQUINT_SCALE', 1.0))
        print(f"✅ Loaded blendshape settings from config.py")
        print(f"   Mouth: {settings['mouth_scale']}, Eye: {settings['eye_scale']}, Eyebrow: {settings['eyebrow_scale']}")
        print(f"   EyeWide: {settings['eyewide_scale']}, EyeSquint: {settings['eyesquint_scale']}")
    except Exception as e:
        print(f"⚠️  Error loading blendshape settings from config.py: {e}, using defaults")

    return settings

if __name__ == "__main__":
    settings = load_blendshape_settings()
    print(f"\nBlendshape settings loaded: {settings}")
