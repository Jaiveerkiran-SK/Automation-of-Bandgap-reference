import math
import numpy as np
import subprocess
import sys
import os
import random
import re
import spec


# Constants
k = 1.38e-23      # Boltzmann constant (J/K)
q = 1.6e-19       # Electron charge (C)
eta = 1.02        # Non-Ideality factor
n = 8             # Scaling factor
T = 27            # Temperature in Kelvin

#==========================================================================================================================================================
#current division:

power = spec.Max_power
V_dd = 1.2
Imax = power/spec.vdd
# 90 % of Imax is used to create the design
Idesign = 0.9 * Imax 
# 20 % current is allocated to opamp block and in that 10% for biasing and 90% for opamp branches                           
Iopamp = 0.2 * Idesign 
# 20 % current is allocated to opamp block and in that 10% for biasing and 90% for opamp branches                         
Iopamp_bias = 0.1 * Iopamp 
# There are 4 bias branches in opamp and since everyone carries same current                     
IBIAS = Iopamp_bias/4                           
print(f"Ibias:{IBIAS}")
# Here branch is for Core block there are 3 branches in it
Ibranch = ((0.8 * Idesign - 0.2*0.8*Idesign))/3                                            
Iopamp_branch = (Iopamp - Iopamp_bias)/2
#ERROR DIVISION: 10% of total error is Assumed due to inaccuracies in current mirroring and 90 % due to finite gain of opamp.
error_current_mirror = 0.1 * spec.error_percentage_vref
error_opamp = 0.9 * spec.error_percentage_vref

os.environ["CDS_LIC_FILE"] = "5280@ams98:5280@ams101:5280@ams91:1717@ams98"

inpfile3 = "diode.scs"
inpfile3_noext = os.path.splitext(inpfile3)[0]
inpfile3path = "./" + inpfile3_noext + ".scs"
inpfile3bckpath = "./" + inpfile3_noext + "_bk.scs"
inpfile3srcpath = "./" + inpfile3_noext + "_src.scs"
output_file3_dc = "./" + inpfile3_noext + "/psf/dc.dc"

with open(inpfile3path , 'r') as file:
    content = file.read()
with open(inpfile3bckpath , 'w') as file:
    file.write(content)
    
    
def run_spectre_sim_diode(ibias,inpfile,inpfile_noext,inpfilepath,inpfilebckpath):
    spectre_args = ["/cad/tools/cadencetools/SPECTRE191/tools.lnx86/bin/spectre",
         "-64",
         inpfile, "+escchars",
         "=log", "./"+inpfile_noext+"/psf/spectre.out",
         "-format", "psfascii",
         "-raw", "./"+inpfile_noext+"/psf",
         "+aps", "+mt",
         "+lqtimeout", "900",
         "-maxw","5",
         "-maxn","5",
         "+logstatus"]
     
    replacements = {'ibias':str(ibias)}
#CHANGING THE INPFILEPATH TO RUN SPECTRE
          
    try:
        with open(inpfilepath, 'r') as file:
            content = file.read()
        for old_word, new_word in replacements.items():
            content = content.replace(old_word,new_word,1)
        with open(inpfilepath, 'w') as file:
            file.write(content)
    except IOError as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

    print("Running Simulation...")
    subprocess.call(spectre_args)
    print("Simulation done.")

run_spectre_sim_diode(Ibranch,inpfile3,inpfile3_noext,inpfile3path,inpfile3bckpath)   

def get_CTAT(filename):
    temperature = []
    vdiode = []

    temp = None
    vbe = None

    with open(filename, 'r') as f:
        data_section = False
        for line in f:
            line = line.strip()

            # Start data section
            if line == "VALUE":
                data_section = True
                continue
            if not data_section:
                continue

            # Extract Id
            if line.startswith('"temp"'):
                parts = line.split()
                try:
                    temp = float(parts[1])
                except (IndexError, ValueError):
                    continue

            # Extract gm/Id
            elif line.startswith('"net1"'):
                parts = line.split()
                try:
                    vbe = float(parts[1])
                except (IndexError, ValueError):
                    continue

            # Once we have both, store them and reset
            if temp is not None and vbe is not None:
                temperature.append(temp)
                vdiode.append(vbe)
                temp = None
                current_gmoverid = None

    if not temperature or not vdiode:
        raise ValueError("No temperature or vdiode data found in file.")

    # Build lookup table {Id: gm/Id}
    lut = {temperature[i]: vdiode[i] for i in range(len(temperature))}
    CTAT_slope = (lut[125] - lut[-40])/165
    VBE30 = lut[30]
    VBEm40 = lut[-40]
    return CTAT_slope,VBE30,VBEm40
    
