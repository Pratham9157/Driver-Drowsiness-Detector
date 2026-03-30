import subprocess
import sys
import os

src = os.path.join(os.path.dirname(__file__), "src")

server = subprocess.Popen([sys.executable, os.path.join(src, "server.py")])
detector = subprocess.Popen([sys.executable, os.path.join(src, "detector.py")])

try:
    server.wait()
    detector.wait()
except KeyboardInterrupt:
    server.terminate()
    detector.terminate()
