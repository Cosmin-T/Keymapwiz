#!/bin/bash
# Fix for "app is damaged" error on macOS
echo "Removing quarantine attribute from Typechron Viz.app..."
xattr -d com.apple.quarantine "/Applications/Typechron Viz.app"
echo "Done! Try opening the app now."