#!/usr/bin/env python3
"""
Keyboard Analytics App - PyQt6 Version
A real-time keyboard visualization and analytics application for macOS
"""

import sys
import time
import os
import math
import json
from collections import defaultdict, deque
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pynput import keyboard as global_keyboard
from PyQt6.QtWidgets import QCheckBox, QSystemTrayIcon
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QRect, QSize, QObject

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QComboBox, QFrame, QScrollArea,
    QSizePolicy
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QRect, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, 
    QPalette, QLinearGradient, QKeyEvent
)


@dataclass
class KeyDef:
    """Key definition matching the HTML structure"""
    row: int
    col: int
    x: float
    y: float
    width: float
    height: float
    label: str
    code: str
    key: str
    rotation: float = 0.0
    is_special: bool = False
    is_knob: bool = False
    space_side: Optional[str] = None

class PynputGlobalKeyListener(QObject):
    """Global keyboard listener - DIRECT APPROACH"""
    key_pressed = pyqtSignal(str)
    key_released = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        
    def start_listening(self):
        """Start global keyboard capture using direct pynput"""
        print("🎯 Starting DIRECT pynput capture...")
        
        if not self.running:
            try:
                import subprocess
                import sys
                
                # Use the EXACT same code that worked in your test script
                script = f'''
import sys
sys.path.insert(0, "{os.path.dirname(sys.executable)}")

from pynput import keyboard
import time

print("🚀 DIRECT CAPTURE STARTING!")

def on_press(key):
    try:
        print(f"KEY_PRESS:{{key}}")
        sys.stdout.flush()
    except:
        pass

def on_release(key):
    try:
        print(f"KEY_RELEASE:{{key}}")
        sys.stdout.flush()
    except:
        pass

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    listener.stop()
'''
                
                # Write and run the script
                script_path = "/tmp/direct_keylogger.py"
                with open(script_path, 'w') as f:
                    f.write(script)
                
                # Start subprocess with real-time output
                self.process = subprocess.Popen([
                    sys.executable, script_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                   bufsize=1, universal_newlines=True)
                
                self.running = True
                
                # Start reading output
                self.read_timer = QTimer()
                self.read_timer.timeout.connect(self.read_process_output)
                self.read_timer.start(50)  # Check every 50ms
                
                print("✅ DIRECT CAPTURE IS LIVE!")
                return True
                
            except Exception as e:
                print(f"❌ Failed to start direct capture: {e}")
                return False
        
        return False
    
    def read_process_output(self):
        """Read subprocess output in real-time"""
        if self.process and self.process.poll() is None:
            try:
                # Read available output
                import select
                if select.select([self.process.stdout], [], [], 0)[0]:
                    line = self.process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line.startswith("KEY_PRESS:"):
                            key_str = line[10:]
                            code = self.convert_key_string(key_str)
                            if code:
                                print(f"🌍 DIRECT PRESS: {code}")
                                self.key_pressed.emit(code)
                        elif line.startswith("KEY_RELEASE:"):
                            key_str = line[12:]
                            code = self.convert_key_string(key_str)
                            if code:
                                self.key_released.emit(code)
            except:
                pass
    
    def convert_key_string(self, key_str):
        """Convert string representation to code"""
        # Handle character keys
        if len(key_str) == 3 and key_str.startswith("'") and key_str.endswith("'"):
            char = key_str[1].lower()
            if char.isalpha():
                return f'Key{char.upper()}'
            elif char.isdigit():
                return f'Digit{char}'
        
        # Handle special keys
        if "Key.space" in key_str:
            return 'Space'
        elif "Key.enter" in key_str:
            return 'Enter'
        elif "Key.backspace" in key_str:
            return 'Backspace'
        elif "Key.cmd" in key_str:
            return 'MetaLeft'
        
        return None
    
    def stop_listening(self):
        """Stop capture"""
        self.running = False
        if hasattr(self, 'read_timer'):
            self.read_timer.stop()
        if hasattr(self, 'process') and self.process:
            self.process.terminate()

class KeyboardLibraryListener(QThread):
    """Global keyboard listener using 'keyboard' library - ACTUALLY WORKS"""
    key_pressed = pyqtSignal(str)
    key_released = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        
    def start_listening(self):
        """Start keyboard library capture"""
        print("🎯 Starting keyboard library global capture...")
        if not self.running:
            self.running = True
            self.start()
            return True
        return False
    
    def stop_listening(self):
        """Stop capture"""
        self.running = False
        try:
            import keyboard
            keyboard.unhook_all()
        except:
            pass
        self.quit()
        self.wait()
    
    def run(self):
        """Use keyboard library for global capture"""
        try:
            import keyboard
            print("🚀 keyboard library detected!")
            
            def on_key_event(event):
                if not self.running:
                    return
                code = self.convert_keyboard_event(event)
                if code:
                    if event.event_type == keyboard.KEY_DOWN:
                        print(f"🌍 GLOBAL KEY: {code}")
                        self.key_pressed.emit(code)
                    elif event.event_type == keyboard.KEY_UP:
                        self.key_released.emit(code)
            
            keyboard.hook(on_key_event)
            print("✅ GLOBAL CAPTURE IS LIVE! Type ANYWHERE!")
            
            while self.running:
                import time
                time.sleep(0.1)
                
        except ImportError:
            print("❌ Install keyboard library: pip install keyboard")
        except Exception as e:
            print(f"❌ keyboard library failed: {e}")
    
    def convert_keyboard_event(self, event):
        """Convert keyboard event to web code"""
        # Implementation here...
        return f"Key{event.name.upper()}" if event.name.isalpha() else None

class GlobalKeyListener(QThread):
    """Global keyboard listener using keyboard library"""
    key_pressed = pyqtSignal(str)
    key_released = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self._keyboard_available = False
        self._test_keyboard_lib()
        
    def _test_keyboard_lib(self):
        """Test if keyboard library works"""
        try:
            import keyboard
            self._keyboard_available = True
            print("keyboard library available")
        except ImportError:
            print("keyboard library not installed - run: pip install keyboard")
            self._keyboard_available = False
        except Exception as e:
            print(f"keyboard library error: {e}")
            self._keyboard_available = False
    
    def start_listening(self):
        """Start global keyboard capture"""
        if not self._keyboard_available:
            print("Cannot start: keyboard library not available")
            return False
            
        if not self.running:
            self.running = True
            self.start()
            return True
        return False
    
    def stop_listening(self):
        """Stop global keyboard capture"""
        self.running = False
        try:
            import keyboard
            keyboard.unhook_all()
        except:
            pass
        self.quit()
        self.wait()
    
    def run(self):
        """Thread run method using keyboard library"""
        if not self._keyboard_available:
            return
            
        try:
            import keyboard
            print("🎯 Starting keyboard library global capture...")
            
            def on_key_event(event):
                if not self.running:
                    return
                    
                try:
                    code = self.keyboard_event_to_web_code(event)
                    if code:
                        if event.event_type == keyboard.KEY_DOWN:
                            print(f"🌍 GLOBAL KEY DOWN: {code}")
                            self.key_pressed.emit(code)
                        elif event.event_type == keyboard.KEY_UP:
                            self.key_released.emit(code)
                except Exception as e:
                    print(f"Error processing key event: {e}")
            
            # Hook all keyboard events
            keyboard.hook(on_key_event)
            print("🚀 keyboard library capture is LIVE! Type ANYWHERE!")
            
            # Keep the hook alive
            while self.running:
                import time
                time.sleep(0.1)
                
        except Exception as e:
            print(f"💥 keyboard library failed: {e}")
            print("This might need different permissions or sudo")
    
    def keyboard_event_to_web_code(self, event) -> Optional[str]:
        """Convert keyboard library event to web code"""
        try:
            name = event.name.lower()
            
            # Handle letters
            if len(name) == 1 and name.isalpha():
                return f'Key{name.upper()}'
            
            # Handle numbers
            elif len(name) == 1 and name.isdigit():
                return f'Digit{name}'
            
            # Handle special keys
            special_map = {
                'space': 'Space',
                'enter': 'Enter',
                'backspace': 'Backspace',
                'delete': 'Delete',
                'tab': 'Tab',
                'left shift': 'ShiftLeft',
                'right shift': 'ShiftRight',
                'left ctrl': 'ControlLeft',
                'right ctrl': 'ControlRight',
                'left alt': 'AltLeft',
                'right alt': 'AltRight',
                'left windows': 'MetaLeft',
                'right windows': 'MetaRight',
                'caps lock': 'CapsLock',
                'esc': 'Escape',
                'up': 'ArrowUp',
                'down': 'ArrowDown',
                'left': 'ArrowLeft',
                'right': 'ArrowRight',
                'home': 'Home',
                'end': 'End',
                'page up': 'PageUp',
                'page down': 'PageDown',
                'insert': 'Insert',
                'f1': 'F1', 'f2': 'F2', 'f3': 'F3', 'f4': 'F4',
                'f5': 'F5', 'f6': 'F6', 'f7': 'F7', 'f8': 'F8',
                'f9': 'F9', 'f10': 'F10', 'f11': 'F11', 'f12': 'F12',
                ';': 'Semicolon',
                "'": 'Quote',
                ',': 'Comma',
                '.': 'Period',
                '/': 'Slash',
                '\\': 'Backslash',
                '[': 'BracketLeft',
                ']': 'BracketRight',
                '-': 'Minus',
                '=': 'Equal',
                '`': 'Backquote'
            }
            
            return special_map.get(name)
            
        except Exception as e:
            print(f"Error converting keyboard event: {e}")
            return None


class MiniKeyWidget(QWidget):
    """Optimized miniature key widget for overlay"""
    
    def __init__(self, key_def: KeyDef, scale_factor: float = 0.15):
        super().__init__()
        self.key_def = key_def
        self.scale_factor = scale_factor
        self.is_pressed = False
        self.update_geometry()
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)  # Optimize painting
        
    def update_geometry(self):
        x = int(self.key_def.x * self.scale_factor)
        y = int(self.key_def.y * self.scale_factor)
        w = max(4, int(self.key_def.width * self.scale_factor))
        h = max(4, int(self.key_def.height * self.scale_factor))
        self.setGeometry(x, y, w, h)
        
    def set_pressed(self, pressed: bool):
        if self.is_pressed != pressed:
            self.is_pressed = pressed
            # Only update if state actually changed
            self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # Disable antialiasing for performance
        
        rect = self.rect()
        
        # Key background
        if self.is_pressed:
            color = QColor(255, 126, 95)
        else:
            color = QColor(80, 80, 80)
        
        painter.fillRect(rect, color)
        
        # Draw border
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.drawRect(rect)


