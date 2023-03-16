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


# Config
SCRCPY_DEBUG        = 'true'
SCRCPY_VERSION_NAME = '2.0'
BUILD_TOOLS         = '33.0.0'
PLATFORM            = 33
BUILD_DIR_NAME      = 'build'


def error(msg):
    print(msg)
    exit()


ANDROID_SDK_ROOT = os.environ.get('ANDROID_SDK_ROOT', None)
if not ANDROID_SDK_ROOT:
    error("need ANDROID_SDK_ROOT")
ANDROID_HOME = ANDROID_SDK_ROOT

BUILD_TOOLS_DIR = f"{ANDROID_HOME}/build-tools/{BUILD_TOOLS}"

SERVER_DIR    = os.path.abspath(os.path.dirname(__file__))
BUILD_DIR     = os.path.join(SERVER_DIR, BUILD_DIR_NAME)
CLASSES_DIR   = os.path.join(BUILD_DIR, "classes")
GEN_DIR       = f'{BUILD_DIR}/gen'
SERVER_BINARY = 'scrcpy-server'
ANDROID_JAR   = f'{ANDROID_HOME}/platforms/android-{PLATFORM}/android.jar'
LAMBDA_JAR    = f'{BUILD_TOOLS_DIR}/core-lambda-stubs.jar'

print(f"Platform: android-{PLATFORM}")
print(f"Build-tools: {BUILD_TOOLS}")
print(f"Build dir: {BUILD_DIR}")

for f in [CLASSES_DIR, GEN_DIR, f'{BUILD_DIR}/{SERVER_BINARY}', f'{BUILD_DIR}/classes.dex']:
    try:
        os.removedirs(f)
    except: pass
try:
    os.makedirs(f"{CLASSES_DIR}")
except: pass
try:
    os.makedirs(f"{GEN_DIR}/com/genymobile/scrcpy")
except: pass


with open(f"{GEN_DIR}/com/genymobile/scrcpy/BuildConfig.java", "w+") as f:
    f.write(f'''\
    package com.genymobile.scrcpy;

    public final class BuildConfig {{
        public static final boolean DEBUG = {SCRCPY_DEBUG};
        public static final String VERSION_NAME = "{SCRCPY_VERSION_NAME}";
    }}
    ''')

print("Generating java from aidl...")
os.chdir(f"{SERVER_DIR}/src/main/aidl")
os.system(f'"{BUILD_TOOLS_DIR}/aidl" -o {GEN_DIR} android/view/IRotationWatcher.aidl')
os.system(f'"{BUILD_TOOLS_DIR}/aidl" -o {GEN_DIR} android/content/IOnPrimaryClipChangedListener.aidl')

print("Compiling java sources...")
os.chdir("../java")
os.system(f' \
javac -encoding UTF-8 -bootclasspath "{ANDROID_JAR}" -cp "{LAMBDA_JAR};{GEN_DIR}" -d "{CLASSES_DIR}" \
    -source 1.8 -target 1.8 \
    com/genymobile/scrcpy/*.java \
    com/genymobile/scrcpy/wrappers/*.java \
')

print("Dexing...")
os.chdir(CLASSES_DIR)
if int(PLATFORM) < 31:
    # use dx
    cmd = f'"{BUILD_TOOLS_DIR}/dx" --dex --output "{BUILD_DIR}/classes.dex" \
        android/view/*.class \
        android/content/*.class \
        com/genymobile/scrcpy/*.class \
        com/genymobile/scrcpy/wrappers/*.class '
    os.system(cmd)

    print("Archiving...")
    os.chdir(BUILD_DIR)
    os.system(f'jar cvf "{SERVER_BINARY}" classes.dex')
else:
    # use d8
    cmd = f'"{BUILD_TOOLS_DIR}/d8" --classpath {ANDROID_JAR} \
        --output {BUILD_DIR}/classes.zip \
        android/view/*.class \
        android/content/*.class \
        com/genymobile/scrcpy/*.class \
        com/genymobile/scrcpy/wrappers/*.class '
    os.system(cmd)

    os.chdir(BUILD_DIR)
    os.remove(SERVER_BINARY)
    os.rename('classes.zip', SERVER_BINARY)
    os.system(f'jar xf "{SERVER_BINARY}"')


print(f"Server generated in {BUILD_DIR}/{SERVER_BINARY}")
