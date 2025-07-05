const { app, BrowserWindow, ipcMain, systemPreferences, screen } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow;
let overlayWindow = null;
let globalKeyListener = null;
let macKeyCaptureProc = null;
let isGlobalTrackingEnabled = false;

// Analytics data storage
const analyticsFile = path.join(__dirname, 'key_analytics.json');

// Load analytics data
function loadAnalytics() {
  try {
    if (fs.existsSync(analyticsFile)) {
      const data = fs.readFileSync(analyticsFile, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Error loading analytics:', error);
  }
  return [];
}

// Save analytics data
function saveAnalytics(data) {
  try {
    fs.writeFileSync(analyticsFile, JSON.stringify(data, null, 4));
  } catch (error) {
    console.error('Error saving analytics:', error);
  }
}

// Global Key Detection System
function setupGlobalKeyListener() {
  console.log('=== SETUP GLOBAL KEY LISTENER ===');
  console.log('Platform:', process.platform);

  if (process.platform === 'darwin') {
    // macOS - requires accessibility permissions
    const result = setupMacGlobalKeys();
    console.log('setupMacGlobalKeys returned:', result);
    return result;
  } else if (process.platform === 'win32') {
    // Windows - use node-global-key-listener or similar
    const result = setupWindowsGlobalKeys();
    console.log('setupWindowsGlobalKeys returned:', result);
    return result;
  } else {
    // Linux/other
    const result = setupLinuxGlobalKeys();
    console.log('setupLinuxGlobalKeys returned:', result);
    return result;
  }
}

function setupMacGlobalKeys() {
  // Check for accessibility permissions with detailed logging
  console.log('=== PERMISSION CHECK ===');
  console.log('App name:', app.getName());
  console.log('App path:', app.getPath('exe'));

  const isTrusted = systemPreferences.isTrustedAccessibilityClient(false);
  console.log('Current permission status:', isTrusted);

  if (!isTrusted) {
    console.log("Requesting accessibility permissions for global key tracking...");
    console.log("You need to grant permission to:", app.getName());

    // Request permission and show dialog
    const granted = systemPreferences.isTrustedAccessibilityClient(true);
    console.log("Permission request result:", granted);

    if (!granted) {
      console.log("❌ PERMISSION DENIED");
      console.log("Go to: System Preferences → Security & Privacy → Privacy → Accessibility");
      console.log("Look for and enable:", app.getName());
      return false;
    }
  }

  console.log("✅ PERMISSION GRANTED");
  // ... rest of the function stays the same

  // Create Swift key capture process
  const swiftScript = path.join(__dirname, 'mac_key_capture.swift');

  // Always regenerate Swift script to ensure latest version with modifier key support
  createMacKeyScript(swiftScript);

  try {
    macKeyCaptureProc = spawn('swift', [swiftScript]);

    macKeyCaptureProc.stdout.on('data', (data) => {
      const lines = data.toString().split('\n');
      for (const line of lines) {
        if (line.startsWith('KEY:')) {
          const keyCode = line.split(' ')[1];
          handleGlobalKeyPress(keyCode);
        } else if (line.startsWith('RELEASE:')) {
          const keyCode = line.split(' ')[1];
          handleGlobalKeyRelease(keyCode);
        }
      }
    });

    macKeyCaptureProc.stderr.on('data', (data) => {
      console.error('Mac key capture error:', data.toString());
    });

    macKeyCaptureProc.on('exit', (code) => {
      console.log('Mac key capture process exited with code:', code);
      macKeyCaptureProc = null;
    });

    console.log("Global key tracking enabled for macOS");
    return true;
  } catch (error) {
    console.error('Failed to start Mac key capture:', error);
    return false;
  }
}

function setupWindowsGlobalKeys() {
  try {
    // Try to use node-global-key-listener or similar package
    // This would need to be installed: npm install node-global-key-listener
    const GlobalKeyboardListener = require("node-global-key-listener").GlobalKeyboardListener;

    globalKeyListener = new GlobalKeyboardListener();

    globalKeyListener.addListener((e, down) => {
      if (down) { // Only track key presses, not releases
        handleGlobalKeyPress(e.name);
      }
    });

    console.log("Global key tracking enabled for Windows");
    return true;
  } catch (error) {
    console.error('Global key listener not available for Windows:', error);
    console.log('Install with: npm install node-global-key-listener');
    return false;
  }
}

function setupLinuxGlobalKeys() {
  try {
    // For Linux, you might use ioHook or similar
    // This is a placeholder - actual implementation would depend on the specific solution
    console.log("Global key tracking for Linux not implemented yet");
    return false;
  } catch (error) {
    console.error('Failed to setup Linux global keys:', error);
    return false;
  }
}

function createMacKeyScript(scriptPath) {
  const swiftCode = `
import Cocoa
import Carbon
import Foundation

class GlobalKeyMonitor {
    var eventTap: CFMachPort?

    init() {
        // Flush stdout immediately
        setbuf(stdout, nil)

        let eventMask = (1 << CGEventType.keyDown.rawValue) | (1 << CGEventType.keyUp.rawValue) | (1 << CGEventType.flagsChanged.rawValue)

        eventTap = CGEvent.tapCreate(
            tap: .cgSessionEventTap,
            place: .headInsertEventTap,
            options: .defaultTap,
            eventsOfInterest: CGEventMask(eventMask),
            callback: { (proxy, type, event, refcon) in
                if type == .keyDown {
                    let keyCode = event.getIntegerValueField(.keyboardEventKeycode)
                    let keyString = GlobalKeyMonitor.keyCodeToString(keyCode: keyCode)
                    print("KEY: \\(keyString)")
                    fflush(stdout)
                } else if type == .keyUp {
                    let keyCode = event.getIntegerValueField(.keyboardEventKeycode)
                    let keyString = GlobalKeyMonitor.keyCodeToString(keyCode: keyCode)
                    print("RELEASE: \\(keyString)")
                    fflush(stdout)
                } else if type == .flagsChanged {
                    let flags = event.flags
                    let keyCode = event.getIntegerValueField(.keyboardEventKeycode)

                    // Handle modifier key presses and releases based on flag changes
                    GlobalKeyMonitor.handleModifierFlags(flags: flags, keyCode: keyCode)
                }
                return Unmanaged.passUnretained(event)
            },
            userInfo: nil
        )

        guard let eventTap = eventTap else {
            print("ERROR: Failed to create event tap")
            fflush(stdout)
            return
        }

        let runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, eventTap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)
        CGEvent.tapEnable(tap: eventTap, enable: true)

        print("READY: Global key monitoring started")
        fflush(stdout)
    }

    static func keyCodeToString(keyCode: Int64) -> String {
        let keyMap: [Int64: String] = [
            0: "KeyA", 1: "KeyS", 2: "KeyD", 3: "KeyF", 4: "KeyH", 5: "KeyG", 6: "KeyZ", 7: "KeyX",
            8: "KeyC", 9: "KeyV", 11: "KeyB", 12: "KeyQ", 13: "KeyW", 14: "KeyE", 15: "KeyR",
            16: "KeyY", 17: "KeyT", 18: "Digit1", 19: "Digit2", 20: "Digit3", 21: "Digit4", 22: "Digit6",
            23: "Digit5", 24: "Equal", 25: "Digit9", 26: "Digit7", 27: "Minus", 28: "Digit8", 29: "Digit0",
            30: "BracketRight", 31: "KeyO", 32: "KeyU", 33: "BracketLeft", 34: "KeyI", 35: "KeyP",
            36: "Enter", 37: "KeyL", 38: "KeyJ", 39: "Quote", 40: "KeyK", 41: "Semicolon",
            42: "Backslash", 43: "Comma", 44: "Slash", 45: "KeyN", 46: "KeyM", 47: "Period",
            48: "Tab", 49: "Space", 50: "Backquote", 51: "Backspace", 53: "Escape",
            54: "MetaRight", 55: "MetaLeft", 56: "ShiftLeft", 57: "CapsLock", 58: "AltLeft",
            59: "ControlLeft", 60: "ShiftRight", 61: "AltRight", 62: "ControlRight",
            63: "Function", 64: "F17", 65: "NumpadDecimal", 67: "NumpadMultiply", 69: "NumpadAdd",
            71: "NumpadClear", 72: "VolumeUp", 73: "VolumeDown", 74: "Mute", 75: "NumpadDivide",
            76: "NumpadEnter", 78: "NumpadSubtract", 79: "F18", 80: "F19", 81: "NumpadEqual",
            82: "Numpad0", 83: "Numpad1", 84: "Numpad2", 85: "Numpad3", 86: "Numpad4",
            87: "Numpad5", 88: "Numpad6", 89: "Numpad7", 91: "Numpad8", 92: "Numpad9",
            96: "F5", 97: "F6", 98: "F7", 99: "F3", 100: "F8", 101: "F9", 103: "F11",
            105: "F13", 106: "F16", 107: "F14", 109: "F10", 111: "F12", 113: "F15",
            114: "Help", 115: "Home", 116: "PageUp", 117: "Delete", 118: "F4", 119: "End",
            120: "F2", 121: "PageDown", 122: "F1", 123: "ArrowLeft", 124: "ArrowRight",
            125: "ArrowDown", 126: "ArrowUp"
        ]

        return keyMap[keyCode] ?? "Unknown\\(keyCode)"
    }

    static var previousFlags: CGEventFlags = []

    static func handleModifierFlags(flags: CGEventFlags, keyCode: Int64) {
        let currentFlags = flags
        let changedFlags = CGEventFlags(rawValue: currentFlags.rawValue ^ previousFlags.rawValue)

        // Check for each modifier key
        if changedFlags.contains(.maskShift) {
            // Detect left vs right shift based on keyCode
            let keyString = (keyCode == 56) ? "ShiftLeft" : "ShiftRight"

            if currentFlags.contains(.maskShift) {
                print("KEY: \\(keyString)")
                fflush(stdout)
            } else {
                print("RELEASE: \\(keyString)")
                fflush(stdout)
            }
        }

        if changedFlags.contains(.maskControl) {
            // Detect left vs right control based on keyCode
            let keyString = (keyCode == 59) ? "ControlLeft" : "ControlRight"

            if currentFlags.contains(.maskControl) {
                print("KEY: \\(keyString)")
                fflush(stdout)
            } else {
                print("RELEASE: \\(keyString)")
                fflush(stdout)
            }
        }

        if changedFlags.contains(.maskAlternate) {
            // Detect left vs right alt based on keyCode
            let keyString = (keyCode == 58) ? "AltLeft" : "AltRight"

            if currentFlags.contains(.maskAlternate) {
                print("KEY: \\(keyString)")
                fflush(stdout)
            } else {
                print("RELEASE: \\(keyString)")
                fflush(stdout)
            }
        }

        if changedFlags.contains(.maskCommand) {
            // Detect left vs right command based on keyCode
            let keyString = (keyCode == 55) ? "MetaLeft" : "MetaRight"

            if currentFlags.contains(.maskCommand) {
                print("KEY: \\(keyString)")
                fflush(stdout)
            } else {
                print("RELEASE: \\(keyString)")
                fflush(stdout)
            }
        }

        if changedFlags.contains(.maskAlphaShift) {
            if currentFlags.contains(.maskAlphaShift) {
                print("KEY: CapsLock")
                fflush(stdout)
            } else {
                print("RELEASE: CapsLock")
                fflush(stdout)
            }
        }

        previousFlags = currentFlags
    }

    deinit {
        if let eventTap = eventTap {
            CGEvent.tapEnable(tap: eventTap, enable: false)
            CFMachPortInvalidate(eventTap)
        }
    }
}

// Handle termination signals
signal(SIGINT) { _ in
    print("SHUTDOWN: Received SIGINT")
    fflush(stdout)
    exit(0)
}

signal(SIGTERM) { _ in
    print("SHUTDOWN: Received SIGTERM")
    fflush(stdout)
    exit(0)
}

let monitor = GlobalKeyMonitor()
CFRunLoopRun()
`;

  try {
    fs.writeFileSync(scriptPath, swiftCode);
    console.log('Created Mac key capture script with immediate stdout flushing');
  } catch (error) {
    console.error('Failed to create Mac key script:', error);
  }
}

function handleGlobalKeyPress(keyCode) {
  // Send to main window for analytics processing
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('global-key-press', keyCode);
  }

  // Send to overlay window for visual feedback
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send('global-key-press', keyCode);
  }
}

