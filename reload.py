import os
import subprocess

subprocess.run(["python", "main.py"])
os.system("kill -9 $(pgrep -f 'python main.py')")