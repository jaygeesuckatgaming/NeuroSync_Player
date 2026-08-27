# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import socket
import configparser
import os

class EmoteConnect:
    server_address = "127.0.0.1"
    server_port = 10000
    osc_address = "/chat/message"
    
    @classmethod
    def load_settings(cls):
        """Load OSC settings from mcp_settings.ini [OSC] section"""
        try:
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            root_dir = os.path.dirname(script_dir)
            ini_path = os.path.join(root_dir, 'mcp_settings.ini')
            
            config = configparser.ConfigParser()
            if os.path.exists(ini_path):
                config.read(ini_path)
                if config.has_section('OSC'):
                    cls.server_address = config.get('OSC', 'ip', fallback='127.0.0.1')
                    cls.server_port = config.getint('OSC', 'port', fallback=10000)
                    cls.osc_address = config.get('OSC', 'address', fallback='/chat/message')
                    print(f"EmoteConnect loaded OSC settings: {cls.server_address}:{cls.server_port} {cls.osc_address}")
                    return
        except Exception as e:
            print(f"EmoteConnect failed to load OSC settings: {e}")
        
        # Fallback to config.py defaults
        try:
            from config import EMOTE_SERVER_ADDRESS, EMOTE_SERVER_PORT
            cls.server_address = EMOTE_SERVER_ADDRESS
            cls.server_port = EMOTE_SERVER_PORT
        except:
            pass
    
    @classmethod
    def send_emote(cls, emote_name: str):
        """
        Sends the provided emote name via OSC (UDP) to your Unreal system.
        Uses the same [OSC] settings as movement commands.
        """
        # Load settings from INI file
        cls.load_settings()
        
        # Validate the emote name
        if not emote_name.strip():
            print("Emote name is invalid or empty.")
            return

        try:
            emote_name = emote_name.strip()
            
            # Build OSC message manually (no external library needed)
            # Format: address pattern, type tag, string length, string data
            
            # Address pattern (null-padded to multiple of 4)
            address = cls.osc_address.encode('utf-8')
            address_padded = address + b'\x00' * ((4 - len(address) % 4) % 4)
            
            # Type tag string: ,s (string)
            type_tag = b',s\x00\x00'
            
            # String length (32-bit big-endian)
            str_len = len(emote_name.encode('utf-8'))
            length_bytes = str_len.to_bytes(4, 'big')
            
            # String data (null-padded to multiple of 4)
            arg_bytes = emote_name.encode('utf-8')
            arg_padded = arg_bytes + b'\x00' * ((4 - len(arg_bytes) % 4) % 4)
            
            # Complete OSC message
            message = address_padded + type_tag + length_bytes + arg_padded
            
            # Send via UDP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(message, (cls.server_address, cls.server_port))
            
            print(f"OSC Emote sent: '{emote_name}' to {cls.server_address}:{cls.server_port} {cls.osc_address}")
            
        except Exception as ex:
            print(f"Error while sending emote: {ex}")



'''
EmoteConnect.send_emote("Wave")

# To send an emote on its own thread (non-blocking):
thread = threading.Thread(target=EmoteConnect.send_emote, args=("Wave",))
thread.start()

'''