function handleGlobalKeyRelease(keyCode) {
  // Send to main window for analytics processing
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('global-key-release', keyCode);
  }

  // Send to overlay window for visual feedback
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send('global-key-release', keyCode);
  }
}

// Sync analytics data to overlay when it's updated in main window
function syncAnalyticsToOverlay(analyticsData) {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send('analytics-sync', analyticsData);
  }
}

function stopGlobalKeyListener() {
  if (process.platform === 'darwin' && macKeyCaptureProc) {
    macKeyCaptureProc.kill();
    macKeyCaptureProc = null;
  } else if (globalKeyListener) {
    globalKeyListener.destroy();
    globalKeyListener = null;
  }

  isGlobalTrackingEnabled = false;
  console.log("Global key tracking stopped");
}

// Create main window
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1450,
    height: 1300,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, 'icon.png'), // Optional icon
    show: false,
    titleBarStyle: 'hiddenInset', // Modern macOS style
    vibrancy: 'dark' // macOS vibrancy effect
  });

  mainWindow.loadFile('index.html');

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    // Send initial analytics data
    const analytics = loadAnalytics();
    mainWindow.webContents.send('analytics-loaded', analytics);
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Create overlay window
function createOverlayWindow() {
  if (overlayWindow) {
    overlayWindow.show();
    return;
  }

  // Calculate position for lower right corner
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;
  const overlayWidth = 400;
  const overlayHeight = 180;
  const padding = 20; // Distance from screen edge

  const x = screenWidth - overlayWidth - padding;
  const y = screenHeight - overlayHeight - padding;

  overlayWindow = new BrowserWindow({
    width: overlayWidth,
    height: overlayHeight,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    frame: false,
    alwaysOnTop: true,
    transparent: true,
    skipTaskbar: true,
    resizable: false,
    minimizable: false,
    maximizable: false,
    movable: true,
    show: false,
    x: x,
    y: y
  });

  overlayWindow.loadFile('overlay.html');

  overlayWindow.once('ready-to-show', () => {
    overlayWindow.show();

    // Enhanced stay-on-top for macOS
    if (process.platform === 'darwin') {
      overlayWindow.setAlwaysOnTop(true, 'floating');
      overlayWindow.setVisibleOnAllWorkspaces(true);
    }

    // Send initial analytics data to overlay
    const analytics = loadAnalytics();
    overlayWindow.webContents.send('analytics-loaded', analytics);
  });

  overlayWindow.on('closed', () => {
    overlayWindow = null;
  });

  // Overlay is now draggable and interactive (removed click-through behavior)
}