class MiniOverlay(QWidget):
    """Miniature floating overlay window"""
    
    def __init__(self, analytics: 'KeyboardAnalytics', parent=None):
        super().__init__(parent)
        self.analytics = analytics
        self.keys = {}
        self.pressed_keys = set()
        
        # macOS-optimized window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # macOS-specific attributes
        if hasattr(Qt.WidgetAttribute, 'WA_MacAlwaysShowToolWindow'):
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        
        self.setup_ui()
        self.setup_mini_keyboard()
        
        # Position in bottom-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 100)
        
        # Create a set of active keys for quick lookup
        self.active_keys = set()
        
        # Use a single shot timer for key updates
        self.update_keys_timer = QTimer()
        self.update_keys_timer.setSingleShot(True)
        self.update_keys_timer.timeout.connect(self.update_key_states)
        
        # Update timer - less frequent for analytics
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_analytics)
        self.update_timer.start(250)  # Update every 250ms
    
    def handle_key_press(self, code: str):
        """Queue key press for processing"""
        if code not in self.active_keys:
            self.active_keys.add(code)
            self.schedule_key_update()
    
    def handle_key_release(self, code: str):
        """Queue key release for processing"""
        if code in self.active_keys:
            self.active_keys.discard(code)
            self.schedule_key_update()
    
    def schedule_key_update(self):
        """Schedule a key state update in the next event loop cycle"""
        if not self.update_keys_timer.isActive():
            self.update_keys_timer.start(0)
    
    def update_key_states(self):
        """Update all key states at once for efficiency"""
        # Create a set of all key widgets that should be pressed
        keys_to_press = set()
        for code in self.active_keys:
            if code in self.keys:
                for key_widget in self.keys[code]:
                    keys_to_press.add(key_widget)
        
        # Update all key widgets
        for key_widget in self.pressed_keys.copy():
            should_be_pressed = key_widget in keys_to_press
            if key_widget.is_pressed != should_be_pressed:
                key_widget.set_pressed(should_be_pressed)
                if should_be_pressed:
                    self.pressed_keys.add(key_widget)
                else:
                    self.pressed_keys.discard(key_widget)
    
    def showEvent(self, event):
        """Ensure overlay stays on top when shown"""
        super().showEvent(event)
        self.raise_()  # Remove the activateWindow() call
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Semi-transparent background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 200);
                border-radius: 8px;
                color: white;
            }
        """)
        
        # Keyboard container - made bigger to fit proper layout
        self.keyboard_container = QWidget()
        self.keyboard_container.setFixedSize(220, 65)
        layout.addWidget(self.keyboard_container)
        
        # Analytics
        analytics_layout = QHBoxLayout()
        analytics_layout.setSpacing(10)
        
        self.kps_label = QLabel("0.0 KPS")
        self.kps_label.setStyleSheet("font-size: 11px; color: #ff7e5f; font-weight: bold;")
        
        self.total_label = QLabel("0")
        self.total_label.setStyleSheet("font-size: 11px; color: #ff7e5f; font-weight: bold;")
        
        analytics_layout.addWidget(QLabel("KPS:"))
        analytics_layout.addWidget(self.kps_label)
        analytics_layout.addWidget(QLabel("Total:"))
        analytics_layout.addWidget(self.total_label)
        
        layout.addLayout(analytics_layout)
        
        self.setFixedSize(240, 100)
        
    def setup_mini_keyboard(self):
        # Simple compact layout that fits in the container
        layout_keys = [
            # Row 1 (Numbers)
            KeyDef(1, 1, 5, 5, 15, 8, '1', 'Digit1', '1'),
            KeyDef(1, 2, 22, 5, 15, 8, '2', 'Digit2', '2'),
            KeyDef(1, 3, 39, 5, 15, 8, '3', 'Digit3', '3'),
            KeyDef(1, 4, 56, 5, 15, 8, '4', 'Digit4', '4'),
            KeyDef(1, 5, 73, 5, 15, 8, '5', 'Digit5', '5'),
            KeyDef(1, 6, 90, 5, 15, 8, '6', 'Digit6', '6'),
            KeyDef(1, 7, 107, 5, 15, 8, '7', 'Digit7', '7'),
            KeyDef(1, 8, 124, 5, 15, 8, '8', 'Digit8', '8'),
            KeyDef(1, 9, 141, 5, 15, 8, '9', 'Digit9', '9'),
            KeyDef(1, 10, 158, 5, 15, 8, '0', 'Digit0', '0'),
            KeyDef(1, 11, 175, 5, 25, 8, 'Bksp', 'Backspace', 'Backspace'),
            
            # Row 2 (QWERTY)
            KeyDef(2, 1, 5, 15, 20, 8, 'Tab', 'Tab', 'Tab'),
            KeyDef(2, 2, 27, 15, 15, 8, 'Q', 'KeyQ', 'q'),
            KeyDef(2, 3, 44, 15, 15, 8, 'W', 'KeyW', 'w'),
            KeyDef(2, 4, 61, 15, 15, 8, 'E', 'KeyE', 'e'),
            KeyDef(2, 5, 78, 15, 15, 8, 'R', 'KeyR', 'r'),
            KeyDef(2, 6, 95, 15, 15, 8, 'T', 'KeyT', 't'),
            KeyDef(2, 7, 112, 15, 15, 8, 'Y', 'KeyY', 'y'),
            KeyDef(2, 8, 129, 15, 15, 8, 'U', 'KeyU', 'u'),
            KeyDef(2, 9, 146, 15, 15, 8, 'I', 'KeyI', 'i'),
            KeyDef(2, 10, 163, 15, 15, 8, 'O', 'KeyO', 'o'),
            KeyDef(2, 11, 180, 15, 20, 8, 'P', 'KeyP', 'p'),
            
            # Row 3 (ASDF)
            KeyDef(3, 1, 5, 25, 25, 8, 'Caps', 'CapsLock', 'CapsLock'),
            KeyDef(3, 2, 32, 25, 15, 8, 'A', 'KeyA', 'a'),
            KeyDef(3, 3, 49, 25, 15, 8, 'S', 'KeyS', 's'),
            KeyDef(3, 4, 66, 25, 15, 8, 'D', 'KeyD', 'd'),
            KeyDef(3, 5, 83, 25, 15, 8, 'F', 'KeyF', 'f'),
            KeyDef(3, 6, 100, 25, 15, 8, 'G', 'KeyG', 'g'),
            KeyDef(3, 7, 117, 25, 15, 8, 'H', 'KeyH', 'h'),
            KeyDef(3, 8, 134, 25, 15, 8, 'J', 'KeyJ', 'j'),
            KeyDef(3, 9, 151, 25, 15, 8, 'K', 'KeyK', 'k'),
            KeyDef(3, 10, 168, 25, 15, 8, 'L', 'KeyL', 'l'),
            KeyDef(3, 11, 185, 25, 15, 8, 'Ent', 'Enter', 'Enter'),
            
            # Row 4 (ZXCV)
            KeyDef(4, 1, 5, 35, 30, 8, 'Shift', 'ShiftLeft', 'Shift'),
            KeyDef(4, 2, 37, 35, 15, 8, 'Z', 'KeyZ', 'z'),
            KeyDef(4, 3, 54, 35, 15, 8, 'X', 'KeyX', 'x'),
            KeyDef(4, 4, 71, 35, 15, 8, 'C', 'KeyC', 'c'),
            KeyDef(4, 5, 88, 35, 15, 8, 'V', 'KeyV', 'v'),
            KeyDef(4, 6, 105, 35, 15, 8, 'B', 'KeyB', 'b'),
            KeyDef(4, 7, 122, 35, 15, 8, 'N', 'KeyN', 'n'),
            KeyDef(4, 8, 139, 35, 15, 8, 'M', 'KeyM', 'm'),
            KeyDef(4, 9, 156, 35, 22, 8, ',', 'Comma', ','),
            KeyDef(4, 10, 180, 35, 20, 8, 'Sft', 'ShiftRight', 'Shift'),
            
            # Row 5 (Bottom)
            KeyDef(5, 1, 5, 45, 20, 8, 'Ctrl', 'ControlLeft', 'Control'),
            KeyDef(5, 2, 27, 45, 20, 8, 'Alt', 'AltLeft', 'Alt'),
            KeyDef(5, 3, 49, 45, 80, 8, 'Space', 'Space', ' '),
            KeyDef(5, 4, 131, 45, 20, 8, 'Alt', 'AltRight', 'Alt'),
            KeyDef(5, 5, 153, 45, 20, 8, 'Cmd', 'MetaRight', 'Meta'),
            KeyDef(5, 6, 175, 45, 25, 8, 'Ctrl', 'ControlRight', 'Control'),
        ]
        
        for key_def in layout_keys:
            key_widget = MiniKeyWidget(key_def, 1.0)  # Use scale factor 1.0
            key_widget.setParent(self.keyboard_container)
            
            if key_def.code not in self.keys:
                self.keys[key_def.code] = []
            self.keys[key_def.code].append(key_widget)
            
            key_widget.show()
    
    def handle_key_press(self, code: str):
        if code in self.keys:
            for key_widget in self.keys[code]:
                if key_widget not in self.pressed_keys:
                    self.pressed_keys.add(key_widget)
                    key_widget.set_pressed(True)
    
    def handle_key_release(self, code: str):
        if code in self.keys:
            for key_widget in self.keys[code]:
                if key_widget in self.pressed_keys:
                    self.pressed_keys.remove(key_widget)
                    key_widget.set_pressed(False)
    
    def update_analytics(self):
        self.kps_label.setText(f"{self.analytics.get_kps():.2f}")
        self.total_label.setText(str(self.analytics.total_keystrokes))
        
    def mousePressEvent(self, event):
        self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        
    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)

class KeyboardAnalytics:
    """Analytics data tracking system"""
    
    def __init__(self):
        self.reset()
        self.filename = "key_analytics.json"
        self.load_from_json()  # Load existing data on startup
        
    def reset(self):
        self.total_keystrokes = 0
        self.key_frequency = defaultdict(int)
        self.dwell_times = deque(maxlen=100)
        self.key_down_times = {}
        self.rhythm_data = deque(maxlen=50)
        self.hand_balance = {'left': 0, 'right': 0}
        self.keystroke_timestamps = deque(maxlen=100)  # Store timestamps for KPS calculation
        
        
        # Left hand keys (QWERTY layout)
        self.left_hand_keys = {
            'KeyQ', 'KeyW', 'KeyE', 'KeyR', 'KeyT',
            'KeyA', 'KeyS', 'KeyD', 'KeyF', 'KeyG', 
            'KeyZ', 'KeyX', 'KeyC', 'KeyV', 'KeyB',
            'Digit1', 'Digit2', 'Digit3', 'Digit4', 'Digit5',
            'Tab', 'CapsLock', 'ShiftLeft', 'ControlLeft', 'AltLeft', 'MetaLeft',
            'Backquote', 'Escape'
        }
    
    def load_from_json(self):
        """Load analytics data from JSON file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    # Convert loaded data to our format
                    for entry in data:
                        key = entry['key']
                        count = entry['count']
                        self.key_frequency[key] = count
                        self.total_keystrokes += count
        except Exception as e:
            print(f"Error loading analytics: {e}")
    
    def record_key_press(self, code: str, timestamp: float):
        self.total_keystrokes += 1
        self.key_frequency[code] += 1
        self.keystroke_timestamps.append(timestamp)
        
        # Record keystroke timing for rhythm
        if len(self.keystroke_timestamps) > 1:
            interval = timestamp - self.keystroke_timestamps[-2]
            self.rhythm_data.append(interval)
        
        self.key_down_times[code] = timestamp
        
        # Track hand balance
        if code in self.left_hand_keys:
            self.hand_balance['left'] += 1
        else:
            self.hand_balance['right'] += 1
    
    def record_key_release(self, code: str, timestamp: float):
        if code in self.key_down_times:
            dwell_time = timestamp - self.key_down_times[code]
            self.dwell_times.append(dwell_time)
            del self.key_down_times[code]
    
    def get_average_dwell(self) -> float:
        return sum(self.dwell_times) / len(self.dwell_times) if self.dwell_times else 0
    
    def get_kps(self) -> float:
        """Calculate keys per second using a 1-second rolling window"""
        if len(self.keystroke_timestamps) < 2:
            return 0.0
            
        current_time = time.time() * 1000
        window_start = current_time - 1000  # 1 second window
        
        # Count keys pressed in the last second
        count = 0
        for ts in reversed(self.keystroke_timestamps):
            if ts >= window_start:
                count += 1
            else:
                break
        
        return count
    
    def get_top_keys(self, n: int = 5) -> List[Tuple[str, int]]:
        return sorted(self.key_frequency.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def save_to_json(self):
        try:
            # Convert defaultdict to regular dict
            key_frequency = dict(self.key_frequency)
            sorted_keys = sorted(key_frequency.items(), key=lambda x: x[1], reverse=True)
            
            # Format data for JSON output
            analytics_data = [
                {"key": key, "count": count} 
                for key, count in sorted_keys
            ]
            
            # Write to JSON file
            with open(self.filename, 'w') as f:
                json.dump(analytics_data, f, indent=4)
                
        except Exception as e:
            print(f"Error saving analytics: {e}")


class KeyWidget(QWidget):
    """Individual key visualization widget"""
    
    def __init__(self, key_def: KeyDef, scale_factor: float = 1.0):
        super().__init__()
        self.key_def = key_def
        self.scale_factor = scale_factor
        self.is_pressed = False
        self.update_geometry()
        
    def update_scale(self, scale_factor: float):
        self.scale_factor = scale_factor
        self.update_geometry()
        
    def update_geometry(self):
        x = int(self.key_def.x * self.scale_factor)
        y = int(self.key_def.y * self.scale_factor)
        w = int(self.key_def.width * self.scale_factor)
        h = int(self.key_def.height * self.scale_factor)
        self.setGeometry(x, y, w, h)
        
    def set_pressed(self, pressed: bool):
        if self.is_pressed != pressed:
            self.is_pressed = pressed
            self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Apply rotation if needed
        if self.key_def.rotation != 0:
            painter.translate(rect.center())
            painter.rotate(math.degrees(self.key_def.rotation))
            painter.translate(-rect.center())
        
        # Key background
        if self.is_pressed:
            if self.key_def.is_special:
                gradient = QLinearGradient(0, 0, 0, rect.height())
                gradient.setColorAt(0, QColor(255, 126, 95))
                gradient.setColorAt(1, QColor(229, 106, 74))
                brush = QBrush(gradient)
            else:
                brush = QBrush(QColor(255, 126, 95))
        else:
            if self.key_def.is_special:
                gradient = QLinearGradient(0, 0, 0, rect.height())
                gradient.setColorAt(0, QColor(255, 126, 95))
                gradient.setColorAt(1, QColor(229, 106, 74))
                brush = QBrush(gradient)
            else:
                gradient = QLinearGradient(0, 0, 0, rect.height())
                gradient.setColorAt(0, QColor(90, 90, 90))
                gradient.setColorAt(1, QColor(74, 74, 74))
                brush = QBrush(gradient)
        
        painter.setBrush(brush)
        painter.setPen(QPen(QColor(58, 58, 58), 1))
        
        # Draw key shape
        if self.key_def.is_knob:
            painter.drawEllipse(rect)
        else:
            painter.drawRoundedRect(rect, 6, 6)
        
        # Draw label
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Arial", max(8, int(12 * self.scale_factor)))
        painter.setFont(font)
        
        # Handle multi-line labels
        label_parts = self.key_def.label.split('\n')
        if len(label_parts) > 1:
            # Two-line label
            fm = QFontMetrics(font)
            total_height = fm.height() * 2
            y_start = rect.center().y() - total_height // 2
            
            for i, part in enumerate(label_parts):
                y = y_start + fm.height() * (i + 1)
                text_rect = QRect(rect.x(), y - fm.height(), rect.width(), fm.height())
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, part)
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.key_def.label)


