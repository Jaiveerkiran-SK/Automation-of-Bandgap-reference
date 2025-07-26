import pandas as pd
import numpy as np
from sympy import symbols, Eq, solve

#===============================================================================
#nmos data at 125
vgs_vals = np.array([
    0.0, 0.1, 0.2, 0.3, 0.4,
    0.5, 0.6, 0.7, 0.8, 0.9,
    1.0, 1.1, 1.2, 1.3, 1.4,
    1.5, 1.6, 1.7, 1.8
])

# Id values from m1 to m19 (in amperes)
id_vals = np.array([
    4.84e-09, 2.73e-08, 1.45e-07, 7.26e-07, 3.19e-06,
    1.02e-05, 2.30e-05, 4.01e-05, 6.00e-05, 8.21e-05,
    1.06e-04, 1.32e-04, 1.60e-04, 1.89e-04, 2.19e-04,
    2.51e-04, 2.83e-04, 3.16e-04, 3.50e-04
])

# Gm values from m1 to m19 (in siemens)
gm_vals = np.array([
    8.51e-08, 4.65e-07, 2.37e-06, 1.14e-05, 4.29e-05,
    9.97e-05, 1.52e-04, 1.87e-04, 2.11e-04, 2.31e-04,
    2.50e-04, 2.67e-04, 2.83e-04, 2.98e-04, 3.10e-04,
    3.21e-04, 3.29e-04, 3.36e-04, 3.41e-04
])

# Compute derived quantities
gm_id = gm_vals / id_vals

# Create lookup table
lookup_table_nmos125 = pd.DataFrame({
    "Vgs (V)": vgs_vals,
    "Id (A)": id_vals,
    "Gm (S)": gm_vals,
    "Gm/Id (1/V)": gm_id
})


# Display the table
print('cmosn 125\n')
print(lookup_table_nmos125)
#===============================================================================
#===============================================================================
# PMOS Data at 125°C
Vgs_values = [-1.80, -1.70, -1.60, -1.50, -1.40, -1.30, -1.20, -1.10, -1.00,
              -0.80, -0.70, -0.60, -0.50, -0.40, -0.30, -0.20, -0.10, 0.00]
Id_values = [-3.48e-05, -3.13e-05, -2.79e-05, -2.45e-05, -2.11e-05,
             -1.79e-05, -1.49e-05, -1.22e-05, -9.80e-06, -5.75e-06,
             -4.08e-06, -2.64e-06, -1.46e-06, -6.35e-07, -1.99e-07,
             -4.77e-08, -1.03e-08, -2.13e-09]
Gm_values = [3.46e-05, 3.44e-05, 3.43e-05, 3.40e-05, 3.32e-05,
             3.12e-05, 2.84e-05, 2.56e-05, 2.28e-05, 1.78e-05,
             1.56e-05, 1.32e-05, 1.02e-05, 6.28e-06, 2.63e-06,
             7.19e-07, 1.59e-07, 3.40e-08]

# Convert Id to absolute for log calculation and compute Gm/Id
Id_abs = np.abs(Id_values)

Gm_over_Id = np.array(Gm_values) / Id_abs

# Create DataFrame
lookup_table_pmos125 = pd.DataFrame({
    "Vgs (V)": Vgs_values,
    "Id (A)": Id_abs,
    "Gm (S)": Gm_values,
    "Gm/Id (1/V)": Gm_over_Id
})

print('cmosp 125\n')
print(lookup_table_pmos125)

#===============================================================================
#===============================================================================
#pmos at 27
vgs_vals = np.array([
    -1.80, -1.70, -1.60, -1.50, -1.40,
    -1.30, -1.20, -1.10, -1.00, -0.80,
    -0.70, -0.60, -0.50, -0.40, -0.30,
    -0.20, -0.10,  0.00
])

# Id values (in A), from m1 to m18 (all negative as PMOS convention)
id_vals = np.array([
    -5.36e-05, -4.87e-05, -4.36e-05, -3.85e-05, -3.33e-05,
    -2.82e-05, -2.35e-05, -1.93e-05, -1.54e-05, -8.97e-06,
    -6.37e-06, -4.16e-06, -2.35e-06, -1.02e-06, -2.83e-07,
    -4.65e-08, -6.09e-09, -7.34e-10
])

