
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
                    print("KEY: \(keyString)")
                    fflush(stdout)
                } else if type == .keyUp {
                    let keyCode = event.getIntegerValueField(.keyboardEventKeycode)
                    let keyString = GlobalKeyMonitor.keyCodeToString(keyCode: keyCode)
                    print("RELEASE: \(keyString)")
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

        return keyMap[keyCode] ?? "Unknown\(keyCode)"
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
                print("KEY: \(keyString)")
                fflush(stdout)
            } else {
                print("RELEASE: \(keyString)")
                fflush(stdout)
            }
        }

        if changedFlags.contains(.maskControl) {
            // Detect left vs right control based on keyCode
            let keyString = (keyCode == 59) ? "ControlLeft" : "ControlRight"
            
            if currentFlags.contains(.maskControl) {
                print("KEY: \(keyString)")
                fflush(stdout)
            } else {
                print("RELEASE: \(keyString)")
                fflush(stdout)
            }
        }

        if changedFlags.contains(.maskAlternate) {
            // Detect left vs right alt based on keyCode
            let keyString = (keyCode == 58) ? "AltLeft" : "AltRight"
            
            if currentFlags.contains(.maskAlternate) {
                print("KEY: \(keyString)")
                fflush(stdout)
            } else {
                print("RELEASE: \(keyString)")
                fflush(stdout)
            }
        }

        if changedFlags.contains(.maskCommand) {
            // Detect left vs right command based on keyCode
            let keyString = (keyCode == 55) ? "MetaLeft" : "MetaRight"
            
            if currentFlags.contains(.maskCommand) {
                print("KEY: \(keyString)")
                fflush(stdout)
            } else {
                print("RELEASE: \(keyString)")
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
