#!/usr/bin/python
#
# This script generates the scrcpy binary "manually" (without gradle).
#
# Adapt Android platform and build tools versions (via ANDROID_PLATFORM and
# ANDROID_BUILD_TOOLS environment variables).
#
# Then execute:
#
#     BUILD_DIR=my_build_dir ./build_without_gradle.sh

import os

os.system('adb push build/scrcpy-server /data/local/tmp')

run_command = f'\
adb shell \
CLASSPATH=/data/local/tmp/scrcpy-server \
app_process / com.genymobile.scrcpy.Server \
2.0 \
'
os.system(run_command)