// Hide overlay window
function hideOverlayWindow() {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.hide();
  }
}

// Destroy overlay window
function destroyOverlayWindow() {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.close();
    overlayWindow = null;
  }
}

// IPC Handlers
ipcMain.handle('load-analytics', () => {
  return loadAnalytics();
});

ipcMain.handle('save-analytics', (event, data) => {
  saveAnalytics(data);
});

ipcMain.handle('toggle-global-tracking', (event, enabled) => {
  console.log('=== IPC TOGGLE-GLOBAL-TRACKING ===');
  console.log('Requested state:', enabled);
  console.log('Current state:', isGlobalTrackingEnabled);

  if (enabled) {
    console.log('Attempting to enable global tracking...');
    const success = setupGlobalKeyListener();
    console.log('setupGlobalKeyListener returned:', success);

    if (success) {
      isGlobalTrackingEnabled = true;

      // Minimize main window and show overlay
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.minimize();
      }
      createOverlayWindow();

      console.log("✅ Global tracking enabled with overlay - returning success");
      return { success: true, message: "Global tracking enabled" };
    } else {
      console.log("❌ Global tracking failed - returning failure");
      return { success: false, message: "Failed to enable global tracking. Check permissions." };
    }
  } else {
    console.log('Disabling global tracking...');
    stopGlobalKeyListener();

    // Hide overlay and restore main window
    destroyOverlayWindow();
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.restore();
      mainWindow.show();
    }

    console.log("✅ Global tracking disabled - returning success");
    return { success: true, message: "Global tracking disabled" };
  }
});

