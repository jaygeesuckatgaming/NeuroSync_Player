import configparser
import os

def load_blendshape_settings():
    """Load blendshape scaling settings from mcp_settings.ini"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
    ini_path = os.path.join(root_dir, 'mcp_settings.ini')
    
    config = configparser.ConfigParser()
    config.read(ini_path)
    
    settings = {
        'mouth_scale': 1.0,
        'eye_scale': 1.0,
        'eyebrow_scale': 0.6,
        'eyewide_scale': 0.4,
        'eyesquint_scale': 1.0
    }
    
    if config.has_section('NeurosyncBlendshapes'):
        try:
            settings['mouth_scale'] = float(config.get('NeurosyncBlendshapes', 'mouth_scale', fallback='1.0'))
            settings['eye_scale'] = float(config.get('NeurosyncBlendshapes', 'eye_scale', fallback='1.0'))
            settings['eyebrow_scale'] = float(config.get('NeurosyncBlendshapes', 'eyebrow_scale', fallback='0.6'))
            settings['eyewide_scale'] = float(config.get('NeurosyncBlendshapes', 'eyewide_scale', fallback='0.4'))
            settings['eyesquint_scale'] = float(config.get('NeurosyncBlendshapes', 'eyesquint_scale', fallback='1.0'))
            print(f"✅ Loaded blendshape settings from {ini_path}")
            print(f"   Mouth: {settings['mouth_scale']}, Eye: {settings['eye_scale']}, Eyebrow: {settings['eyebrow_scale']}")
            print(f"   EyeWide: {settings['eyewide_scale']}, EyeSquint: {settings['eyesquint_scale']}")
        except Exception as e:
            print(f"⚠️  Error loading blendshape settings: {e}, using defaults")
    else:
        print(f"ℹ️  No [NeurosyncBlendshapes] section found in {ini_path}, using defaults")
    
    return settings

if __name__ == "__main__":
    settings = load_blendshape_settings()
    print(f"\nBlendshape settings loaded: {settings}")