CTAT = get_CTAT(output_file3_dc)[0]
VBE30 = get_CTAT(output_file3_dc)[1]
VBEm40 = get_CTAT(output_file3_dc)[2]

I = Ibranch        # branch current of core

Vref = spec.reference_voltage       # Reference voltage (V)  to be generated = 500mV
Vthp_max = 0.35                     # PMOS threshold voltage (V) maximum occurs at low temperatures. (-40 degrees)
Vthp_min = 0.2                      # PMOS threshold voltage (V) minimum occurs at high temperatures. (125 degrees)
VDD = spec.vdd                      # Supply voltage (V)
margin = 0.050                      # Margin for VDSAT(V)
percent_error_vdd = spec.error_percentage_vdd     # 10% of VDD
percent_error_vref_mirror = error_current_mirror
percent_error_vref_opamp = error_opamp



# Equation for R2/R1 ratio
R2_R1 = -(CTAT) / ((k/q) * math.log(n) * eta)
print(f"R2/R1 ratio = {R2_R1:.3f}")
# Equation (2)
lhs = I
rhs_coeff = (k/q) * (273 + T) * math.log(n) * eta

# Solve for R1 and R2
R1 = (rhs_coeff + VBE30/R2_R1) / I
R2 = R2_R1 * R1
print(f"R1 = {R1:.2f} Ω")

# Equation (3) for R3
R3 = Vref / I
print(f"R2 = {R2:.2f} Ω")
print(f"R3 = {R3:.0f} Ω")

vdd_error = VDD * (percent_error_vdd/100)
vdsat_mirror = ((VDD - vdd_error - VBEm40)/2) # margin not included here because already available vdsat is much less from theoritical calculations
print(vdd_error)

# Inequality for (Vbias the one used for biasing CASCODE current mirror)
Vbias_min = Vref - Vthp_max
Vbias_max = VDD - 2*vdsat_mirror - Vthp_max

# Midpoint chosen for Vbias
Vbias_chosen = (Vbias_min + Vbias_max)/2

# ΔI calculation
dI = (Vref * (percent_error_vref_mirror/100) )/ R3   # ΔI = ΔVref / R3

Rout1 = (VBEm40 - Vref) / dI

gm_id_mirror = 2/vdsat_mirror


print(gm_id_mirror)
Vearly_sq = (Rout1 * I) / gm_id_mirror
Vearly_mirror = Vearly_sq**0.5

#opamp gain calculations
Verr = (((Vref * (percent_error_vref_opamp)/100)/((R3/R2)*(1+(R2/R1))))/2)
Vgate = VDD + vdd_error - (2/gm_id_mirror) - Vthp_min
A = Vgate/Verr
AdB = 20 * math.log10(A)

#opamp calculations
#setting up Vbias
vdsat_opamp = (((2/gm_id_mirror)+Vthp_min)/2)- margin
gm_id_opamp = 2/(vdsat_opamp)
print(f"GM over ID of Opamp :{gm_id_opamp}")
vearly_opamp = ((2 * A)**(0.5))/gm_id_opamp


# early voltage varies drastically from ideal cases( level-1 model) so to have more accurate values more accurate gate and drain voltages are chosen
#vgate = 0.9 vds = 0.6 temp = 27 for look up table nmos for early voltage 0.9 and 0.6 are rough values of voltages obtain from {{Simulation}}.
#Vgate = 0.9 vds = 0.6 temp = 27 for look up table pmos
#Length of device calculations
# Your NMOS and PMOS lookup tables
early_voltage_lut_nmos = {
    70.00E-9:2.560, 80.00E-9:2.900, 90.00E-9:3.170, 100.0E-9:3.379,
    110.0E-9:3.552, 120.0E-9:3.682, 130.0E-9:3.779, 140.0E-9:3.848,
    150.0E-9:3.897, 160.0E-9:3.928, 170.0E-9:3.946, 180.0E-9:3.953,
    190.0E-9:3.952, 200.0E-9:3.943
}