ipcMain.handle('check-global-permissions', () => {
  if (process.platform === 'darwin') {
    const isTrusted = systemPreferences.isTrustedAccessibilityClient(false);
    return {
      hasPermission: isTrusted,
      platform: 'macOS',
      // message: isTrusted ? 'Accessibility permissions granted' : 'Accessibility permissions required'
    };
  } else if (process.platform === 'win32') {
    // Windows doesn't require special permissions for global key listening
    return {
      hasPermission: true,
      platform: 'Windows',
      message: 'No special permissions required'
    };
  } else {
    return {
      hasPermission: false,
      platform: process.platform,
      message: 'Global tracking not supported on this platform yet'
    };
  }
});


// Note: Removed overlay mouse event handling since overlay is now fully interactive

// Sync analytics from main window to overlay
ipcMain.on('sync-analytics-to-overlay', (event, data) => {
  syncAnalyticsToOverlay(data);
});

// Toggle main window visibility from overlay
ipcMain.on('restore-main-window', () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isVisible()) {
      // If visible, hide it
      mainWindow.hide();
    } else {
      // If hidden, show it
      mainWindow.show();
      mainWindow.focus();
    }
  }
});

// Exit application from overlay
ipcMain.on('exit-application', () => {
  // Clean shutdown
  stopGlobalKeyListener();
  destroyOverlayWindow();

  // Close main window and quit
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.close();
  }

  app.quit();
});

// App event handlers
app.whenReady().then(() => {
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  // Clean shutdown
  stopGlobalKeyListener();
  destroyOverlayWindow();
  console.log('Application shutting down...');
});