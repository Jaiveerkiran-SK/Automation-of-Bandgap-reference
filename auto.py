import os
import sys

choice = "n" #input("Want power optimisation ? y/n: ").strip().lower()

if choice == "n":
    print("Switching to autoband.py ...")
    os.system(f"{sys.executable} autoband.py")  # runs other.py using same Python interpreter
    sys.exit()  # stop main.py after switching
else:
    print("Switching to autoband_power.py...")
    os.system(f"{sys.executable} autoband_power.py")  # runs other.py using same Python interpreter
    sys.exit()