early_voltage_lut_pmos = {
    70.00E-9:592.0E-3, 80.00E-9:761.9E-3, 90.00E-9:933.8E-3, 100.0E-9:1.103,
    110.0E-9:1.247, 120.0E-9:1.388, 130.0E-9:1.522, 140.0E-9:1.650,
    150.0E-9:1.772, 160.0E-9:1.887, 170.0E-9:1.995, 180.0E-9:2.098,
    190.0E-9:2.195, 200.0E-9:2.287, 210.0E-9:2.375, 220.0E-9:2.459,
    230.0E-9:2.540, 240.0E-9:2.617, 250.0E-9:2.699, 260.0E-9:2.778,
    270.0E-9:2.854, 280.0E-9:2.928, 290.0E-9:3.000, 300.0E-9:3.070,
    310.0E-9:3.139, 320.0E-9:3.205, 330.0E-9:3.270, 340.0E-9:3.333,
    350.0E-9:3.395, 360.0E-9:3.455, 370.0E-9:3.514, 380.0E-9:3.572,
    390.0E-9:3.629, 400.0E-9:3.684, 410.0E-9:3.738, 420.0E-9:3.791,
    430.0E-9:3.843, 440.0E-9:3.894, 450.0E-9:3.944, 460.0E-9:3.993,
    470.0E-9:4.041, 480.0E-9:4.088, 490.0E-9:4.134, 500.0E-9:4.179
}

def find_length_from_va(lut, va_query):
    """Interpolates device length for a given Early Voltage Va."""
    lengths = np.array(list(lut.keys()))
    vas = np.array(list(lut.values()))
    return round((np.interp(va_query, vas, lengths))*1e09)

L_nmos_opamp = find_length_from_va(early_voltage_lut_nmos, vearly_opamp)
L_pmos_opamp = find_length_from_va(early_voltage_lut_pmos, vearly_opamp)
L_pmos_mirror = find_length_from_va(early_voltage_lut_pmos, Vearly_mirror)

#===============CURRENT MIRROR (BIAS CIRCUIT) LENGTH CALCULATIONS============================================================================
mirror_ratio_error_percent = 10                                                #for smaller error better use cascode mirrors (ΔI/I = 0.1)
vdrain_pmos_mirror_ibias = Vbias_chosen
vdrain_pmos_opamp_ibias = VDD - (2/gm_id_opamp) - Vthp_min  
vearly_mirror_ibias = (vdrain_pmos_opamp_ibias - vdrain_pmos_mirror_ibias)/((mirror_ratio_error_percent/100))

L_nmos_ibias = find_length_from_va(early_voltage_lut_nmos, vearly_mirror_ibias)
L_pmos_ibias = find_length_from_va(early_voltage_lut_pmos, vearly_mirror_ibias)

print(f"Vdsat = {vdsat_mirror:.3f} V")
print(f"Vbias range = {Vbias_min:.2f} V to {Vbias_max:.2f} V")
print(f"Vbias chosen = {Vbias_chosen:.2f} V")
print(f"Vearly = {Vearly_mirror:.2f} V")
print(f"Rout (from 0.35/ΔI) = {Rout1:.2e} Ω")
print(f"Verr = {Verr*1e3:.2f} mV")
print(f"Vgate = {Vgate:.2f} V")
print(f"Required Gain = {A:.2f}")
print(f"Gain in dB = {AdB:.2f} dB")
print(f"Vearly_opamp = {vearly_opamp:.2f} V")
print(f"for opamp NMOS: Va = {vearly_opamp} V → L ≈ {L_nmos_opamp:.2f} nm")
print(f"for opamp PMOS: Va = {vearly_opamp} V → L ≈ {L_pmos_opamp:.2f} nm")
print(f"for mirror PMOS: Va = {Vearly_mirror} V → L ≈ {L_pmos_mirror:.2f} nm")








