const { execSync } = require('child_process');
const path = require('path');

// This is an afterPack hook for electron-builder
exports.default = async function(context) {
  const { appOutDir, electronPlatformName, arch } = context;
  
  if (electronPlatformName !== 'darwin') {
    return;
  }

  const appPath = path.join(appOutDir, 'Typechron Viz.app');
  console.log('Ad-hoc signing:', appPath);
  
  try {
    execSync(`codesign --force --deep --sign - "${appPath}"`, { stdio: 'inherit' });
    console.log('Successfully signed app');
  } catch (error) {
    console.error('Signing failed:', error.message);
    throw error;
  }
};