# Gm values (in S), from m1 to m18
gm_vals = np.array([
    4.79e-05, 4.96e-05, 5.12e-05, 5.22e-05, 5.15e-05,
    4.87e-05, 4.48e-05, 4.06e-05, 3.64e-05, 2.81e-05,
    2.41e-05, 2.01e-05, 1.58e-05, 1.05e-05, 4.43e-06,
    9.18e-07, 1.26e-07, 1.59e-08
])

# Compute Gm/Id 
gm_id_vals = gm_vals / np.abs(id_vals)

# Create DataFrame
lookup_table_pmos27 = pd.DataFrame({
    "Vgs (V)": vgs_vals,
    "Id (A)": id_vals,
    "Gm (S)": gm_vals,
    "Gm/Id (1/V)": gm_id_vals
})


# Display the full table
print('pmos 27\n')
print(lookup_table_pmos27)

def find_id_for_gm_id(lookup_table, target_gm_id):
    # Find the index of the closest Gm/Id value
    closest_index = (lookup_table["Gm/Id (1/V)"] - target_gm_id).abs().idxmin()

    # Get the corresponding row
    closest_row = lookup_table.loc[closest_index]

    # Return the corresponding Id and Gm/Id
    return {
        "Closest Gm/Id": closest_row["Gm/Id (1/V)"],
        "Corresponding Id": closest_row["Id (A)"],
        "Vgs (V)": closest_row["Vgs (V)"]
    }
#==============================================================================
#automation of hand calculations
#==============================================================================

# Constants
k = 1.38e-23
q = 1.6e-19
I = 1.752
Vdd = 1.8
Vdd_error_percentage = 10
Pmax = 500e-6
n = 8
T = 300
Vref = 1.2
Vref_error_percentage = 2
Ibias = 5e-6
fingers_bias = 3


# Total current budget
Itotal_max = Pmax / Vdd
I_design = 0.9 * Itotal_max
# 20% of total current assigned for opamp.
I_opamp = 0.2 * I_design
I_branches = (0.8 * I_design)/3


# Resistor ratio
R2_by_R1 = (q * 0.0023) / (I * k * np.log(n))

# Solving for R1 and R2
R1, R2 = symbols('R1 R2', positive=True)
term1 = (k / q) * T * np.log(n) * I
I_target = I_branches
eq1 = Eq(term1 / R1 + 0.453 / R2, I_target)
eq2 = Eq(R2 / R1, R2_by_R1)
solution = solve((eq1, eq2), (R1, R2))
R1_val = float(solution[0][0])
R2_val = float(solution[0][1])

#opamp design==================================================================

fingers_tail = int(round(((I_opamp - Ibias)/Ibias ) * fingers_bias))
desired_gmid = 5
I_per_width_p = find_id_for_gm_id(lookup_table_pmos125, desired_gmid)["Corresponding Id"]
fingers_OTAP = int(round(abs(((I_opamp - Ibias)/2) / I_per_width_p)))
desired_gmid = 5
I_per_width_n = find_id_for_gm_id(lookup_table_nmos125, desired_gmid)["Corresponding Id"]
fingers_OTAN = int(round(abs(((I_opamp - Ibias)/2) / I_per_width_n)))


#==============================================================================
# R3 calculation
R3_val = 1.2 / (I_branches )
#==============================================================================

# Current mirror calculations:=================================================
Vdsat = Vdd - Vref
# Vdsat margin = 200mV
gm_Id = 2 / ( Vdsat + 0.2 )

target_value = gm_Id
result = find_id_for_gm_id(lookup_table_pmos27, target_value)
fingers_branch = int(abs(I_branches//(result["Corresponding Id"])))
#==============================================================================
#==============================================================================
# Output summary
print("Total available current: {:.2f} µA".format(Itotal_max * 1e6))
print("Current used: {:.2f} µA".format(I_design * 1e6))
print("R2/R1 ≈ {:.2f}".format(R2_by_R1))
print("Solved R1: {:.2f} Ω".format(R1_val))
print("Solved R2: {:.2f} Ω".format(R2_val))
print("Calculated R3: {:.2f} Ω".format(R3_val))
print("No. of fingers in current mirror :",fingers_branch)
print("No. of fingers in Tail of opamp :",fingers_tail)
print("No. of fingers in Input stage of opamp :",fingers_OTAP)
print("No. of fingers in Active load stage of opamp :",fingers_OTAN)
print("No. of fingers in bias stage of opamp :",fingers_bias)

#==============================================================================