class KeyboardWidget(QWidget):
    """Main keyboard visualization widget"""
    
    key_pressed = pyqtSignal(str)  # code
    key_released = pyqtSignal(str)  # code
    
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.keys: Dict[str, List[KeyWidget]] = {}
        self.current_layout = 'keychron'
        self.scale_factor = 0.8
        self.pressed_keys: Set[KeyWidget] = set()
        
        # Initialize keyboard layouts (exact copy from HTML)
        self.key_layouts = {
            'keychron': [
                # Row 0 (Knob and function keys)
                KeyDef(0, 0, 26.5, 2.89852, 52, 54, 'OSL(1)', 'KC_ACL0', 'OSL(1)', 0.0, False, True),
                KeyDef(0, 1, 106, 2.89852, 52, 54, 'Esc', 'Escape', 'Escape', 0.0, True),
                KeyDef(0, 2, 172.25, 2.89852, 52, 54, 'Scr -', 'F1', 'F1'),
                KeyDef(0, 3, 225.25, 2.89852, 52, 54, 'Scr +', 'F2', 'F2'),
                KeyDef(0, 4, 284.829, 5.30011, 52, 54, 'MCtl', 'F3', 'F3', 0.10472),
                KeyDef(0, 5, 337.539, 10.8401, 52, 54, 'LPad', 'F4', 'F4', 0.10472),
                KeyDef(0, 6, 403.426, 17.7651, 52, 54, 'BL -', 'F5', 'F5', 0.10472),
                KeyDef(0, 7, 456.136, 23.3051, 52, 54, 'BL +', 'F6', 'F6', 0.10472),
                KeyDef(0, 8, 540.748, 23.6689, 52, 54, 'Prvs', 'F7', 'F7', -0.10472),
                KeyDef(0, 9, 593.458, 18.1289, 52, 54, 'Play', 'F8', 'F8', -0.10472),
                KeyDef(0, 10, 659.345, 11.2039, 52, 54, 'Next', 'F9', 'F9', -0.10472),
                KeyDef(0, 11, 712.054, 5.66387, 52, 54, 'Mute', 'F10', 'F10', -0.10472),
                KeyDef(0, 12, 773.8, 2.89852, 52, 54, 'Vol -', 'F11', 'F11'),
                KeyDef(0, 13, 826.8, 2.89852, 52, 54, 'Vol +', 'F12', 'F12'),
                KeyDef(0, 14, 893.05, 2.89852, 52, 54, 'Ins', 'Insert', 'Insert'),
                KeyDef(0, 15, 959.3, 2.89852, 52, 54, 'Del', 'Delete', 'Delete'),

                # Row 1 (Number row)
                KeyDef(1, 0, 39.75, 71.6485, 52, 54, 'M1', 'N/A', 'M1'),
                KeyDef(1, 1, 119.25, 71.6485, 52, 54, '~\n`', 'Backquote', '`'),
                KeyDef(1, 2, 172.25, 71.6485, 52, 54, '!\n1', 'Digit1', '1'),
                KeyDef(1, 3, 225.25, 71.6485, 52, 54, '@\n2', 'Digit2', '2'),
                KeyDef(1, 4, 285.55, 74.5045, 52, 54, '#\n3', 'Digit3', '3', 0.10472),
                KeyDef(1, 5, 338.259, 80.0445, 52, 54, '$\n4', 'Digit4', '4', 0.10472),
                KeyDef(1, 6, 390.969, 85.5845, 52, 54, '%\n5', 'Digit5', '5', 0.10472),
                KeyDef(1, 7, 443.679, 91.1245, 52, 54, '^\n6', 'Digit6', '6', 0.10472),
                KeyDef(1, 8, 513.673, 95.6433, 52, 54, '&\n7', 'Digit7', '7', -0.10472),
                KeyDef(1, 9, 566.383, 90.1033, 52, 54, '*\n8', 'Digit8', '8', -0.10472),
                KeyDef(1, 10, 619.092, 84.5633, 52, 54, '(\n9', 'Digit9', '9', -0.10472),
                KeyDef(1, 11, 671.802, 79.0233, 52, 54, ')\n0', 'Digit0', '0', -0.10472),
                KeyDef(1, 12, 736.7, 71.6485, 52, 54, '_\n-', 'Minus', '-'),
                KeyDef(1, 13, 789.7, 71.6485, 52, 54, '+\n=', 'Equal', '='),
                KeyDef(1, 14, 842.7, 71.6485, 105, 54, 'Backspace', 'Backspace', 'Backspace'),
                KeyDef(1, 15, 980.5, 71.6485, 52, 54, 'PgUp', 'PageUp', 'PageUp'),

                # Row 2 (QWERTY row)
                KeyDef(2, 0, 26.5, 126.649, 52, 54, 'M2', 'N/A', 'M2'),
                KeyDef(2, 1, 106, 126.649, 78.5, 54, 'Tab', 'Tab', 'Tab'),
                KeyDef(2, 2, 185.5, 126.649, 52, 54, 'Q', 'KeyQ', 'q'),
                KeyDef(2, 3, 245.539, 125.602, 52, 54, 'W', 'KeyW', 'w', 0.10472),
                KeyDef(2, 4, 298.249, 131.142, 52, 54, 'E', 'KeyE', 'e', 0.10472),
                KeyDef(2, 5, 350.959, 136.682, 52, 54, 'R', 'KeyR', 'r', 0.10472),
                KeyDef(2, 6, 403.668, 142.222, 52, 54, 'T', 'KeyT', 't', 0.10472),
                KeyDef(2, 7, 493.067, 153.112, 52, 54, 'Y', 'KeyY', 'y', -0.10472),
                KeyDef(2, 8, 545.777, 147.572, 52, 54, 'U', 'KeyU', 'u', -0.10472),
                KeyDef(2, 9, 598.487, 142.032, 52, 54, 'I', 'KeyI', 'i', -0.10472),
                KeyDef(2, 10, 651.196, 136.492, 52, 54, 'O', 'KeyO', 'o', -0.10472),
                KeyDef(2, 11, 703.906, 130.952, 52, 54, 'P', 'KeyP', 'p', -0.10472),
                KeyDef(2, 12, 763.2, 126.649, 52, 54, '{\n[', 'BracketLeft', '['),
                KeyDef(2, 13, 816.2, 126.649, 52, 54, '}\n]', 'BracketRight', ']'),
                KeyDef(2, 14, 869.2, 126.649, 91.75, 54, '|\n\\', 'Backslash', '\\'),
                KeyDef(2, 15, 988.45, 126.649, 52, 54, 'PgDn', 'PageDown', 'PageDown'),

                # Row 3 (ASDF row) 
                KeyDef(3, 0, 13.25, 181.649, 52, 54, 'M3', 'N/A', 'M3'),
                KeyDef(3, 1, 92.75, 181.649, 91.75, 54, 'Caps Lock', 'CapsLock', 'CapsLock'),
                KeyDef(3, 2, 185.5, 181.649, 52, 54, 'A', 'KeyA', 'a'),
                KeyDef(3, 3, 245.061, 180.855, 52, 54, 'S', 'KeyS', 's', 0.10472),
                KeyDef(3, 4, 297.771, 186.395, 52, 54, 'D', 'KeyD', 'd', 0.10472),
                KeyDef(3, 5, 350.48, 191.935, 52, 54, 'F', 'KeyF', 'f', 0.10472),
                KeyDef(3, 6, 403.19, 197.475, 52, 54, 'G', 'KeyG', 'g', 0.10472),
                KeyDef(3, 7, 525.171, 205.041, 52, 54, 'H', 'KeyH', 'h', -0.10472),
                KeyDef(3, 8, 577.881, 199.501, 52, 54, 'J', 'KeyJ', 'j', -0.10472),
                KeyDef(3, 9, 630.591, 193.961, 52, 54, 'K', 'KeyK', 'k', -0.10472),
                KeyDef(3, 10, 683.3, 188.421, 52, 54, 'L', 'KeyL', 'l', -0.10472),
                KeyDef(3, 11, 747.3, 181.649, 52, 54, ':\n;', 'Semicolon', ';'),
                KeyDef(3, 12, 800.3, 181.649, 52, 54, '"\n\'', 'Quote', "'"),
                KeyDef(3, 14, 853.3, 181.649, 118.25, 54, 'Enter', 'Enter', 'Enter', 0.0, True),
                KeyDef(3, 15, 999.05, 181.649, 52, 54, 'Sleep', 'Home', 'Home'),

                # Row 4 (ZXCV row)
                KeyDef(4, 0, 0, 236.649, 52, 54, 'M4', 'N/A', 'M4'),
                KeyDef(4, 1, 79.5, 236.649, 118.25, 54, 'Shift', 'ShiftLeft', 'Shift'),
                KeyDef(4, 2, 198.75, 236.649, 52, 54, 'Z', 'KeyZ', 'z'),
                KeyDef(4, 3, 257.76, 237.493, 52, 54, 'X', 'KeyX', 'x', 0.10472),
                KeyDef(4, 4, 310.47, 243.033, 52, 54, 'C', 'KeyC', 'c', 0.10472),
                KeyDef(4, 5, 363.18, 248.573, 52, 54, 'V', 'KeyV', 'v', 0.10472),
                KeyDef(4, 6, 415.889, 254.113, 52, 54, 'B', 'KeyB', 'b', 0.10472),
                KeyDef(4, 7, 501.93, 262.786, 52, 54, 'B', 'KeyB', 'b', -0.10472),
                KeyDef(4, 8, 554.64, 257.246, 52, 54, 'N', 'KeyN', 'n', -0.10472),
                KeyDef(4, 9, 607.349, 251.706, 52, 54, 'M', 'KeyM', 'm', -0.10472),
                KeyDef(4, 10, 660.059, 246.166, 52, 54, '<\n,', 'Comma', ',', -0.10472),
                KeyDef(4, 11, 712.769, 240.626, 52, 54, '>\n.', 'Period', '.', -0.10472),
                KeyDef(4, 12, 779.1, 236.649, 52, 54, '?\n/', 'Slash', '/'),
                KeyDef(4, 13, 832.1, 236.649, 91.75, 54, 'Shift', 'ShiftRight', 'Shift'),
                KeyDef(4, 14, 938.1, 250.399, 52, 54, '↑', 'ArrowUp', 'ArrowUp'),

                # Row 5 (Bottom row)
                KeyDef(5, 0, 0, 291.649, 52, 54, 'M5', 'N/A', 'M5'),
                KeyDef(5, 1, 79.5, 291.649, 65.25, 54, 'Ctrl', 'ControlLeft', 'Control'),
                KeyDef(5, 2, 145.75, 291.649, 65.25, 54, 'LOpt', 'AltLeft', 'Alt'),
                KeyDef(5, 3, 251.975, 292.884, 65.25, 54, 'LCmd', 'MetaLeft', 'Meta', 0.10472),
                KeyDef(5, 5, 317.717, 302.579, 118.25, 54, 'Space', 'Space', ' ', 0.10472, False, False, 'left'),
                KeyDef(5, 6, 436.495, 311.581, 52, 54, 'MO(1)', 'N/A', 'MO(1)', 0.10472),
                KeyDef(5, 7, 507.454, 313.192, 134.15, 54, 'Space', 'Space', ' ', -0.10472, False, False, 'right'),
                KeyDef(5, 9, 642.089, 303.358, 52, 54, 'RCmd', 'MetaRight', 'Meta', -0.10472),
                KeyDef(5, 10, 694.798, 297.818, 52, 54, 'Ctrl', 'ControlRight', 'Control', -0.10472),
                KeyDef(5, 12, 885.1, 305.399, 52, 54, '←', 'ArrowLeft', 'ArrowLeft'),
                KeyDef(5, 13, 938.1, 305.399, 52, 54, '↓', 'ArrowDown', 'ArrowDown'),
                KeyDef(5, 14, 991.1, 305.399, 52, 54, '→', 'ArrowRight', 'ArrowRight')
            ],
            
            'marvo': [
                # Function row
                KeyDef(0, 0, 10, 10, 52, 54, 'Esc', 'Escape', 'Escape', is_special=True),
                KeyDef(0, 1, 100, 10, 52, 54, 'F1', 'F1', 'F1'),
                KeyDef(0, 2, 160, 10, 52, 54, 'F2', 'F2', 'F2'),
                KeyDef(0, 3, 220, 10, 52, 54, 'F3', 'F3', 'F3'),
                KeyDef(0, 4, 280, 10, 52, 54, 'F4', 'F4', 'F4'),
                KeyDef(0, 5, 384, 10, 52, 54, 'F5', 'F5', 'F5'),
                KeyDef(0, 6, 444, 10, 52, 54, 'F6', 'F6', 'F6'),
                KeyDef(0, 7, 504, 10, 52, 54, 'F7', 'F7', 'F7'),
                KeyDef(0, 8, 564, 10, 52, 54, 'F8', 'F8', 'F8'),
                KeyDef(0, 9, 668, 10, 52, 54, 'F9', 'F9', 'F9'),
                KeyDef(0, 10, 728, 10, 52, 54, 'F10', 'F10', 'F10'),
                KeyDef(0, 11, 788, 10, 52, 54, 'F11', 'F11', 'F11'),
                KeyDef(0, 12, 848, 10, 52, 54, 'F12', 'F12', 'F12'),
                KeyDef(0, 13, 910, 10, 52, 54, 'PrtSc', 'PrintScreen', 'PrintScreen'),
                KeyDef(0, 14, 970, 10, 52, 54, 'ScrLk', 'ScrollLock', 'ScrollLock'),
                KeyDef(0, 15, 1030, 10, 52, 54, 'Pause', 'Pause', 'Pause'),

                # Number row
                KeyDef(1, 0, 10, 70, 52, 54, '~\n`', 'Backquote', '`'),
                KeyDef(1, 1, 70, 70, 52, 54, '!\n1', 'Digit1', '1'),
                KeyDef(1, 2, 130, 70, 52, 54, '@\n2', 'Digit2', '2'),
                KeyDef(1, 3, 190, 70, 52, 54, '#\n3', 'Digit3', '3'),
                KeyDef(1, 4, 250, 70, 52, 54, '$\n4', 'Digit4', '4'),
                KeyDef(1, 5, 310, 70, 52, 54, '%\n5', 'Digit5', '5'),
                KeyDef(1, 6, 370, 70, 52, 54, '^\n6', 'Digit6', '6'),
                KeyDef(1, 7, 430, 70, 52, 54, '&\n7', 'Digit7', '7'),
                KeyDef(1, 8, 490, 70, 52, 54, '*\n8', 'Digit8', '8'),
                KeyDef(1, 9, 550, 70, 52, 54, '(\n9', 'Digit9', '9'),
                KeyDef(1, 10, 610, 70, 52, 54, ')\n0', 'Digit0', '0'),
                KeyDef(1, 11, 670, 70, 52, 54, '_\n-', 'Minus', '-'),
                KeyDef(1, 12, 730, 70, 52, 54, '+\n=', 'Equal', '='),
                KeyDef(1, 13, 790, 70, 110, 54, 'Backspace', 'Backspace', 'Backspace'),
                KeyDef(1, 14, 910, 70, 52, 54, 'Ins', 'Insert', 'Insert'),
                KeyDef(1, 15, 970, 70, 52, 54, 'Home', 'Home', 'Home'),
                KeyDef(1, 16, 1030, 70, 52, 54, 'PgUp', 'PageUp', 'PageUp'),

                # QWERTY row
                KeyDef(2, 0, 10, 130, 78, 54, 'Tab', 'Tab', 'Tab'),
                KeyDef(2, 1, 100, 130, 52, 54, 'Q', 'KeyQ', 'q'),
                KeyDef(2, 2, 160, 130, 52, 54, 'W', 'KeyW', 'w'),
                KeyDef(2, 3, 220, 130, 52, 54, 'E', 'KeyE', 'e'),
                KeyDef(2, 4, 280, 130, 52, 54, 'R', 'KeyR', 'r'),
                KeyDef(2, 5, 340, 130, 52, 54, 'T', 'KeyT', 't'),
                KeyDef(2, 6, 400, 130, 52, 54, 'Y', 'KeyY', 'y'),
                KeyDef(2, 7, 460, 130, 52, 54, 'U', 'KeyU', 'u'),
                KeyDef(2, 8, 520, 130, 52, 54, 'I', 'KeyI', 'i'),
                KeyDef(2, 9, 580, 130, 52, 54, 'O', 'KeyO', 'o'),
                KeyDef(2, 10, 640, 130, 52, 54, 'P', 'KeyP', 'p'),
                KeyDef(2, 11, 700, 130, 52, 54, '{\n[', 'BracketLeft', '['),
                KeyDef(2, 12, 760, 130, 52, 54, '}\n]', 'BracketRight', ']'),
                KeyDef(2, 13, 820, 130, 80, 54, '|\n\\', 'Backslash', '\\'),
                KeyDef(2, 14, 910, 130, 52, 54, 'Del', 'Delete', 'Delete'),
                KeyDef(2, 15, 970, 130, 52, 54, 'End', 'End', 'End'),
                KeyDef(2, 16, 1030, 130, 52, 54, 'PgDn', 'PageDown', 'PageDown'),

                # ASDF row
                KeyDef(3, 0, 10, 190, 88, 54, 'Caps Lock', 'CapsLock', 'CapsLock'),
                KeyDef(3, 1, 110, 190, 52, 54, 'A', 'KeyA', 'a'),
                KeyDef(3, 2, 170, 190, 52, 54, 'S', 'KeyS', 's'),
                KeyDef(3, 3, 230, 190, 52, 54, 'D', 'KeyD', 'd'),
                KeyDef(3, 4, 290, 190, 52, 54, 'F', 'KeyF', 'f'),
                KeyDef(3, 5, 350, 190, 52, 54, 'G', 'KeyG', 'g'),
                KeyDef(3, 6, 410, 190, 52, 54, 'H', 'KeyH', 'h'),
                KeyDef(3, 7, 470, 190, 52, 54, 'J', 'KeyJ', 'j'),
                KeyDef(3, 8, 530, 190, 52, 54, 'K', 'KeyK', 'k'),
                KeyDef(3, 9, 590, 190, 52, 54, 'L', 'KeyL', 'l'),
                KeyDef(3, 10, 650, 190, 52, 54, ':\n;', 'Semicolon', ';'),
                KeyDef(3, 11, 710, 190, 52, 54, '"\n\'', 'Quote', "'"),
                KeyDef(3, 12, 770, 190, 130, 54, 'Enter', 'Enter', 'Enter', is_special=True),
                KeyDef(3, 13, 970, 250, 52, 54, '↑', 'ArrowUp', 'ArrowUp'),

                # ZXCV row
                KeyDef(4, 0, 10, 250, 118, 54, 'Shift', 'ShiftLeft', 'Shift'),
                KeyDef(4, 1, 140.5, 250, 52, 54, 'Z', 'KeyZ', 'z'),
                KeyDef(4, 2, 200, 250, 52, 54, 'X', 'KeyX', 'x'),
                KeyDef(4, 3, 260, 250, 52, 54, 'C', 'KeyC', 'c'),
                KeyDef(4, 4, 320, 250, 52, 54, 'V', 'KeyV', 'v'),
                KeyDef(4, 5, 380, 250, 52, 54, 'B', 'KeyB', 'b'),
                KeyDef(4, 6, 440, 250, 52, 54, 'N', 'KeyN', 'n'),
                KeyDef(4, 7, 500, 250, 52, 54, 'M', 'KeyM', 'm'),
                KeyDef(4, 8, 560, 250, 52, 54, '<\n,', 'Comma', ','),
                KeyDef(4, 9, 620, 250, 52, 54, '>\n.', 'Period', '.'),
                KeyDef(4, 10, 680, 250, 52, 54, '?\n/', 'Slash', '/'),
                KeyDef(4, 11, 741, 250, 160, 54, 'Shift', 'ShiftRight', 'Shift'),
                KeyDef(4, 12, 910, 310, 52, 54, '←', 'ArrowLeft', 'ArrowLeft'),
                KeyDef(4, 13, 970, 310, 52, 54, '↓', 'ArrowDown', 'ArrowDown'),
                KeyDef(4, 14, 1030, 310, 52, 54, '→', 'ArrowRight', 'ArrowRight'),

                # Bottom row
                KeyDef(5, 0, 10, 310, 72, 54, 'Ctrl', 'ControlLeft', 'Control'),
                KeyDef(5, 1, 94, 310, 52, 54, 'Win', 'MetaLeft', 'Meta'),
                KeyDef(5, 2, 154, 310, 52, 54, 'Alt', 'AltLeft', 'Alt'),
                KeyDef(5, 3, 218, 310, 418, 54, 'Space', 'Space', ' '),
                KeyDef(5, 4, 648.5, 310, 52, 54, 'Alt', 'AltRight', 'Alt'),
                KeyDef(5, 5, 708.5, 310, 52, 54, 'Win', 'MetaRight', 'Meta'),
                KeyDef(5, 6, 768, 310, 52, 54, 'Menu', 'ContextMenu', 'ContextMenu'),
                KeyDef(5, 7, 829.5, 310, 72, 54, 'Ctrl', 'ControlRight', 'Control')
            ]
        }
        
        self.setup_keyboard()
        
    def setup_keyboard(self):
        self.keys.clear()
        
        # Clear existing widgets
        for child in self.findChildren(KeyWidget):
            child.deleteLater()
        
        # Create key widgets
        layout_keys = self.key_layouts[self.current_layout]
        
        # Calculate bounds for proper scaling
        max_x = max(k.x + k.width for k in layout_keys)
        max_y = max(k.y + k.height for k in layout_keys)
        
        self.original_size = QSize(int(max_x), int(max_y))
        
        for key_def in layout_keys:
            key_widget = KeyWidget(key_def, self.scale_factor)
            key_widget.setParent(self)
            
            # Group keys by code for handling duplicate keys (like Space, B)
            if key_def.code not in self.keys:
                self.keys[key_def.code] = []
            self.keys[key_def.code].append(key_widget)
            
            key_widget.show()
        
        self.update_size()
    
    def update_size(self):
        if hasattr(self, 'original_size'):
            new_size = QSize(
                int(self.original_size.width() * self.scale_factor),
                int(self.original_size.height() * self.scale_factor)
            )
            self.setFixedSize(new_size)
    
    def set_layout(self, layout_name: str):
        if layout_name in self.key_layouts:
            self.current_layout = layout_name
            self.setup_keyboard()
    
    def set_scale_factor(self, factor: float):
        self.scale_factor = factor
        for key_list in self.keys.values():
            for key_widget in key_list:
                key_widget.update_scale(factor)
        self.update_size()
    
    def handle_key_press(self, code: str):
        self.key_pressed.emit(code)
        
        if code in self.keys:
            for key_widget in self.keys[code]:
                if key_widget not in self.pressed_keys:
                    self.pressed_keys.add(key_widget)
                    key_widget.set_pressed(True)
    
    def handle_key_release(self, code: str):
        self.key_released.emit(code)
        
        if code in self.keys:
            for key_widget in self.keys[code]:
                if key_widget in self.pressed_keys:
                    self.pressed_keys.remove(key_widget)
                    key_widget.set_pressed(False)
    
    def keyPressEvent(self, event: QKeyEvent):
        if not event.isAutoRepeat():
            # Convert Qt key to web key code
            code = self.qt_key_to_web_code(event.key(), event.text())
            if code:
                self.handle_key_press(code)
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event: QKeyEvent):
        if not event.isAutoRepeat():
            code = self.qt_key_to_web_code(event.key(), event.text())
            if code:
                self.handle_key_release(code)
        super().keyReleaseEvent(event)
    
    def qt_key_to_web_code(self, qt_key: int, text: str) -> Optional[str]:
        """Convert Qt key codes to web KeyboardEvent.code format"""
        key_map = {
            # Letters
            Qt.Key.Key_A: 'KeyA', Qt.Key.Key_B: 'KeyB', Qt.Key.Key_C: 'KeyC', Qt.Key.Key_D: 'KeyD',
            Qt.Key.Key_E: 'KeyE', Qt.Key.Key_F: 'KeyF', Qt.Key.Key_G: 'KeyG', Qt.Key.Key_H: 'KeyH',
            Qt.Key.Key_I: 'KeyI', Qt.Key.Key_J: 'KeyJ', Qt.Key.Key_K: 'KeyK', Qt.Key.Key_L: 'KeyL',
            Qt.Key.Key_M: 'KeyM', Qt.Key.Key_N: 'KeyN', Qt.Key.Key_O: 'KeyO', Qt.Key.Key_P: 'KeyP',
            Qt.Key.Key_Q: 'KeyQ', Qt.Key.Key_R: 'KeyR', Qt.Key.Key_S: 'KeyS', Qt.Key.Key_T: 'KeyT',
            Qt.Key.Key_U: 'KeyU', Qt.Key.Key_V: 'KeyV', Qt.Key.Key_W: 'KeyW', Qt.Key.Key_X: 'KeyX',
            Qt.Key.Key_Y: 'KeyY', Qt.Key.Key_Z: 'KeyZ',
            
            # Numbers
            Qt.Key.Key_1: 'Digit1', Qt.Key.Key_2: 'Digit2', Qt.Key.Key_3: 'Digit3', Qt.Key.Key_4: 'Digit4',
            Qt.Key.Key_5: 'Digit5', Qt.Key.Key_6: 'Digit6', Qt.Key.Key_7: 'Digit7', Qt.Key.Key_8: 'Digit8',
            Qt.Key.Key_9: 'Digit9', Qt.Key.Key_0: 'Digit0',
            
            # Function keys
            Qt.Key.Key_F1: 'F1', Qt.Key.Key_F2: 'F2', Qt.Key.Key_F3: 'F3', Qt.Key.Key_F4: 'F4',
            Qt.Key.Key_F5: 'F5', Qt.Key.Key_F6: 'F6', Qt.Key.Key_F7: 'F7', Qt.Key.Key_F8: 'F8',
            Qt.Key.Key_F9: 'F9', Qt.Key.Key_F10: 'F10', Qt.Key.Key_F11: 'F11', Qt.Key.Key_F12: 'F12',
            
            # Special keys
            Qt.Key.Key_Space: 'Space',
            Qt.Key.Key_Return: 'Enter',
            Qt.Key.Key_Enter: 'Enter',
            Qt.Key.Key_Backspace: 'Backspace',
            Qt.Key.Key_Delete: 'Delete',
            Qt.Key.Key_Tab: 'Tab',
            Qt.Key.Key_Shift: 'ShiftLeft',
            Qt.Key.Key_Control: 'ControlLeft',
            Qt.Key.Key_Alt: 'AltLeft',
            Qt.Key.Key_Meta: 'MetaLeft',
            Qt.Key.Key_CapsLock: 'CapsLock',
            Qt.Key.Key_Escape: 'Escape',
            
            # Punctuation
            Qt.Key.Key_Semicolon: 'Semicolon',
            Qt.Key.Key_Apostrophe: 'Quote',
            Qt.Key.Key_Comma: 'Comma',
            Qt.Key.Key_Period: 'Period',
            Qt.Key.Key_Slash: 'Slash',
            Qt.Key.Key_Backslash: 'Backslash',
            Qt.Key.Key_BracketLeft: 'BracketLeft',
            Qt.Key.Key_BracketRight: 'BracketRight',
            Qt.Key.Key_Minus: 'Minus',
            Qt.Key.Key_Equal: 'Equal',
            Qt.Key.Key_QuoteLeft: 'Backquote',
            
            # Arrows
            Qt.Key.Key_Left: 'ArrowLeft',
            Qt.Key.Key_Right: 'ArrowRight',
            Qt.Key.Key_Up: 'ArrowUp',
            Qt.Key.Key_Down: 'ArrowDown',
            
            # Navigation
            Qt.Key.Key_Home: 'Home',
            Qt.Key.Key_End: 'End',
            Qt.Key.Key_PageUp: 'PageUp',
            Qt.Key.Key_PageDown: 'PageDown',
            Qt.Key.Key_Insert: 'Insert',
        }
        
        return key_map.get(qt_key)


