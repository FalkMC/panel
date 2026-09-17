import subprocess
import glob
import shutil
import re

# Locate available Java
def find_java():
    candidates = []
    path_java = shutil.which("java")
    if path_java:
        candidates.append(path_java)

    common_patterns = [
        "C:/Program Files/Java/jdk-*/bin/java.exe",
        "C:/Program Files/Java/jre-*/bin/java.exe",
        "C:/Program Files/Java/jdk*/bin/java.exe",
        "C:/Program Files/Java/jre*/bin/java.exe",
        "C:/Program Files (x86)/Java/jdk*/bin/java.exe",
        "C:/Program Files (x86)/Java/jre*/bin/java.exe",
        "C:/Program Files/Eclipse Adoptium/jdk-*/bin/java.exe",
        "C:/Program Files/Temurin/jdk-*/bin/java.exe",
        "C:/Program Files/AdoptOpenJDK/jdk-*/bin/java.exe",
        "C:/Program Files/OpenJDK/openjdk-*/bin/java.exe",
        "C:/Program Files/Amazon Corretto/jdk*/bin/java.exe",
        "C:/Program Files/ojdkbuild/java-*/bin/java.exe",
    ]
    for pattern in common_patterns:
        matches = glob.glob(pattern)
        candidates.extend(matches)

    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)

    best_version = None
    best_path = None
    for java_path in unique_candidates:
        version = get_java_version(java_path)
        if version:
            major = version[0]
            if best_version is None or major > best_version[0]:
                best_version = version
                best_path = java_path
            elif major == best_version[0] and (
                version[1] > best_version[1]
                or (version[1] == best_version[1] and version[2] > best_version[2])
            ):
                best_version = version
                best_path = java_path

    return best_path


# Return (major, minor, patch) as ints, or none if it cant be determined
def get_java_version(java_path):
    try:
        result = subprocess.run([java_path, "-version"], capture_output=True, text=True)
        output = result.stderr.strip()

        match = re.search(r'version "(\d+)\.(\d+)\.(\d+)"', output)
        if match:
            return tuple(map(int, match.groups()))

        match = re.search(r'version "1\.(\d+)\.(\d+)_(\d+)"', output)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))

        match = re.search(r'(\d+)\.(\d+)\.(\d+)', output)
        if match:
            return tuple(map(int, match.groups()))

        return None
    except Exception:
        return None
