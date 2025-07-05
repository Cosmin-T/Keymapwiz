# Typechron Viz - Keyboard Analytics Visualization App

A real-time keyboard analytics application built with Electron that tracks typing patterns, visualizes key usage, and provides detailed typing statistics.

## Features

- **Real-time Key Tracking**: Monitor global keyboard activity with system-wide key capture
- **Visual Analytics**: Interactive charts showing typing patterns and key frequency
- **Overlay Mode**: Minimalist floating overlay for unobtrusive monitoring
- **Cross-platform**: Works on macOS, Windows, and Linux
- **Privacy-focused**: All data stays local on your machine

## Installation

### From DMG (macOS)
1. Download the latest `Typechron Viz-1.0.0.dmg` from the releases
2. Open the DMG file
3. Drag the app to your Applications folder
4. Launch from Applications

### From Source
```bash
git clone <repository-url>
cd typechron-viz
npm install
npm start
```

## Building

### Prerequisites
- Node.js 16 or later
- npm or yarn

### Development
```bash
npm install
npm start
```

### Building for Distribution

#### macOS
```bash
npm run build:mac
```
This creates:
- `dist/Typechron Viz-1.0.0.dmg` - Universal DMG installer
- `dist/mac/` - x64 app bundle
- `dist/mac-arm64/` - ARM64 app bundle

#### Windows
```bash
npm run build:win
```

#### Linux
```bash
npm run build:linux
```

#### All Platforms
```bash
npm run build
```

## Usage

### Main Window
- View real-time typing statistics
- Analyze key frequency charts
- Monitor typing rhythm patterns
- Toggle global tracking on/off

### Overlay Mode
- Minimal floating display
- Always-on-top functionality
- Draggable positioning
- Quick access to main window

### Permissions (macOS)
On macOS, the app requires accessibility permissions for global key tracking:
1. Go to System Preferences → Security & Privacy → Privacy → Accessibility
2. Add and enable "Typechron Viz"
3. Restart the app if needed

## Data Privacy

All typing data is stored locally on your machine in `key_analytics.json`. No data is transmitted to external servers.

## Development

### File Structure
```
├── main.js           # Main Electron process
├── index.html        # Main window UI
├── overlay.html      # Overlay window UI
├── package.json      # App configuration
├── build/            # Build resources
└── dist/             # Built applications
```

### Scripts
- `npm start` - Run in development mode
- `npm run build` - Build for all platforms
- `npm run build:mac` - Build for macOS only
- `npm run build:win` - Build for Windows only
- `npm run build:linux` - Build for Linux only

## License

MIT License - see LICENSE file for details