class RhythmChart(QWidget):
    """Compact keystroke rhythm visualization chart"""
    
    def __init__(self):
        super().__init__()
        self.data = []
        self.setMinimumHeight(80)  # Reduced height
        
    def update_data(self, rhythm_data: deque):
        self.data = list(rhythm_data)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        painter.fillRect(rect, QColor(50, 50, 50, 100))  # Darker background
        
        if len(self.data) < 2:
            painter.setPen(QPen(QColor(255, 255, 255, 128)))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Start typing...")
            return
        
        # Draw grid
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        for i in range(4):
            y = rect.height() * i / 3
            painter.drawLine(0, int(y), rect.width(), int(y))
        
        # Prepare data
        data = self.data[-20:]  # Only last 20 intervals
        if not data:
            return
            
        max_interval = max(max(data), 500)  # Cap at 500ms
        min_interval = min(min(data), 0)
        
        # Draw rhythm line
        painter.setPen(QPen(QColor(255, 126, 95), 2))
        
        for i in range(1, len(data)):
            x1 = rect.width() * (i - 1) / (len(data) - 1)
            x2 = rect.width() * i / (len(data) - 1)
            
            y1 = rect.height() - (min(data[i-1], 500) - min_interval) / (max_interval - min_interval) * rect.height()
            y2 = rect.height() - (min(data[i], 500) - min_interval) / (max_interval - min_interval) * rect.height()
            
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw data points
        painter.setBrush(QBrush(QColor(255, 126, 95)))
        for i, interval in enumerate(data):
            x = rect.width() * i / (len(data) - 1)
            y = rect.height() - (min(interval, 500) - min_interval) / (max_interval - min_interval) * rect.height()
            painter.drawEllipse(int(x - 2), int(y - 2), 4, 4)


class BalanceBarContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 14)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.setBrush(QBrush(QColor(80, 80, 80, 100)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 6, 6)
        
        # Draw center indicator (vertical line)
        center_x = self.width() // 2
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        painter.drawLine(center_x, 0, center_x, self.height())
        
        # Draw left and right bars (if they exist)
        if hasattr(self, 'left_bar_rect'):
            painter.setBrush(QBrush(QColor(255, 126, 95)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.left_bar_rect, 6, 6)
            
        if hasattr(self, 'right_bar_rect'):
            painter.setBrush(QBrush(QColor(255, 126, 95)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.right_bar_rect, 6, 6)
            
    def set_balance(self, left_percent, right_percent):
        # Calculate bar widths
        left_width = int(self.width() * left_percent / 100)
        right_width = self.width() - left_width
        
        # Set left bar rectangle
        self.left_bar_rect = QRect(0, 0, left_width, self.height())
        
        # Set right bar rectangle (starts where left bar ends)
        self.right_bar_rect = QRect(left_width, 0, right_width, self.height())
        
        self.update()


class AnalyticsPanel(QWidget):
    """Compact Analytics dashboard panel"""
    
    def __init__(self, analytics: KeyboardAnalytics):
        super().__init__()
        self.analytics = analytics
        self.setup_ui()
        
         # Update timer - same as overlay
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(250)  # Update every 250ms

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Live Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_keystrokes_label = self.create_mini_stat("Keystrokes", "0")
        self.avg_dwell_label = self.create_mini_stat("Avg Dwell", "0ms")
        self.kps_label = self.create_mini_stat("KPS", "0.0")
        
        # Create hand balance widget with text and visualization
        hand_balance_container = QWidget()
        hand_balance_layout = QVBoxLayout(hand_balance_container)
        hand_balance_layout.setContentsMargins(0, 0, 0, 0)
        hand_balance_layout.setSpacing(2)
        
        # Hand balance text
        self.hand_balance_label = QLabel("50/50")
        self.hand_balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hand_balance_label.setStyleSheet("""
            QLabel {
                color: #ff7e5f;
                font-size: 18px;
                font-weight: 700;
            }
        """)
        
        # Create balance visualization with labels
        balance_viz_layout = QHBoxLayout()
        balance_viz_layout.setSpacing(5)
        
        # Left label
        left_label = QLabel("L")
        left_label.setStyleSheet("color: #aaa; font-weight: bold;")
        left_label.setFixedWidth(10)
        
        # Custom balance bar container
        self.balance_bar = BalanceBarContainer()
        
        # Right label
        right_label = QLabel("R")
        right_label.setStyleSheet("color: #aaa; font-weight: bold;")
        right_label.setFixedWidth(10)
        
        # Add to layout
        balance_viz_layout.addWidget(left_label)
        balance_viz_layout.addWidget(self.balance_bar)
        balance_viz_layout.addWidget(right_label)
        
        # Add to main layout
        hand_balance_layout.addWidget(self.hand_balance_label)
        hand_balance_layout.addLayout(balance_viz_layout)
        
        # Create a container for the hand balance widget
        hand_balance_wrapper = QWidget()
        wrapper_layout = QVBoxLayout(hand_balance_wrapper)
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrapper_layout.addWidget(hand_balance_container)
        
        stats_layout.addWidget(self.total_keystrokes_label)
        stats_layout.addWidget(self.avg_dwell_label)
        stats_layout.addWidget(self.kps_label)
        stats_layout.addWidget(hand_balance_wrapper)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout, 0, 0, 1, 2)
        
        # Top Keys Card
        top_keys_card = self.create_card("Top Keys")
        self.top_keys_layout = QVBoxLayout()
        self.top_keys_layout.setSpacing(3)
        top_keys_card.setLayout(self.top_keys_layout)
        layout.addWidget(top_keys_card, 1, 0)
        
        # Rhythm Chart Card
        rhythm_card = self.create_card("Typing Rhythm")
        self.rhythm_chart = RhythmChart()
        rhythm_card_layout = QVBoxLayout(rhythm_card)
        rhythm_card_layout.addWidget(self.rhythm_chart)
        layout.addWidget(rhythm_card, 1, 1)
        
        # Set column stretch factors
        layout.setColumnStretch(0, 1)  # Top Keys column
        layout.setColumnStretch(1, 2)  # Rhythm Chart column (wider)
        
        # Set row stretch factors
        layout.setRowStretch(0, 1)  # Stats row
        layout.setRowStretch(1, 3)  # Main content row
        
    def create_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(60, 60, 60, 0.4);
                border: 1px solid rgba(255, 126, 95, 0.2);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        return card
        
    def create_mini_stat(self, label: str, value: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("""
            QLabel {
                color: #ff7e5f;
                font-size: 18px;
                font-weight: 700;
            }
        """)
        
        desc_label = QLabel(label)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 11px;
                text-transform: uppercase;
            }
        """)
        
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        
        widget.value_label = value_label  # Store reference for updates
        widget.desc_label = desc_label
        return widget
        
    def update_display(self):
        # Update live stats
        self.total_keystrokes_label.value_label.setText(str(self.analytics.total_keystrokes))
        self.avg_dwell_label.value_label.setText(f"{int(self.analytics.get_average_dwell())}ms")
        self.kps_label.value_label.setText(f"{self.analytics.get_kps():.1f}")
        
        # Update hand balance
        total = self.analytics.hand_balance['left'] + self.analytics.hand_balance['right']
        if total == 0:
            balance_text = "50/50"
            left_percent = 50
            right_percent = 50
        else:
            left_percent = int((self.analytics.hand_balance['left'] / total) * 100)
            right_percent = 100 - left_percent
            balance_text = f"{left_percent}/{right_percent}"
        self.hand_balance_label.setText(balance_text)
        
        # Update hand balance visualization
        self.balance_bar.set_balance(left_percent, right_percent)
        
        # Update rhythm chart
        self.rhythm_chart.update_data(self.analytics.rhythm_data)
        
        # Update top keys
        self.update_top_keys()
        
    def update_top_keys(self):
        # Clear existing items
        for i in reversed(range(self.top_keys_layout.count())):
            self.top_keys_layout.itemAt(i).widget().deleteLater()
        
        top_keys = self.analytics.get_top_keys(5)
        max_count = top_keys[0][1] if top_keys else 1
        
        for code, count in top_keys:
            item = self.create_top_key_item(self.get_key_display_name(code), count, max_count)
            self.top_keys_layout.addWidget(item)
            
    def create_top_key_item(self, key_name: str, count: int, max_count: int) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 3, 5, 3)
        
        name_label = QLabel(f"{key_name}:")
        name_label.setStyleSheet("color: white; font-weight: 600; font-size: 13px;")
        name_label.setFixedWidth(60)  # Fixed width for key name
        
        # Progress bar
        progress_widget = QWidget()
        progress_widget.setFixedHeight(6)
        progress_widget.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border-radius: 3px;")
        
        # Progress fill - dynamically sized based on count
        progress_fill = QWidget(progress_widget)
        progress_fill.setStyleSheet("background-color: #ff7e5f; border-radius: 3px;")
        fill_width = int(120 * count / max_count)
        progress_fill.setGeometry(0, 0, fill_width, 6)
        
        # Count label - dynamically sized based on digit count
        count_label = QLabel(str(count))
        count_label.setStyleSheet("color: #ff7e5f; font-weight: 700; font-size: 13px;")
        
        # Calculate required width based on digit count
        digit_count = len(str(count))
        min_width = 15 + (digit_count * 7)  # 7px per digit + padding
        count_label.setMinimumWidth(min_width)
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(name_label)
        layout.addWidget(progress_widget, 1)  # Allow progress bar to expand
        layout.addWidget(count_label)
        
        return widget
    
    def reset(self):
        """Reset all analytics data and clear JSON file"""
        self.session_start_time = time.time() * 1000
        self.total_keystrokes = 0
        self.key_frequency = defaultdict(int)
        self.dwell_times = deque(maxlen=100)
        self.keystroke_timings = deque(maxlen=1000)
        self.key_down_times = {}
        self.rhythm_data = deque(maxlen=50)
        self.hand_balance = {'left': 0, 'right': 0}
        
        # Clear the JSON file
        self.save_to_json()
    
    def save_to_json(self):
        """Save key frequencies to JSON file"""
        try:
            # Convert defaultdict to regular dict
            key_frequency = dict(self.key_frequency)
            
            # Create a sorted list of keys with counts
            sorted_keys = sorted(key_frequency.items(), key=lambda x: x[1], reverse=True)
            
            # Format data for JSON output
            analytics_data = [
                {"key": key, "count": count} 
                for key, count in sorted_keys
            ]
            
            # Write to JSON file
            with open(self.filename, 'w') as f:
                json.dump(analytics_data, f, indent=4)
                
        except Exception as e:
            print(f"Error saving analytics: {e}")
        
    def get_key_display_name(self, code: str) -> str:
        key_map = {
            'Space': 'Space',
            'Enter': 'Enter',
            'Backspace': 'Backsp',
            'ShiftLeft': 'LShift',
            'ShiftRight': 'RShift',
            'ControlLeft': 'LCtrl',
            'ControlRight': 'RCtrl',
            'AltLeft': 'LAlt',
            'AltRight': 'RAlt',
            'MetaLeft': 'LCmd',
            'MetaRight': 'RCmd',
            'Tab': 'Tab',
            'CapsLock': 'Caps',
            'Escape': 'Esc'
        }
        
        if code in key_map:
            return key_map[code]
        elif code.startswith('Key'):
            return code[3:]
        elif code.startswith('Digit'):
            return code[5:]
        elif code.startswith('Arrow'):
            return code[5:]
        
        return code

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.analytics = KeyboardAnalytics()
        
        # Initialize these first to prevent crashes
        self.overlay_enabled = False
        self.global_listener = None
        self.mini_overlay = None
        
        # Setup UI first
        self.setup_ui()
        self.setWindowTitle("Keyboard Analytics")
        self.resize(1400, 900)
        
        # Add auto-save timer (saves every 5 seconds)
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_analytics)
        self.save_timer.start(5000)  # 5 seconds
        
        # Enable global key capturing
        self.installEventFilter(self)
        
        # Delay global capture setup to prevent crashes
        QTimer.singleShot(1000, self.setup_global_capture_delayed)

    def setup_global_capture_delayed(self):
        """Setup global capture with delay to prevent initialization crashes"""
        try:
            print("🔧 Setting up delayed global capture...")
            self.setup_global_capture()
        except Exception as e:
            print(f"❌ Delayed global capture setup failed: {e}")
            print("Global overlay will not be available")
    
    def setup_global_capture(self):
        """Setup global capture using pynput - SAFE VERSION"""
        try:
            print("🔧 Setting up global capture...")
            
            # Create mini overlay first (this should always work)
            try:
                self.mini_overlay = MiniOverlay(self.analytics)
                self.mini_overlay.hide()
                print("✅ Mini overlay created")
            except Exception as e:
                print(f"❌ Mini overlay failed: {e}")
                return
            
            # Try to create global listener (this might fail due to permissions)
            try:
                import pynput  # Test import first
                self.global_listener = PynputGlobalKeyListener()
                self.global_listener.key_pressed.connect(self.on_global_key_press)
                self.global_listener.key_released.connect(self.on_global_key_release)
                print("✅ Global listener created")
            except ImportError:
                print("❌ pynput not installed - run: pip install pynput")
                self.global_listener = None
            except Exception as e:
                print(f"⚠️  Global listener creation failed: {e}")
                print("This is normal if accessibility permissions aren't granted yet")
                self.global_listener = None
            
            print("✅ Global capture setup complete")
            
        except Exception as e:
            print(f"❌ Failed to setup global capture: {e}")
            print("App will continue without global capture")
            self.global_listener = None
            if not hasattr(self, 'mini_overlay') or self.mini_overlay is None:
                try:
                    self.mini_overlay = MiniOverlay(self.analytics)
                    self.mini_overlay.hide()
                except:
                    self.mini_overlay = None

    def show_permission_dialog(self, python_path: str):
        """Show permission request dialog"""
        from PyQt6.QtWidgets import QMessageBox
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Accessibility Permission Required")
        msg.setText("TypeChron Viz needs accessibility permissions to capture global keystrokes.")
        msg.setInformativeText(
            f"System Preferences should open automatically.\n\n"
            f"If not, manually:\n"
            f"1. Go to System Preferences → Security & Privacy → Privacy → Accessibility\n"
            f"2. Click the lock and enter your password\n"
            f"3. Click + and add:\n"
            f"   {python_path}\n"
            f"   /Applications/Utilities/Terminal.app\n"
            f"4. Restart the application"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def setup_global_capture(self):
        """Setup global capture using pynput"""
        try:
            print("🔧 Setting up global capture...")
            
            # Create mini overlay first
            self.mini_overlay = MiniOverlay(self.analytics)
            self.mini_overlay.hide()
            
            # Create global listener using pynput
            try:
                self.global_listener = PynputGlobalKeyListener()
                self.global_listener.key_pressed.connect(self.on_global_key_press)
                self.global_listener.key_released.connect(self.on_global_key_release)
                print("✅ Global capture setup complete")
            except Exception as e:
                print(f"⚠️  Global listener setup failed: {e}")
                self.global_listener = None
            
        except Exception as e:
            print(f"❌ Failed to setup global capture: {e}")
            self.global_listener = None
            self.mini_overlay = MiniOverlay(self.analytics) if not hasattr(self, 'mini_overlay') else self.mini_overlay
            if self.mini_overlay:
                self.mini_overlay.hide()

    def on_global_key_press(self, code: str):
        """Handle global key press efficiently"""
        timestamp = time.time() * 1000
        self.analytics.record_key_press(code, timestamp)
        
        # Handle overlay if enabled
        if self.overlay_enabled and self.mini_overlay:
            # Queue the key press instead of immediate handling
            self.mini_overlay.handle_key_press(code)
            
    def on_global_key_release(self, code: str):
        """Handle global key release efficiently"""
        timestamp = time.time() * 1000
        self.analytics.record_key_release(code, timestamp)
        
        # Handle overlay if enabled
        if self.overlay_enabled and self.mini_overlay:
            # Queue the key release instead of immediate handling
            self.mini_overlay.handle_key_release(code)

    def toggle_overlay(self, enabled: bool):
        """Toggle overlay functionality - CRASH-SAFE VERSION"""
        print(f"🔄 Toggle overlay: {enabled}")
        self.overlay_enabled = enabled
        
        if enabled:
            # Show overlay first (this should always work)
            if self.mini_overlay:
                try:
                    self.mini_overlay.show()
                    self.mini_overlay.raise_()
                    print("✅ Overlay shown")
                except Exception as e:
                    print(f"❌ Failed to show overlay: {e}")
                    return
            
            # Try to start global capture (this might fail)
            if self.global_listener:
                try:
                    print("🎯 Attempting to start global listener...")
                    success = self.global_listener.start_listening()
                    if success:
                        print("🚀 Global capture start initiated")
                    else:
                        print("❌ Global capture failed to start")
                except Exception as e:
                    print(f"❌ Exception starting global listener: {e}")
                    print("❌ This usually means accessibility permissions are missing")
                    self.show_permission_dialog()
            else:
                print("⚠️  No global listener available")
                
        else:
            # Disable overlay
            if self.mini_overlay:
                try:
                    self.mini_overlay.hide()
                    print("✅ Overlay hidden")
                except Exception as e:
                    print(f"❌ Error hiding overlay: {e}")
                    
            if self.global_listener:
                try:
                    self.global_listener.stop_listening()
                    print("✅ Global capture stopped")
                except Exception as e:
                    print(f"❌ Error stopping global listener: {e}")

    def show_permission_dialog(self):
        """Show permission instructions"""
        import sys
        print("\n" + "="*60)
        print("🔒 ACCESSIBILITY PERMISSIONS REQUIRED")
        print("="*60)
        print("1. Open System Preferences")
        print("2. Go to Security & Privacy → Privacy → Accessibility")
        print("3. Click the lock icon and enter your password")
        print("4. Click + and add this Python executable:")
        print(f"   📁 {sys.executable}")
        print("5. Make sure the checkbox is checked ✅")
        print("6. Restart this app")
        print("="*60 + "\n")

    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.overlay_enabled and self.mini_overlay:
                self.mini_overlay.show()
                self.mini_overlay.raise_()
            elif self.mini_overlay:
                self.mini_overlay.hide()
        super().changeEvent(event)

    def save_analytics(self):
        """Save analytics to JSON file"""
        if self.analytics.total_keystrokes > 0:  # Only save if there's data
            self.analytics.save_to_json()

    def closeEvent(self, event):
        """Save analytics when closing the application"""
        self.save_analytics()
        event.accept()
        # Clean up global listener
        if hasattr(self, 'global_listener'):
            self.global_listener.stop_listening()
        if hasattr(self, 'mini_overlay'):
            self.mini_overlay.close()
        

    def reset_analytics(self):
        """Reset analytics and clear JSON file"""
        self.analytics.reset()
        self.clear_button_focus()
        
    def change_keyboard_layout(self, text: str):
        layout_map = {
            "ANSI Alice Layout": "keychron",
            "ANSI 87-key": "marvo"
        }
        if text in layout_map:
            self.keyboard_widget.set_layout(layout_map[text])
        self.clear_button_focus()
        
    def adjust_scale(self, delta: float):
        current_scale = self.keyboard_widget.scale_factor
        new_scale = max(0.3, min(1.5, current_scale + delta))
        self.keyboard_widget.set_scale_factor(new_scale)
        self.clear_button_focus()
        
    def clear_button_focus(self):
        """Clear focus from all buttons to prevent spacebar activation"""
        # Clear focus from all focusable widgets
        for widget in self.findChildren(QPushButton):
            widget.clearFocus()
        for widget in self.findChildren(QComboBox):
            widget.clearFocus()
        for widget in self.findChildren(QCheckBox):  # Add this line
            widget.clearFocus()
        
        # Set focus to keyboard widget and ensure it's active
        self.keyboard_widget.setFocus(Qt.FocusReason.OtherFocusReason)
        self.keyboard_widget.activateWindow()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("TypeChron Viz")
        title.setStyleSheet("""
            QLabel {
                color: #ff7e5f;
                font-size: 42px;
                font-weight: 700;
            }
        """)
        
        subtitle = QLabel("Visualize typing on multiple keyboard layouts")
        subtitle.setStyleSheet("""
            QLabel {
                color: #ddd;
                font-size: 18px;
                margin-top: 5px;
            }
        """)
        
        # Global overlay toggle
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()

        self.overlay_toggle = QCheckBox("Enable Global Overlay")
        self.overlay_toggle.setFocusPolicy(Qt.FocusPolicy.ClickFocus)  # Add this line
        self.overlay_toggle.setStyleSheet("""
            QCheckBox {
                color: #ddd;
                font-size: 14px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid #5a5a5a;
                background-color: rgba(80, 80, 80, 0.3);
            }
            QCheckBox::indicator:checked {
                background-color: #ff7e5f;
                border-color: #ff7e5f;
            }
        """)
        self.overlay_toggle.toggled.connect(self.toggle_overlay)

        toggle_layout.addWidget(self.overlay_toggle)
        toggle_layout.addStretch()

        main_layout.addLayout(toggle_layout)

        header_widget = QWidget()
        header_layout_v = QVBoxLayout(header_widget)
        header_layout_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout_v.addWidget(title)
        header_layout_v.addWidget(subtitle)
        
        header_layout.addStretch()
        header_layout.addWidget(header_widget)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # Keyboard selection
        keyboard_layout = QHBoxLayout()
        keyboard_layout.addStretch()
        
        layout_selector = QComboBox()
        layout_selector.addItems(["ANSI Alice Layout", "ANSI 87-key"])
        layout_selector.currentTextChanged.connect(self.change_keyboard_layout)
        # Prevent focus retention
        layout_selector.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        layout_selector.setStyleSheet("""
            QComboBox {
                background: rgba(80, 80, 80, 0.3);
                color: white;
                border: 1px solid #5a5a5a;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 16px;
            }
            QComboBox:hover {
                background: rgba(100, 100, 100, 0.4);
                border-color: #ff7e5f;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        
        keyboard_layout.addWidget(layout_selector)
        keyboard_layout.addStretch()
        
        main_layout.addLayout(keyboard_layout)
        
        # Keyboard visualization
        keyboard_container = QHBoxLayout()
        keyboard_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.keyboard_widget = KeyboardWidget()
        self.keyboard_widget.key_pressed.connect(self.on_key_press)
        self.keyboard_widget.key_released.connect(self.on_key_release)
        
        # Keyboard background
        keyboard_frame = QFrame()
        keyboard_frame.setStyleSheet("""
            QFrame {
                background-color: #3a3a3a;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        keyboard_frame_layout = QHBoxLayout(keyboard_frame)
        keyboard_frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        keyboard_frame_layout.addWidget(self.keyboard_widget)
        
        keyboard_container.addWidget(keyboard_frame)
        main_layout.addLayout(keyboard_container)
        
        # Scale controls
        scale_layout = QHBoxLayout()
        scale_layout.addStretch()
        
        scale_label = QLabel("Scale:")
        scale_label.setStyleSheet("color: #ddd; font-size: 14px;")
        
        scale_buttons_layout = QHBoxLayout()
        
        scale_down_btn = QPushButton("-")
        scale_down_btn.clicked.connect(lambda: self.adjust_scale(-0.1))
        scale_down_btn.setFixedSize(30, 30)
        # Prevent focus retention
        scale_down_btn.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        
        scale_up_btn = QPushButton("+")
        scale_up_btn.clicked.connect(lambda: self.adjust_scale(0.1))
        scale_up_btn.setFixedSize(30, 30)
        # Prevent focus retention
        scale_up_btn.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        
        for btn in [scale_down_btn, scale_up_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: #5a5a5a;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #6a6a6a;
                }
                QPushButton:pressed {
                    background: #4a4a4a;
                }
            """)
        
        scale_buttons_layout.addWidget(scale_down_btn)
        scale_buttons_layout.addWidget(scale_up_btn)
        
        scale_layout.addWidget(scale_label)
        scale_layout.addLayout(scale_buttons_layout)
        scale_layout.addStretch()
        
        main_layout.addLayout(scale_layout)
        
        # Analytics panel
        self.analytics_panel = AnalyticsPanel(self.analytics)
        
        # Create a container to add some spacing
        analytics_container = QWidget()
        analytics_layout = QVBoxLayout(analytics_container)
        analytics_layout.setContentsMargins(20, 10, 20, 20)  # Reduced margins
        analytics_layout.addWidget(self.analytics_panel)
        
        main_layout.addWidget(analytics_container)
        
        # Reset button
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        
        reset_btn = QPushButton("Reset Analytics")
        reset_btn.clicked.connect(self.reset_analytics)
        # Prevent focus retention
        reset_btn.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #ff7e5f;
                color: white;
                border: none;
                padding: 14px 30px;
                border-radius: 30px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #ff6a4a;
            }
            QPushButton:pressed {
                background: #e5563a;
            }
        """)
        
        reset_layout.addWidget(reset_btn)
        reset_layout.addStretch()
        
        main_layout.addLayout(reset_layout)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2a2a2a, stop:1 #1a1a1a);
                color: #f0f0f0;
            }
            QWidget {
                color: #f0f0f0;
            }
        """)
        
        # Set initial focus to keyboard
        self.keyboard_widget.setFocus()
        
    def on_key_press(self, code: str):
        print(f"MainWindow.on_key_press called with code: {code}")
        timestamp = time.time() * 1000
        self.analytics.record_key_press(code, timestamp)
        
        # Clear focus from buttons when typing starts
        self.clear_button_focus()
        
        # ALWAYS trigger overlay when enabled (whether global capture works or not)
        if self.overlay_enabled and self.mini_overlay:
            print(f"Overlay enabled, sending {code} to mini overlay")
            self.mini_overlay.handle_key_press(code)
        else:
            print(f"Overlay not enabled or mini_overlay is None. overlay_enabled={self.overlay_enabled}, mini_overlay={self.mini_overlay}")
            
    def on_key_release(self, code: str):
        print(f"MainWindow.on_key_release called with code: {code}")
        timestamp = time.time() * 1000
        self.analytics.record_key_release(code, timestamp)
        
        # ALWAYS trigger overlay when enabled (whether global capture works or not)
        if self.overlay_enabled and self.mini_overlay:
            print(f"Overlay enabled, releasing {code} in mini overlay")
            self.mini_overlay.handle_key_release(code)
        
    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress and not event.isAutoRepeat():
            code = self.keyboard_widget.qt_key_to_web_code(event.key(), event.text())
            if code:
                self.clear_button_focus()  # Add this line
                self.keyboard_widget.handle_key_press(code)
        elif event.type() == event.Type.KeyRelease and not event.isAutoRepeat():
            code = self.keyboard_widget.qt_key_to_web_code(event.key(), event.text())
            if code:
                self.keyboard_widget.handle_key_release(code)
        
        return super().eventFilter(obj, event)


def main():
    import sys
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Keyboard Analytics")
    app.setOrganizationName("TypeChron")
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()