
"""
Created on Sat Jun 28 11:11:00 2025

@author: EE22B042 Jaiveer Kiran S K
"""

# %%

import re
from pathlib import Path
import subprocess
import calculation

# === CONFIGURATION ===
ltspice_path = r"C:\Program Files\ADI\LTspice\LTspice.exe"
original_file = Path(r"C:\Users\Dr. Senthilkumar\bandgap\project1.txt")
new_file = original_file.with_name("project1.txt")

# === VALUES TO MODIFY ========================================================
resistor_values = {
    "R1": calculation.R1_val,
    "R2": calculation.R2_val,
    "R3": calculation.R2_val,
    "R4": calculation.R3_val
}

mos_m_values = {
    "M1": calculation.fingers_branch,
    "M2": calculation.fingers_branch,
    "M3": calculation.fingers_OTAP,
    "M4": calculation.fingers_OTAP,
    "M5": calculation.fingers_OTAN,
    "M6": calculation.fingers_OTAN,
    "M7": calculation.fingers_branch,
    "M8": calculation.fingers_bias,
    "M11": calculation.fingers_tail
}

# === READ ORIGINAL FILE ======================================================
with open(original_file, "r") as f:
    lines = f.readlines()

new_lines = []

for line in lines:
    # --- Replace resistor values ---
    for res_name, new_val in resistor_values.items():
        pattern = rf"^{res_name}\s+[\w\d]+\s+[\w\d]+\s+[\d.eE+-]+"
        if re.match(pattern, line):
            parts = line.split()
            parts[-1] = str(new_val)
            line = " ".join(parts) + "\n"

    # --- Replace m values in MOSFET lines ---
    for mos_name, new_m in mos_m_values.items():
        if line.startswith(mos_name):
            line = re.sub(r"m=\d+", f"m={new_m}", line)

    new_lines.append(line)

# === WRITE TO NEW FILE =======================================================
with open(new_file, "w") as f:
    f.writelines(new_lines)


# === RUN LTspice (optional) ==================================================
subprocess.call([ltspice_path, "-b", str(new_file)])


# %%
import LTspy3
import matplotlib.pyplot as plt

sd = LTspy3.SimData('project1.raw')
name = sd.variables
dc_op_sweep = sd.values
Voltage = dc_op_sweep[10]
print('Output voltage at 28 degrees :',Voltage[7])
print('range of Output Reference Voltage obtained:',(max(Voltage)- min(Voltage)) * 1000,'mV')
print('Max current used :',(-dc_op_sweep[60][-1]) * 1e06, 'uA')
#===PLOTS======================================================================
x = dc_op_sweep[0]    
y = dc_op_sweep[10]

plt.plot(x, y)
plt.xlabel("Temperature")
plt.ylabel("Output Voltage")
plt.title("Plot")
plt.grid(True)
plt.show()

#==============================================================================












