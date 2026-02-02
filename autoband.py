
import os
import time
import re
import importlib
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import calculations
import spec
import time
START = time.time()
# Characterization file names (same as in your original script)
inpfile1 = "nmoschar.scs"
inpfile1_noext = os.path.splitext(inpfile1)[0]
inpfile1path = "./" + inpfile1_noext + ".scs"
inpfile1bckpath = "./" + inpfile1_noext + "_bk.scs"
output_file1_dc = "./" + inpfile1_noext + "/psf/dc.dc"

inpfile2 = "pmoschar.scs"
inpfile2_noext = os.path.splitext(inpfile2)[0]
inpfile2path = "./" + inpfile2_noext + ".scs"
inpfile2bckpath = "./" + inpfile2_noext + "_bk.scs"
output_file2_dc = "./" + inpfile2_noext + "/psf/dc.dc"
 
# (bandgap)
inpfile4 = "band_gap.scs"
inpfile4_noext = os.path.splitext(inpfile4)[0]
inpfile4path = "./" + inpfile4_noext + ".scs"
inpfile4bckpath = "./" + inpfile4_noext + "_bk.scs"
output_file4_dc = "./" + inpfile4_noext + "/psf/dc.dc"
output_file4_noise = "./" + inpfile4_noext + "/psf/noise.noise"
output_file4_stb = "./" + inpfile4_noext + "/psf/stb.margin.stb"




# Ensure we have backups of .scs (non-fatal)
def backup_if_missing(src_path, bk_path):
    try:
        if os.path.exists(src_path) and not os.path.exists(bk_path):
            with open(src_path, "r") as f:
                with open(bk_path, "w") as g:
                    g.write(f.read())
    except Exception as e:
        print("Warning: backup failed:", e)


backup_if_missing(inpfile1path, inpfile1bckpath)
backup_if_missing(inpfile2path, inpfile2bckpath)
backup_if_missing(inpfile4path, inpfile4bckpath)


def run_spectre_sim(ch_len,vol_ds,vol_gs,vdd, inpfile, inpfile_noext, inpfilepath, inpfilebckpath,vol_vdd = spec.vdd):
    spectre_args = [
        "/cad/tools/cadencetools/SPECTRE191/tools.lnx86/bin/spectre",
        "-64",
        inpfile, "+escchars",
        "=log", "./" + inpfile_noext + "/psf/spectre.out",
        "-format", "psfascii",
        "-raw", "./" + inpfile_noext + "/psf",
        "+aps", "+mt",
        "+lqtimeout", "900",
        "-maxw", "5",
        "-maxn", "5",
        "+logstatus"
    ]
    replacements = {"ch_len": str(ch_len) + 'n', "vol_ds":str(vol_ds),"vol_gs":str(vol_gs),"vdd":str(vdd),"vol_vdd":str(vol_vdd)}

    # change the scs with replacements
    try:
        if os.path.exists(inpfilepath):
            with open(inpfilepath, 'r') as file:
                content = file.read()
            for old_word, new_word in replacements.items():
                content = content.replace(old_word, new_word, 1)
            with open(inpfilepath, 'w') as file:
                file.write(content)
        else:
            
            print(f"Warning: {inpfilepath} not found; skipping replacement step.")
    except Exception as e:
        print("Error preparing scs file:", e)
        raise

    
    print("Running Spectre (characterization)...")
    try:
        subprocess.call(spectre_args)
    except Exception as e:
        print("Warning: spectre call failed or not available in environment:", e)
    
    print("Spectre (characterization) done.")

    # restore original
    try:
        if os.path.exists(inpfilebckpath):
            with open(inpfilebckpath, 'r') as readfile, open(inpfilepath, 'w') as writefile:
                for line in readfile:
                    writefile.write(line)
    except Exception as e:
        print("Warning: failed to restore scs backup:", e)

def run_spectre_sim_bandgap(
        # --- Fingers ---
        f_t, f_p_o, f_p_o_b, f_p_m,
        f_n_o, f_n_o_b, f_n_m_b, f_n_i,
        # --- Lengths ---
        l_p_o, l_p_m, l_n_o,
        l_n_i, l_p_i, l_t,
        l_c, l_c_b,
        # --- Widths ---
        w_p_o, w_p_m, w_n_o, w_n_i,
        w_t, w_c, w_c_b,w_p_i,
        # --- Diffusion ---
        d1, d2,
        # --- Mirror alias ---
        c_l_p_m, c_f_p_m, c_w_p_m,
        # --- Resistors ---
        res1, res2, res3,
        # --- Bias/supply ---
        IBIAS, VDD,
        #-----Corners--------
        cd,cm,cc,
        # --- Filepaths ---
        inpfile, inpfile_noext, inpfilepath, inpfilebckpath
    ):

    import re
    import os
    import subprocess

    # =====================================================
    # Utility for clean numeric formatting for Spectre
    # =====================================================
    def fmt(v, append_n=False):
        """Return properly formatted numeric value for Spectre."""
        try:
            val = float(v)
            is_int = abs(val - int(val)) < 1e-12
            val = int(val) if is_int else val
        except:
            val = v
        val = str(val)
        return val + "n" if append_n else val

    # =====================================================
    # Replacement dictionary — mapping placeholder → new value
    # =====================================================
    replacements = {
        "f_t": fmt(f_t),"f_p_o": fmt(f_p_o),"f_p_o_b": fmt(f_p_o_b),"f_p_m": fmt(f_p_m),"f_n_o": fmt(f_n_o),"f_n_o_b": fmt(f_n_o_b),
        "f_n_m_b": fmt(f_n_m_b),"f_n_i": fmt(f_n_i),"l_p_o": fmt(l_p_o, True),"l_p_m": fmt(l_p_m, True),"l_n_o": fmt(l_n_o, True),
        "l_n_i": fmt(l_n_i, True),"l_p_i": fmt(l_p_i, True),"l_t": fmt(l_t, True),"l_c": fmt(l_c, True),"l_c_b": fmt(l_c_b, True),
        "w_p_o": fmt(w_p_o, True),"w_p_m": fmt(w_p_m, True),"w_n_o": fmt(w_n_o, True),"w_n_i": fmt(w_n_i, True),"w_t": fmt(w_t, True),
        "w_c": fmt(w_c, True),"w_c_b": fmt(w_c_b, True),"w_p_i": fmt(w_p_i, True),"d1": fmt(d1),"d2": fmt(d2),
        "c_l_p_m": fmt(c_l_p_m, True),"c_f_p_m": fmt(c_f_p_m),"c_w_p_m": fmt(c_w_p_m, True),"RES1": fmt(res1),"RES2": fmt(res2),
        "RES3": fmt(res3),"IBIAS": fmt(IBIAS),"vdd": fmt(VDD),"cd":fmt(cd),"cm":fmt(cm),"cc":fmt(cc)
    }

    # =====================================================
    # REPLACE ONLY PLACEHOLDER TOKENS (SAFE)
    # =====================================================
    if os.path.exists(inpfilepath):
        with open(inpfilepath, "r") as f:
            content = f.read()

        for key, newval in replacements.items():
            # Replace ONLY standalone tokens like "l_c", "f_p_o", "res1", etc.
            pattern = re.compile(rf"\b{key}\b")
            content = pattern.sub(newval, content)

        with open(inpfilepath, "w") as f:
            f.write(content)
    else:
        print(f"WARNING: Netlist file {inpfilepath} not found — cannot update parameters.")

    # =====================================================
    # Run Spectre
    # =====================================================
    spectre_args = [
        "/cad/tools/cadencetools/SPECTRE191/tools.lnx86/bin/spectre",
        "-64",
        inpfile, "+escchars",
        "=log", "./" + inpfile_noext + "/psf/spectre.out",
        "-format", "psfascii",
        "-raw", "./" + inpfile_noext + "/psf",
        "+aps", "+mt",
        "+lqtimeout", "900",
        "-maxw", "5",
        "-maxn", "5",
        "+logstatus"
    ]
    #spectre_args = [
    #    "/cad/tools/cadencetools/SPECTRE191/tools.lnx86/bin/spectre",
    #    "-64",
    #    inpfile, "+escchars",
    #    "+log", f"./{inpfile_noext}/psf/spectre.out",
    #    "-format", "psfascii",
    #    "-raw", f"./{inpfile_noext}/psf",
    #    "+aps", "+mt",
    #    "+lqtimeout", "900",
    #   "-maxw", "5",
    #    "-maxn", "5",
    #    "-env",
    #    "+logstatus"
    #]

    subprocess.call(spectre_args)

    # =====================================================
    # Restore original .scs
    # =====================================================
    try:
        with open(inpfilebckpath, "r") as src, open(inpfilepath, "w") as dst:
            dst.write(src.read())
    except Exception as e:
        print("WARNING: Could not restore original .scs:", e)

def get_gmoverid_lut(filename):
    ids = []
    gmoverids = []
    current_id = None
    current_gmoverid = None

    if not os.path.exists(filename):
        raise FileNotFoundError(f"GM/ID LUT file not found: {filename}")

    with open(filename, 'r') as f:
        data_section = False
        for line in f:
            line = line.strip()
            if line == "VALUE":
                data_section = True
                continue
            if not data_section:
                continue
            if line.startswith('"M0:ids"'):
                parts = line.split()
                try:
                    current_id = float(parts[1])
                except:
                    continue
            elif line.startswith('"M0:gmoverid"'):
                parts = line.split()
                try:
                    current_gmoverid = float(parts[1])
                except:
                    continue
            if current_id is not None and current_gmoverid is not None:
                ids.append(current_id)
                gmoverids.append(current_gmoverid)
                current_id = None
                current_gmoverid = None

    if not ids or not gmoverids:
        raise ValueError("No Id or gm/Id data found in file.")
    return {ids[i]: gmoverids[i] for i in range(len(ids))}


def find_id_from_gmid(lut_dict, target_gmid):
    # find id whose gm/Id is closest to target
    return min(lut_dict, key=lambda id_: abs(lut_dict[id_] - target_gmid))


def get_vout(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"DC output file not found: {filename}")

    temperature = []
    vout = []
    current_temperature = None
    current_vout = None

    with open(filename, 'r') as f:
        data_section = False
        for line in f:
            line = line.strip()
            if line == "VALUE":
                data_section = True
                continue
            if not data_section:
                continue
            if line.startswith('"temp"'):
                parts = line.split()
                try:
                    current_temperature = float(parts[1])
                except:
                    continue
            elif line.startswith('"net7"'):
                parts = line.split()
                try:
                    current_vout = float(parts[1])
                except:
                    continue
            if current_temperature is not None and current_vout is not None:
                temperature.append(current_temperature)
                vout.append(current_vout)
                current_temperature = None
                current_vout = None

    if not temperature or not vout:
        raise ValueError("No temperature or vout data found in file.")
    return {temperature[i]: vout[i] for i in range(len(temperature))}


def extract_currents(psf_file_path):
    currents = []
    if not os.path.exists(psf_file_path):
        
        print(f"Warning: currents file not found: {psf_file_path}")
        return currents

    with open(psf_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('"V0:p"'):
                parts = line.split()
                try:
                    current_value = float(parts[-1])
                    currents.append(current_value)
                except:
                    pass
    return currents
    
    
def extract_CTAT_currents(psf_file_path):
    currents = []
    if not os.path.exists(psf_file_path):
        
        print(f"Warning: currents file not found: {psf_file_path}")
        return currents

    with open(psf_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('"I9.R4:1"'):
                parts = line.split()
                try:
                    current_value = float(parts[-1])
                    currents.append(current_value)
                except:
                    pass
    return currents   
    
def extract_PTAT_currents(psf_file_path):
    currents = []
    if not os.path.exists(psf_file_path):
        
        print(f"Warning: currents file not found: {psf_file_path}")
        return currents

    with open(psf_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('"I9.R2:1"'):
                parts = line.split()
                try:
                    current_value = float(parts[-1])
                    currents.append(current_value)
                except:
                    pass
    return currents    
    
    

import os

# small helper: safe float conversion
def _to_float(s):
    try:
        return float(s)
    except Exception:
        return None


import re
import numpy as np
import matplotlib.pyplot as plt

def parse_psf_noise_ascii(psf_file):
    freqs = []
    out_total_noise = []
    out_fn_noise = []
    out_thermal_noise = []

    inside_value = False
    current_freq = None
    device_values = []
    current_device = None

    # regex patterns
    freq_re = re.compile(r'"freq"\s+([eE0-9\+\-\.]+)')
    dev_start_re = re.compile(r'^"([^"]+)"\s*\(')
    dev_end_re = re.compile(r'^\)')

    with open(psf_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Wait until we see VALUE
            if not inside_value:
                if line.startswith("VALUE"):
                    inside_value = True
                continue

            # detect start of new frequency
            m = freq_re.match(line)
            if m:
                # store previous frequency result
                if current_freq is not None:
                    # Compute total noise at output
                    thermal_sum = 0.0
                    flicker_sum = 0.0
                    total_sum = 0.0

                    for dev, arr in device_values:
                        if dev.startswith("out"):  
                            # Only output total noise (already node output)
                            total_sum += arr[-1]
                            flicker_sum += 0.0  # no flicker component at out
                            thermal_sum += 0.0
                        elif ".R" in dev:       
                            # Resistors → thermal only (1 value)
                            thermal_sum += arr[0]
                        elif ".D" in dev:
                            # Diodes → arr = [thermal, flicker, total]
                            thermal_sum += arr[0]
                            flicker_sum += arr[1]
                        else:
                            # MOS devs: last → total noise; last-1 → flicker noise
                            flicker_sum += arr[-2]
                            thermal_sum += (arr[-1] - arr[-2])

                        total_sum += arr[-1]

                    freqs.append(current_freq)
                    out_total_noise.append(total_sum)
                    out_fn_noise.append(flicker_sum)
                    out_thermal_noise.append(thermal_sum)

                # reset for new frequency
                current_freq = float(m.group(1))
                device_values = []
                continue

            # detect device block start
            m = dev_start_re.match(line)
            if m:
                current_device = m.group(1)
                current_values = []
                continue

            # end of device block
            if dev_end_re.match(line):
                # Store this device's values
                device_values.append((current_device, current_values))
                current_device = None
                continue

            # If inside a device block, record numeric values
            if current_device is not None:
                try:
                    val = float(line)
                    current_values.append(val)
                except:
                    pass

    return (np.array(freqs),
            np.array(out_total_noise),
            np.array(out_fn_noise),
            np.array(out_thermal_noise))


def get_out_total_noise_at_freq(psf_file, target_freq=1e-3):
    freqs, out_total, out_fn, out_thermal = parse_psf_noise_ascii(psf_file)

    if freqs.size == 0:
        return None

    # ensure sorted (important for interpolation)
    idx = np.argsort(freqs)
    freqs = freqs[idx]
    out_total = out_total[idx]
    out_thermal = out_thermal[idx]
    out_fn = out_fn[idx]

    # interpolate
    noise_at_f = np.interp(target_freq, freqs, out_total)
    noise_at_thermal = np.interp(target_freq, freqs, out_thermal)
    noise_at_flicker = np.interp(target_freq, freqs, out_fn)

    return float(noise_at_f),float(noise_at_thermal),float(noise_at_flicker)





#=============================bandwidth_finder===========================================================================================================


def find_flicker_bandwidth(freqs, out_fn_noise, out_thermal_noise):
    """
    Return the frequency where flicker (1/f) noise equals thermal noise.
    If they never cross, returns the frequency where their difference is minimum.
    """

    freqs = np.asarray(freqs, dtype=float)
    fn = np.asarray(out_fn_noise, dtype=float)
    th = np.asarray(out_thermal_noise, dtype=float)

    # sanity checks
    if freqs.size < 2 or fn.size != freqs.size or th.size != freqs.size:
        return None

    diff = fn - th

    # Look for sign changes of diff (i.e. crossings)
    sign = np.sign(diff)
    sign_changes = np.where(sign[1:] * sign[:-1] < 0)[0]

    if sign_changes.size == 0:
        # No true crossing; pick point where |fn - th| is minimum
        idx = np.argmin(np.abs(diff))
        return float(freqs[idx])

    # Take the first crossing and linearly interpolate
    i = sign_changes[0]
    f1, f2 = freqs[i], freqs[i+1]
    d1, d2 = diff[i], diff[i+1]

    if d2 == d1:
        return float((f1 + f2) / 2.0)

    # linear interpolation: diff(f) = d1 + (d2-d1)*t, solve diff=0
    t = -d1 / (d2 - d1)
    f_corner = f1 + t * (f2 - f1)
    return float(f_corner)   
    
    
import re
import math

def noise_contribution_at_freq(psf_file, target_freq):
    """
    device_name -> (thermal %, flicker %) at closest available frequency
    """

    freq_re = re.compile(r'"freq"\s+([eE0-9\+\-\.]+)')
    dev_start_re = re.compile(r'^"([^"]+)"\s*\($')

    inside_value = False

    # --- best match tracking ---
    best_freq = None
    best_err = float("inf")
    best_device_data = None
    best_out_noise = None

    # --- current block ---
    current_freq = None
    current_device = None
    current_values = []
    device_data = {}
    out_noise = None

    with open(psf_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line == "VALUE":
                inside_value = True
                continue

            if not inside_value:
                continue

            # -------- New frequency block --------
            m = freq_re.match(line)
            if m:
                # evaluate previous block
                if current_freq is not None and out_noise is not None:
                    err = abs(current_freq - target_freq)
                    if err < best_err:
                        best_err = err
                        best_freq = current_freq
                        best_device_data = device_data.copy()
                        best_out_noise = out_noise

                # reset for new block
                current_freq = float(m.group(1))
                device_data = {}
                out_noise = None
                current_device = None
                continue

            # -------- Output noise --------
            if line.startswith('"out"'):
                out_noise = float(line.split()[-1])
                continue

            # -------- Device start --------
            m = dev_start_re.match(line)
            if m:
                current_device = m.group(1)
                current_values = []
                continue

            # -------- Device end --------
            if line == ")" and current_device is not None:
                device_data[current_device] = current_values.copy()
                current_device = None
                continue

            # -------- Numeric values --------
            if current_device is not None:
                current_values.append(float(line))

        # ---------- Final block check ----------
        if current_freq is not None and out_noise is not None:
            err = abs(current_freq - target_freq)
            if err < best_err:
                best_err = err
                best_freq = current_freq
                best_device_data = device_data.copy()
                best_out_noise = out_noise

    if best_out_noise is None:
        raise ValueError("No valid noise data found in file")

    # -------- Convert out to V²/Hz --------
    total_out_noise_power = best_out_noise ** 2

    contribution = {}

    for dev, vals in best_device_data.items():
        # Resistor
        if len(vals) == 2:
            thermal = vals[0]
            flicker = 0.0

        # Diode
        elif len(vals) == 3:
            thermal = vals[2]
            flicker = 0.0

        # MOS (BSIM4)
        elif len(vals) >= 14:
            flicker = vals[12]
            total = vals[13]
            thermal = max(total - flicker, 0.0)

        else:
            continue

        thermal_pct = 100.0 * thermal / total_out_noise_power
        flicker_pct = 100.0 * flicker / total_out_noise_power

        contribution[dev] = (thermal_pct, flicker_pct)

    # Optional: return the actual frequency used
    return contribution, best_freq    
    
    
    
def top_noise_contributors(contribution, top_n=5):
    """
    contribution: dict
        device -> (thermal_pct, flicker_pct)

    returns:
        dict { device: (max_pct, 'th' or 'fn') }
    """

    ranked = []

    for dev, (th_pct, fn_pct) in contribution.items():
        if th_pct >= fn_pct:
            ranked.append((dev, th_pct, "th"))
        else:
            ranked.append((dev, fn_pct, "fn"))

    # Sort by contribution percentage (descending)
    ranked.sort(key=lambda x: x[1], reverse=True)

    # Take top N
    top = ranked[:top_n]

    # Build output dictionary
    return {dev: (pct, kind) for dev, pct, kind in top}    


def vout_within_5mV(results, max_delta_v= (spec.error_percentage_vref * spec.reference_voltage * 0.01)):
    
    try:
        dict_t_vs_vout = results[0]
    except Exception:
        return False

    if not isinstance(dict_t_vs_vout, dict) or not dict_t_vs_vout:
        return False

    vouts = np.array(list(dict_t_vs_vout.values()), dtype=float)
    span = float(vouts.max() - vouts.min())
    
    print(f"Bandgap Vout span over temp = {span:.6f} V")
    return span <= max_delta_v

import time
import numpy as np

def optimize_bandgap(
    #====corners========
    cd,cm,cc,

    # === Fingers ===
    f_t,            # tail
    f_p_o,          # PMOS op-amp
    f_p_o_b,        # PMOS op-amp bias
    f_p_m,          # PMOS mirror
    f_n_o,          # NMOS op-amp
    f_n_o_b,        # NMOS op-amp bias
    f_n_m_b,        # NMOS mirror bias
    f_n_i,          # NMOS IBIAS device

    # === Lengths ===
    l_p_o,          # PMOS op-amp length
    l_p_m,          # PMOS mirror length
    l_n_o,          # NMOS op-amp length
    l_n_i,          # NMOS bias length
    l_p_i,          # PMOS bias length
    l_t,            # Tail transistor length
    l_c,            # Cascode (alias)
    l_c_b,          # Bias cascode length

    # === Widths ===
    w_p_o,
    w_p_m,
    w_n_o,
    w_n_i,
    w_t,
    w_c,
    w_c_b,
    w_p_i,

    # === Resistors ===
    res1, res2, res3,

    # === Supply & bias ===
    IBIAS,
    VDD,
    Vref,

    # === Diffusion parameters ===
    d1, d2,

    # === Mirror alias params ===
    c_l_p_m,
    c_f_p_m,
    c_w_p_m,
    

    # === File paths ===
    inpfile4, inpfile4_noext, inpfile4path, inpfile4bckpath,
    output_file4_dc,

    # === Optimization deltas ===
    delta_fnb=2,
    delta_fpm=100,
    delta_res=300,

    # === Optimization settings ===
    tol_smooth=0.5e-2,
    max_iters=50,
    error_margin=0.05
    
):

    start = time.time()

    def smoothness_cost(dict_t_vs_vout):
        temps = np.array(list(dict_t_vs_vout.keys()))
        vouts = np.array(list(dict_t_vs_vout.values()))
        if temps.size < 3:
            return 0.0
        diffs = np.diff(vouts)
        second_diffs = np.diff(diffs)
        return np.sum(np.abs(second_diffs))

    def run_bandgap(f_n_m_b_loc, f_p_m_loc, res1_loc, res2_loc, res3_loc):
        run_spectre_sim_bandgap(
            # --- Fingers ---
            f_t, f_p_o, f_p_o_b, f_p_m_loc,
            f_n_o, f_n_o_b, f_n_m_b_loc, f_n_i,

            # --- Lengths ---
            l_p_o, l_p_m, l_n_o,
            l_n_i, l_p_i, l_t,
            l_c, l_c_b,

            # --- Widths ---
            w_p_o, w_p_m, w_n_o, w_n_i,
            w_t, w_c, w_c_b, w_p_i,

            # --- Diffusion params ---
            d1, d2,

            # --- Mirror alias params ---
            c_l_p_m, c_f_p_m, c_w_p_m,

            # --- Resistors ---
            res1_loc, res2_loc, res3_loc,

            # --- Bias/supply ---
            IBIAS, VDD,
            #-----corners--------
            cd,cm,cc,

            # --- Filepaths ---
            inpfile4, inpfile4_noext, inpfile4path, inpfile4bckpath
        )

        try:
            return get_vout(output_file4_dc)
        except Exception as e:
            print("Warning: get_vout failed during bandgap run:", e)
            return {}

    def get_vout_at_30(dict_t_vs_vout):
        if not dict_t_vs_vout:
            return None
        if 30 in dict_t_vs_vout:
            return dict_t_vs_vout[30]
        temps_sorted = np.array(sorted(dict_t_vs_vout.keys()))
        vouts_sorted = np.array([dict_t_vs_vout[t] for t in temps_sorted])
        return float(np.interp(30, temps_sorted, vouts_sorted))

    def turning_point_temp(dict_t_vs_vout):
        if not dict_t_vs_vout:
            return None
        temps = np.array(sorted(dict_t_vs_vout.keys()))
        vouts = np.array([dict_t_vs_vout[t] for t in temps])
        if temps.size < 3:
            return None
        slopes = np.diff(vouts)
        idx_changes = np.where(np.diff(np.sign(slopes)) != 0)[0]
        if len(idx_changes) == 0:
            return None
        idx = idx_changes[-1]
        t1, t2 = temps[idx], temps[idx + 1]
        v1, v2 = slopes[idx], slopes[idx + 1]
        if v2 - v1 == 0:
            return (t1 + t2) / 2
        frac = -v1 / (v2 - v1)
        return t1 + frac * (t2 - t1)    

        
    def turning_point_cost(tp_temp, t_min=0, t_max=80):
        if tp_temp is None:
            return 1.0     # large penalty: no TP detected
        if tp_temp < t_min:
            return abs((t_min - tp_temp) / (t_max - t_min))
        if tp_temp > t_max:
            return abs((tp_temp - t_max) / (t_max - t_min))
        return 0.0


    # Stage 1: smoothness
    for i in range(int(int(max_iters)/2)):
        dict_t_vs_vout = run_bandgap(f_n_m_b, f_p_m, res1, res2, res3)
        J = smoothness_cost(dict_t_vs_vout)
        if J < tol_smooth:
            break
        f_n_m_b += delta_fnb
        
        print(f"f_n_m_b = {f_n_m_b}")

    # Stage 2: tune Vref
    Vref_min = Vref * (1 - error_margin)
    Vref_max = Vref * (1 + error_margin)
    vout_30 = get_vout_at_30(dict_t_vs_vout)
    iter2 = 0
    while (vout_30 is None or not (Vref_min <= vout_30 <= Vref_max)) and iter2 < max_iters:
        f_p_m += delta_fpm
        dict_t_vs_vout = run_bandgap(f_n_m_b, f_p_m, res1, res2, res3)
        if smoothness_cost(dict_t_vs_vout) > tol_smooth:
            f_n_m_b += delta_fnb
            
            iter2 += 1
            continue
        vout_30 = get_vout_at_30(dict_t_vs_vout)
        iter2 += 1

    # Stage 3:turning point enforcement
    iter3 = 0
    tp_temp = turning_point_temp(dict_t_vs_vout)

    # NOTE: this assumes -40 and 125 always exist as keys
    SLOPE = (dict_t_vs_vout[125] - dict_t_vs_vout[-40]) / 165.0

    while ( (tp_temp is None or not (0 <= tp_temp <= 85)) and (iter3 < max_iters) ):
        scale = turning_point_cost(tp_temp)
        if tp_temp is None:
            if SLOPE > 0:
                res1 += (scale * delta_res)
            else:
                res2 += ((scale * delta_res))

        if tp_temp is not None:
            if not (0 <= tp_temp <= 80):
                if (tp_temp >= 80) and SLOPE > 0:
                    res1 += (1*scale * delta_res)
                if (tp_temp >= 80) and SLOPE < 0:
                    res2 += (1*(scale * delta_res))
                if (tp_temp <= 0) and SLOPE > 0:
                    res1 += (1*scale * delta_res)
                if (tp_temp <= 0) and SLOPE < 0:
                    res2 += (1*(scale * delta_res))

            temps_sorted = np.array(sorted(dict_t_vs_vout.keys()))
            vouts_sorted = np.array([dict_t_vs_vout[t] for t in temps_sorted])
            vout_tp = float(np.interp(tp_temp, temps_sorted, vouts_sorted))

            print(f"\n🔹 Turning Point Temperature: {tp_temp:.2f}°C")
            print(f"🔹 Vout at Turning Point: {vout_tp:.4f} V")
            vmean = (sum(dict_t_vs_vout.values()) / len(dict_t_vs_vout))
            if (sum(dict_t_vs_vout.values()) / len(dict_t_vs_vout)) > Vref :
                res3 = res3 - ((abs(vout_tp - Vref) / vout_tp) * res3)
                
            else:
                res3 = res3 + ((abs(vout_tp - Vref) / vout_tp ) * res3)
                #res3 += 100

        dict_t_vs_vout = run_bandgap(f_n_m_b, f_p_m, res1, res2, res3)
        inner_iter = 0
        while smoothness_cost(dict_t_vs_vout) > tol_smooth and inner_iter < max_iters:
            f_n_m_b += delta_fnb
            dict_t_vs_vout = run_bandgap(f_n_m_b, f_p_m, res1, res2, res3)
            inner_iter += 1

        SLOPE = (dict_t_vs_vout[125] - dict_t_vs_vout[-40]) / 165.0
        tp_temp = turning_point_temp(dict_t_vs_vout)
        iter3 += 1

    time_elapsed = time.time() - start
    print(f"total time taken = {time_elapsed:.2f} seconds...")

    return dict_t_vs_vout, f_n_m_b, f_p_m, res1, res2, res3, tp_temp




# ---- run iteration ----
def run_iteration():
    
    ch_len_nmos = calculations.L_nmos_opamp
    ch_len_pmos_opamp = calculations.L_pmos_opamp
    ch_len_pmos_mirror = calculations.L_pmos_mirror

    run_spectre_sim(ch_len_nmos,spec.vdd/2,spec.vdd/2,spec.vdd, inpfile1, inpfile1_noext, inpfile1path, inpfile1bckpath)
    lut_gmid_nmos = get_gmoverid_lut(output_file1_dc)
    gmid_opamp = calculations.gm_id_opamp
    i_perfinger_nmos = find_id_from_gmid(lut_gmid_nmos, gmid_opamp)
    no_of_fingers_nmos_opamp = round((calculations.Iopamp_branch / i_perfinger_nmos))
    
    print(f"No. of fingers of nmos in opamp: {no_of_fingers_nmos_opamp}")
    
    run_spectre_sim(60,spec.vdd/2,spec.vdd/2,spec.vdd, inpfile1, inpfile1_noext, inpfile1path, inpfile1bckpath)
    lut_gmid_nmos = get_gmoverid_lut(output_file1_dc)
    gmid_opamp_nmos_bias = calculations.gm_id_opamp / 2
    i_perfinger_nmos = find_id_from_gmid(lut_gmid_nmos, gmid_opamp_nmos_bias)
    no_of_fingers_nmos_opamp_bias = round((calculations.IBIAS / i_perfinger_nmos))
    if no_of_fingers_nmos_opamp_bias == 0:
        no_of_fingers_nmos_opamp_bias = 1
    
    print(f"No. of fingers of nmos in opamp in bias stage: {no_of_fingers_nmos_opamp_bias}")
    
    run_spectre_sim(ch_len_pmos_opamp,spec.vdd/2,spec.vdd/2,spec.vdd, inpfile2, inpfile2_noext, inpfile2path, inpfile2bckpath)
    lut_gmid_pmos = get_gmoverid_lut(output_file2_dc)
    i_perfinger_pmos_opamp = find_id_from_gmid(lut_gmid_pmos, calculations.gm_id_opamp)
    no_of_fingers_pmos_opamp = round(-(calculations.Iopamp_branch / i_perfinger_pmos_opamp))
    
    print(f"No. of fingers of pmos of opamp: {no_of_fingers_pmos_opamp}")
    
    run_spectre_sim(60,spec.vdd/2,spec.vdd/2,spec.vdd, inpfile2, inpfile2_noext, inpfile2path, inpfile2bckpath)
    lut_gmid_pmos = get_gmoverid_lut(output_file2_dc)
    i_perfinger_pmos_opamp = find_id_from_gmid(lut_gmid_pmos, calculations.gm_id_opamp / 2)
    no_of_fingers_pmos_opamp_bias = round(-(calculations.IBIAS / i_perfinger_pmos_opamp))
    if no_of_fingers_pmos_opamp_bias == 0 :
        no_of_fingers_pmos_opamp_bias = 3
    
    print(f"No. of fingers of pmos of opamp for bias stage: {no_of_fingers_pmos_opamp_bias}")
    
    run_spectre_sim(ch_len_pmos_mirror,spec.vdd/2,spec.vdd/2,spec.vdd, inpfile2, inpfile2_noext, inpfile2path, inpfile2bckpath)
    lut_gmid_pmos = get_gmoverid_lut(output_file2_dc)
    i_perfinger_pmos_mirror = find_id_from_gmid(lut_gmid_pmos, calculations.gm_id_mirror)
    no_of_fingers_pmos_mirror = round(-(calculations.I / i_perfinger_pmos_mirror))
    
    print(f"No. of fingers of pmos of mirror: {no_of_fingers_pmos_mirror}")
    
    gmid_mirror_bias = calculations.gm_id_mirror/2 #2 / (calculations.VDD - calculations.Vbias_chosen - 0.285)
    
    run_spectre_sim(ch_len_pmos_mirror,spec.vdd/2,spec.vdd/2,spec.vdd, inpfile2, inpfile2_noext, inpfile2path, inpfile2bckpath)
    lut_gmid_pmos = get_gmoverid_lut(output_file2_dc)
    i_perfinger_pmos_mirror = find_id_from_gmid(lut_gmid_pmos, gmid_mirror_bias)
    no_of_fingers_nmos_mirror_bias = round(- i_perfinger_pmos_mirror / calculations.IBIAS)
    if no_of_fingers_nmos_mirror_bias == 0:
        no_of_fingers_nmos_mirror_bias = 1
    print(f"No. of fingers of nmos in bias stage of current mirror: {no_of_fingers_nmos_mirror_bias}")
    
    no_of_fingers_tail = round(((2*calculations.Iopamp_branch) + calculations.IBIAS) / calculations.IBIAS)
    print(f"no of fingers for tail:{no_of_fingers_tail}")
    

    l_p_o = calculations.L_pmos_opamp
    l_p_m = calculations.L_pmos_mirror
    l_n_o = calculations.L_nmos_opamp
    f_p_o = no_of_fingers_pmos_opamp
    f_p_o_b = no_of_fingers_pmos_opamp_bias
    f_p_m = no_of_fingers_pmos_mirror
    f_n_o = no_of_fingers_nmos_opamp
    f_n_o_b = no_of_fingers_nmos_opamp_bias
    f_n_m_b = no_of_fingers_nmos_mirror_bias
    f_t = no_of_fingers_tail
    l_c = calculations.L_pmos_mirror
    w_c = 200
    c_l_p_m = calculations.L_pmos_mirror
    c_f_p_m = no_of_fingers_pmos_mirror
    c_w_p_m = 200
    IBIAS = calculations.IBIAS
    l_c_b = calculations.L_nmos_ibias
    l_n_i = calculations.L_nmos_ibias
    l_p_i = calculations.L_pmos_ibias
    l_t = calculations.L_nmos_ibias
    d1 = 1
    d2 = 8
    f_n_i = 1
    w_c_b = 200
    w_n_i = 200
    w_n_o = 200
    w_p_i = 200
    w_p_m = 200
    w_p_o = 200
    w_t = 200
    
    print(f"f_p_o = {f_p_o}/n, f_p_m = {f_p_m}/n, f_n_o = {f_n_o}/n")

    res1 = calculations.R1
    res2 = calculations.R2
    res3 = calculations.R3
    VDD = calculations.V_dd     #for pvt calculations V_dd is used.

    params = {
    "l_p_o": l_p_o,"l_p_m": l_p_m,"l_n_o": l_n_o,"l_n_i": l_n_i,"l_p_i": l_p_i,"l_t": l_t,"l_c": l_c,"l_c_b": l_c_b,
    "f_t": f_t,"f_p_o": f_p_o,"f_p_o_b": f_p_o_b,"f_p_m": f_p_m,"f_n_o": f_n_o,"f_n_o_b": f_n_o_b,"f_n_m_b": f_n_m_b,"f_n_i": f_n_i,
    "w_p_o": w_p_o,"w_p_m": w_p_m,"w_n_o": w_n_o,"w_n_i": w_n_i,"w_t": w_t,"w_c": w_c,"w_c_b": w_c_b,"w_p_i": w_p_i,"R1": res1,
   "R2": res2,"R3": res3,"IBIAS": IBIAS,"VDD": VDD,"d1": d1,"d2": d2,"c_l_p_m": c_l_p_m,"c_f_p_m": c_f_p_m,"c_w_p_m": c_w_p_m
}

    dict_t_vs_vout, f_n_m_b, f_p_m, res1, res2, res3, tp_temp = optimize_bandgap(
    
    #====corners========
    cd,cm,cc,

    # === Fingers ===
    f_t,
    f_p_o,
    f_p_o_b,
    f_p_m,
    f_n_o,
    f_n_o_b,
    f_n_m_b,
    f_n_i,

    # === Lengths ===
    l_p_o,
    l_p_m,
    l_n_o,
    l_n_i,
    l_p_i,
    l_t,
    l_c,
    l_c_b,

    # === Widths ===
    w_p_o,
    w_p_m,
    w_n_o,
    w_n_i,
    w_t,
    w_c,
    w_c_b,
    w_p_i,

    # === Resistors ===
    res1,
    res2,
    res3,

    # === Bias & supply ===
    IBIAS,
    VDD,
    calculations.Vref,

    # === Diffusion ===
    d1,
    d2,

    # === Mirror alias ===
    c_l_p_m,
    c_f_p_m,
    c_w_p_m,
    
    

    # === File paths ===
    inpfile4,
    inpfile4_noext,
    inpfile4path,
    inpfile4bckpath,
    output_file4_dc,

    # === Optimization settings (optional overrides) ===
    delta_fnb=1,
    delta_fpm=50,
    delta_res=100,
    tol_smooth=1e-2,
    max_iters=10,
    error_margin=0.05,
    
    
)
    results = (dict_t_vs_vout, f_n_m_b, f_p_m, res1, res2, res3, tp_temp)
    return params, results

#params,results = run_iteration()

PRINT_PROGRESS = True


def integrated_rms_noise(freqs, noise_psd, start_freq, stop_freq):
    """
    Compute integrated RMS noise from noise PSD.

    Parameters
    ----------
    freqs : np.ndarray
        Frequency array (Hz)
    noise_psd : np.ndarray
        Noise power spectral density (V^2/Hz)
    start_freq : float
        Integration start frequency (Hz)
    stop_freq : float
        Integration stop frequency (Hz)

    Returns
    -------
    rms_noise : float
        Integrated RMS noise (V)
    """
    freqs = np.asarray(freqs)
    noise_psd = np.asarray(noise_psd)

    if freqs.shape != noise_psd.shape:
        raise ValueError("freqs and noise_psd must have the same shape")

    mask = (freqs >= start_freq) & (freqs <= stop_freq)

    if not np.any(mask):
        raise ValueError("No frequency points in the specified range")

    noise_variance = np.trapezoid(noise_psd[mask], freqs[mask])
    return np.sqrt(noise_variance)


def optimise_noise_with_optbandgap(
    dict_t_vs_vout, f_n_m_b, f_p_m, res1, res2, res3,
    params,
    max_iters=50,
):
    '''
    Noise optimisation:
      - Start from last geometry (params, results).
      - In each iteration:
          * tweak selected lengths/fingers in params,
          * call optimize_bandgap(...) directly,
          * evaluate noise_ok, vspan_ok, band_ok.
      - Stop when noise_ok and band_ok are True (and vspan_ok remains True).
    '''
    # Unpack geometry from params dict for convenience
    # (Assumes params keys are as in run_iteration)
    l_p_o  = params["l_p_o"]
    l_p_m  = params["l_p_m"]
    l_n_o  = params["l_n_o"]
    l_n_i  = params["l_n_i"]
    l_p_i  = params["l_p_i"]
    l_t    = params["l_t"]
    l_c    = params["l_c"]
    l_c_b  = params["l_c_b"]

    f_t      = params["f_t"]
    f_p_o    = params["f_p_o"]
    f_p_o_b  = params["f_p_o_b"]
    f_n_o    = params["f_n_o"]
    f_n_o_b  = params["f_n_o_b"]
    
    f_n_i    = 1  # or derive if you have it separately

    w_p_o  = params["w_p_o"]
    w_p_m  = params["w_p_m"]
    w_n_o  = params["w_n_o"]
    w_n_i  = params["w_n_i"]
    w_t    = params["w_t"]
    w_c    = params["w_c"]
    w_c_b  = params["w_c_b"]
    w_p_i  = params["w_p_i"]

    c_l_p_m = params["c_l_p_m"]
    c_f_p_m = params["c_f_p_m"]
    c_w_p_m = params["c_w_p_m"]
    IBIAS = params["IBIAS"]
    VDD = params["VDD"]
    Vref = spec.reference_voltage
    
    iterations = max_iters
    check = [0 for i in range(spec.no_points)]
    check_ok = [1 for i in range(spec.no_points)]
    alpha = 0.3 # damping factor
    #best = None
    for it in range(iterations):
        check = [0]*spec.no_points
        if spec.integrated == "y":
            start = spec.start_freq
            end = spec.stop_freq 
            integ = spec.integ_noise
            freqs, out_total, out_fn, out_thermal = parse_psf_noise_ascii(output_file4_noise)
            flick_bw = find_flicker_bandwidth(freqs, out_fn, out_thermal)
            noise_rms = integrated_rms_noise(freqs, out_total , start, end)
            if noise_rms > spec.integ_noise:
                analysis_freq = min(flick_bw, spec.noise_corner)
                contribution,best_freq = noise_contribution_at_freq(output_file4_noise,analysis_freq)
                top = top_noise_contributors(contribution)
                scale_rms = (spec.integ_noise/noise_rms)*(spec.integ_noise/noise_rms)*alpha
                if 'I9.M2' in top.keys():
                    if top['I9.M2'][1]=='th':
                        l_p_m *= (1+((top['I9.M2'][0]/100)*(scale_rms)))
                    if top['I9.M2'][1]=='fn':
                        l_p_m *= (1+((top['I9.M2'][0]/100)*(scale_rms)))
                        w_p_m *= (1+((top['I9.M2'][0]/100)*(scale_rms)))
                if 'I9.M0' in top.keys():
                    if top['I9.M0'][1]=='th':
                        l_p_m *= (1+((top['I9.M0'][0]/100)*(scale_rms)))
                    if top['I9.M0'][1]=='fn':
                        l_p_m *= (1+((top['I9.M0'][0]/100)*(scale_rms)))
                        w_p_m *= (1+((top['I9.M0'][0]/100)*(scale_rms)))
                if 'I5.M7' in top.keys():
                    if top['I5.M7'][1]=='th':
                        l_n_o *= (1+((top['I5.M7'][0]/100)*(scale_rms)))
                    if top['I5.M7'][1]=='fn':
                        l_n_o *= (1+((top['I5.M7'][0]/100)*(scale_rms)))
                        w_n_o *= (1+((top['I5.M7'][0]/100)*(scale_rms)))
                if 'I5.M5' in top.keys():
                    if top['I5.M5'][1]=='th':
                        l_n_o *= (1+((top['I5.M5'][0]/100)*(scale_rms)))
                    if top['I5.M5'][1]=='fn':
                        l_n_o *= (1+((top['I5.M5'][0]/100)*(scale_rms)))
                        w_n_o *= (1+((top['I5.M5'][0]/100)*(scale_rms)))   
                if 'I5.M0' in top.keys():
                    if top['I5.M0'][1]=='th':
                        l_p_o *= (1+((top['I5.M0'][0]/100)*(scale_rms)))
                    if top['I5.M0'][1]=='fn':
                        l_p_o *= (1+((top['I5.M0'][0]/100)*(scale_rms)))
                        w_p_o *= (1+((top['I5.M0'][0]/100)*(scale_rms)))
                if 'I5.M14' in top.keys():
                    if top['I5.M14'][1]=='th':
                        l_p_i *= (1+((top['I5.M14'][0]/100)*(scale_rms)))
                    if top['I5.M14'][1]=='fn':
                        l_p_i *= (1+((top['I5.M14'][0]/100)*(scale_rms)))
                        w_p_i *= (1+((top['I5.M14'][0]/100)*(scale_rms)))
                if 'I9.M6' in top.keys():
                    if top['I9.M6'][1]=='th':
                        l_c *= (1+((top['I9.M6'][0]/100)*(scale_rms)))
                    if top['I9.M6'][1]=='fn':
                        l_c *= (1+((top['I9.M6'][0]/100)*(scale_rms)))
                        w_c *= (1+((top['I9.M6'][0]/100)*(scale_rms)))
                dict_t_vs_vout, f_n_m_b, f_p_m, res1, res2, res3, tp_temp = optimize_bandgap(
                cd,cm,cc,
                f_t, f_p_o, f_p_o_b, f_p_m,
                f_n_o, f_n_o_b, f_n_m_b, f_n_i,
                l_p_o, l_p_m, l_n_o, l_n_i, l_p_i, l_t, l_c, l_c_b,
                w_p_o, w_p_m, w_n_o, w_n_i, w_t, w_c, w_c_b, w_p_i,
                res1, res2, res3,
                IBIAS, calculations.V_dd, Vref,
                d1=1, d2=8,
                c_l_p_m=c_l_p_m, c_f_p_m=c_f_p_m, c_w_p_m=c_w_p_m,
                
                
                
                inpfile4=inpfile4,
                inpfile4_noext=inpfile4_noext,
                inpfile4path=inpfile4path,
                inpfile4bckpath=inpfile4bckpath,
                output_file4_dc=output_file4_dc,
                delta_fnb=1,
                delta_fpm=50,
                delta_res=100,
                tol_smooth=1e-2,
                max_iters=5,
                error_margin=0.05

                )
        if spec.spot == "y":
        
            for i in range(spec.no_points):
                dict_t_vs_vout, f_n_m_b, f_p_m, res1, res2, res3, tp_temp = optimize_bandgap(
                cd,cm,cc,
                f_t, f_p_o, f_p_o_b, f_p_m,
                f_n_o, f_n_o_b, f_n_m_b, f_n_i,
                l_p_o, l_p_m, l_n_o, l_n_i, l_p_i, l_t, l_c, l_c_b,
                w_p_o, w_p_m, w_n_o, w_n_i, w_t, w_c, w_c_b, w_p_i,
                res1, res2, res3,
                IBIAS, calculations.V_dd, Vref,
                d1=1, d2=8,
                c_l_p_m=c_l_p_m, c_f_p_m=c_f_p_m, c_w_p_m=c_w_p_m,
                
               
                
                inpfile4=inpfile4,
                inpfile4_noext=inpfile4_noext,
                inpfile4path=inpfile4path,
                inpfile4bckpath=inpfile4bckpath,
                output_file4_dc=output_file4_dc,
                delta_fnb=1,
                delta_fpm=50,
                delta_res=100,
                tol_smooth=1e-2,
                max_iters=20,
                error_margin=0.05,
                
                )
            
                actual_noise,actual_thermal_noise_value,actual_flicker_noise_value = get_out_total_noise_at_freq(output_file4_noise, target_freq=spec.entry[i][0])

                #expected_thermal_noise_value = spec.entry[i][1]
                #expected_flicker_noise_value = spec.entry[i][2]
                #print(expected_thermal_noise_value,actual_thermal_noise_value)
                #if actual_thermal_noise_value > expected_thermal_noise_value:
                if actual_noise > spec.entry[i][1]:
                    contribution,best_freq = noise_contribution_at_freq(output_file4_noise, spec.entry[i][0])
                    top = top_noise_contributors(contribution)
                    scale_n = ((actual_noise - spec.entry[i][1])/actual_thermal_noise_value)*alpha
                    if 'I9.M2' in top.keys():
                        if top['I9.M2'][1]=='th':
                            l_p_m *= (1+((top['I9.M2'][0]/100)*scale_n))
                            w_p_m *= 1
                        if top['I9.M2'][1]=='fn':
                            l_p_m *= (1+((top['I9.M2'][0]/100)*scale_n))
                            w_p_m *= (1+((top['I9.M2'][0]/100)*scale_n))
                    if 'I9.M0' in top.keys():
                        if top['I9.M0'][1]=='th':
                            l_p_m *= (1+((top['I9.M0'][0]/100)*scale_n))
                            w_p_m *= 1
                        if top['I9.M0'][1]=='fn':
                            l_p_m *= (1+((top['I9.M0'][0]/100)*scale_n))
                            w_p_m *= (1+((top['I9.M0'][0]/100)*scale_n))
                    if 'I5.M7' in top.keys():
                        if top['I5.M7'][1]=='th':
                            l_n_o *= (1+((top['I5.M7'][0]/100)*scale_n))
                            w_n_o *= 1
                        if top['I5.M7'][1]=='fn':
                            l_n_o *= (1+((top['I5.M7'][0]/100)*scale_n))
                            w_n_o *= (1+((top['I5.M7'][0]/100)*scale_n))
                    if 'I5.M5' in top.keys():
                        if top['I5.M5'][1]=='th':
                            l_n_o *= (1+((top['I5.M5'][0]/100)*scale_n))
                            w_n_o *= 1
                        if top['I5.M5'][1]=='fn':
                            l_n_o *= (1+((top['I5.M5'][0]/100)*scale_n))
                            w_n_o *= (1+((top['I5.M5'][0]/100)*scale_n)) 
                    if 'I5.M0' in top.keys():
                        if top['I5.M0'][1]=='th':
                            l_p_o *= (1+((top['I5.M0'][0]/100)*scale_n))
                            w_p_o *= 1
                        if top['I5.M0'][1]=='fn':
                            l_p_o *= (1+((top['I5.M0'][0]/100)*scale_n))
                            w_p_o *= (1+((top['I5.M0'][0]/100)*scale_n))
                    if 'I5.M14' in top.keys():
                        if top['I5.M14'][1]=='th':
                            l_p_i *= (1+((top['I5.M14'][0]/100)*scale_n))
                            w_p_i *= 1
                        if top['I5.M14'][1]=='fn':
                            l_p_i *= (1+((top['I5.M14'][0]/100)*scale_n))
                            w_p_i *= (1+((top['I5.M14'][0]/100)*scale_n))
                    if 'I9.M6' in top.keys():
                        if top['I9.M6'][1]=='th':
                            l_c *= (1+((top['I9.M6'][0]/100)*scale_n))
                            w_c *= 1
                        if top['I9.M6'][1]=='fn':
                            l_c *= (1+((top['I9.M6'][0]/100)*scale_n))
                            w_c *= (1+((top['I9.M6'][0]/100)*scale_n))
                    dict_t_vs_vout, f_n_m_b, f_p_m, res1, res2, res3, tp_temp = optimize_bandgap(
                    cd,cm,cc,
                    f_t, f_p_o, f_p_o_b, f_p_m,
                    f_n_o, f_n_o_b, f_n_m_b, f_n_i,
                    l_p_o, l_p_m, l_n_o, l_n_i, l_p_i, l_t, l_c, l_c_b,
                    w_p_o, w_p_m, w_n_o, w_n_i, w_t, w_c, w_c_b, w_p_i,
                    res1, res2, res3,
                    IBIAS, calculations.V_dd, Vref,
                    d1=1, d2=8,
                    c_l_p_m=c_l_p_m, c_f_p_m=c_f_p_m, c_w_p_m=c_w_p_m,
                    
                    
                    
                    inpfile4=inpfile4,
                    inpfile4_noext=inpfile4_noext,
                    inpfile4path=inpfile4path,
                    inpfile4bckpath=inpfile4bckpath,
                    output_file4_dc=output_file4_dc,
                    delta_fnb=1,
                    delta_fpm=50,
                    delta_res=100,
                    tol_smooth=1e-2,
                    max_iters=5,
                    error_margin=0.05,
                    
                    )     
                
                freqs, out_total, out_fn, out_thermal = parse_psf_noise_ascii(output_file4_noise)
                flick_bw = find_flicker_bandwidth(freqs, out_fn, out_thermal)
                if flick_bw > spec.noise_corner :
                    contribution,best_freq = noise_contribution_at_freq(output_file4_noise,flick_bw)
                    top = top_noise_contributors(contribution)
                    scale_bw = ((flick_bw - spec.noise_corner)/flick_bw)* alpha
                    if 'I9.M2' in top.keys():
                        if top['I9.M2'][1]=='th':
                            l_p_m *= (1+((top['I9.M2'][0]/100)*scale_bw))
                        if top['I9.M2'][1]=='fn':
                            l_p_m *= (1+((top['I9.M2'][0]/100)*scale_bw))
                            w_p_m *= (1+((top['I9.M2'][0]/100)*scale_bw))
                    if 'I9.M0' in top.keys():
                        if top['I9.M0'][1]=='th':
                            l_p_m *= (1+((top['I9.M0'][0]/100)*scale_bw))
                        if top['I9.M0'][1]=='fn':
                            l_p_m *= (1+((top['I9.M0'][0]/100)*scale_bw))
                            w_p_m *= (1+((top['I9.M0'][0]/100)*scale_bw))
                    if 'I5.M7' in top.keys():
                        if top['I5.M7'][1]=='th':
                            l_n_o *= (1+((top['I5.M7'][0]/100)*scale_bw))
                        if top['I5.M7'][1]=='fn':
                            l_n_o *= (1+((top['I5.M7'][0]/100)*scale_bw))
                            w_n_o *= (1+((top['I5.M7'][0]/100)*scale_bw))
                    if 'I5.M5' in top.keys():
                        if top['I5.M5'][1]=='th':
                            l_n_o *= (1+((top['I5.M5'][0]/100)*scale_bw))
                        if top['I5.M5'][1]=='fn':
                            l_n_o *= (1+((top['I5.M5'][0]/100)*scale_bw))
                            w_n_o *= (1+((top['I5.M5'][0]/100)*scale_bw))
                    if 'I5.M0' in top.keys():
                        if top['I5.M0'][1]=='th':
                            l_p_o *= (1+((top['I5.M0'][0]/100)*scale_bw))
                        if top['I5.M0'][1]=='fn':
                            l_p_o *= (1+((top['I5.M0'][0]/100)*scale_bw))
                            w_p_o *= (1+((top['I5.M0'][0]/100)*scale_bw))
                    if 'I5.M14' in top.keys():
                        if top['I5.M14'][1]=='th':
                            l_p_i *= (1+((top['I5.M14'][0]/100)*scale_bw))
                        if top['I5.M14'][1]=='fn':
                            l_p_i *= (1+((top['I5.M14'][0]/100)*scale_bw))
                            w_p_i *= (1+((top['I5.M14'][0]/100)*scale_bw))
                    if 'I9.M6' in top.keys():
                        if top['I9.M6'][1]=='th':
                            l_c *= (1+((top['I9.M6'][0]/100)*scale_bw))
                        if top['I9.M6'][1]=='fn':
                            l_c *= (1+((top['I9.M6'][0]/100)*scale_bw))
                            w_c *= (1+((top['I9.M6'][0]/100)*scale_bw))
                    dict_t_vs_vout, f_n_m_b, f_p_m, res1, res2, res3, tp_temp = optimize_bandgap(
                    cd,cm,cc,
                    f_t, f_p_o, f_p_o_b, f_p_m,
                    f_n_o, f_n_o_b, f_n_m_b, f_n_i,
                    l_p_o, l_p_m, l_n_o, l_n_i, l_p_i, l_t, l_c, l_c_b,
                    w_p_o, w_p_m, w_n_o, w_n_i, w_t, w_c, w_c_b, w_p_i,
                    res1, res2, res3,
                    IBIAS, calculations.V_dd, Vref,
                    d1=1, d2=8,
                    c_l_p_m=c_l_p_m, c_f_p_m=c_f_p_m, c_w_p_m=c_w_p_m,
                    
                    
                    
                    inpfile4=inpfile4,
                    inpfile4_noext=inpfile4_noext,
                    inpfile4path=inpfile4path,
                    inpfile4bckpath=inpfile4bckpath,
                    output_file4_dc=output_file4_dc,
                    delta_fnb=1,
                    delta_fpm=50,
                    delta_res=100,
                    tol_smooth=1e-2,
                    max_iters=5,
                    error_margin=0.05,
                    
                    )
                if (actual_noise <= spec.entry[i][1]) and (flick_bw <= spec.noise_corner):
                    check[i] = 1
               
        if (noise_rms < spec.integ_noise) and (check == check_ok):
            print(f"- check = ------{check}-------------------")
            print(f"- noise_rms = ------{noise_rms}------------")
            freqs, out_total, out_fn, out_thermal = parse_psf_noise_ascii(output_file4_noise)
            flick_bw = find_flicker_bandwidth(freqs, out_fn, out_thermal)
            noise_rms = integrated_rms_noise(freqs, out_total , start, end)
            break                            

    best = {
                "dict_t_vs_vout": dict_t_vs_vout,
                "noise_rms":noise_rms,
                "flick_bw": flick_bw,
                "params": {
                    "l_p_o": l_p_o, "l_p_m": l_p_m, "l_n_o": l_n_o,
                    "l_n_i": l_n_i, "l_p_i": l_p_i, "l_t": l_t,
                    "l_c": l_c, "l_c_b": l_c_b,
                    "f_t": f_t, "f_p_o": f_p_o, "f_p_o_b": f_p_o_b,
                    "f_p_m": f_p_m, "f_n_o": f_n_o, "f_n_o_b": f_n_o_b,
                    "f_n_m_b": f_n_m_b,
                    "w_p_o": w_p_o, "w_p_m": w_p_m,
                    "w_n_o": w_n_o, "w_n_i": w_n_i,
                    "w_t": w_t, "w_c": w_c, "w_c_b": w_c_b, "w_p_i": w_p_i,
                    "R1": res1, "R2": res2, "R3": res3,
                    "c_l_p_m": c_l_p_m, "c_f_p_m": c_f_p_m, "c_w_p_m": c_w_p_m,"IBIAS":IBIAS,
                },
                "tp_temp": tp_temp,
            }
    print(check )  
    return best


#best= optimise_noise_with_optbandgap( results[0],results[1],results[2],results[3],results[4],results[5],params)


import importlib
import sys

def reload_calculations():
    """
    Import or reload calculations module and return it.
    Safe for repeated PVT / optimization runs.
    """
    global calculations

    if "calculations" in sys.modules:
        calculations = importlib.reload(sys.modules["calculations"])
    else:
        calculations = importlib.import_module("calculations")

    if PRINT_PROGRESS:
        print(
            f"[reload] calculations.V_dd = "
            f"{getattr(calculations, 'V_dd', 'MISSING')}"
        )

    return calculations

# ===========================================update_power_in_file========================================================================================
def update_in_file(Avdd, module=calculations):
    """
    Overwrite the first 'V_dd = ...' line in calculations.py on disk.
    If no such line exists, prepend it.
    Returns the path written to.
    """
    file_path = getattr(module, "__file__", None)
    if file_path is None:
        raise RuntimeError("Module file path not available for calculations")

    # sometimes compiled .pyc path; ensure .py path
    if file_path.endswith(".pyc"):
        file_path = file_path[:-1]

    with open(file_path, "r") as f:
        original = f.read()

    lines = original.splitlines(keepends=True)
    found = False
    pattern = re.compile(r"^\s*V_dd\s*=")

    new_lines = []
    for line in lines:
        if (not found) and pattern.match(line):
            new_lines.append(f"V_dd = {Avdd}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        # prepend the power line
        new_content = f"V_dd = {Avdd}\n" + "".join(new_lines)
    else:
        new_content = "".join(new_lines)

    with open(file_path, "w") as f:
        f.write(new_content)

    if PRINT_PROGRESS:
        print(f"[disk] calculations.py updated: V_dd = {Avdd}  (path: {file_path})")
    return file_path

import os
import re

def set_process_corner_inplace(netlist_file, corner):
    """
    Replace Spectre model include sections in-place:
      cor_dio.scs     -> section=<corner>_dio
      cor_std_mos.scs -> section=<corner>
      cor_mim.scs     -> section=<corner>_mim
    """

    if corner not in ("ss", "tt", "ff"):
        raise ValueError("corner must be 'ss', 'tt', or 'ff'")

    if not os.path.isfile(netlist_file):
        raise FileNotFoundError(netlist_file)

    with open(netlist_file, "r") as f:
        lines = f.readlines()

    changed = False
    out = []

    for line in lines:
        orig = line

        if 'include "/cad/library/TSMC/65/GP/oa_pdk/models/spectre/cor_dio.scs" section=tt_dio\n' in line:
            line = re.sub(
                r'section\s*=\s*\w+',
                f'section={corner}_dio',
                line
            )

        elif 'include "/cad/library/TSMC/65/GP/oa_pdk/models/spectre/cor_std_mos.scs" section=tt\n' in line:
            line = re.sub(
                r'section\s*=\s*\w+',
                f'section={corner}',
                line
            )

        elif 'include "/cad/library/TSMC/65/GP/oa_pdk/models/spectre/cor_mim.scs" section=tt_mim' in line:
            line = re.sub(
                r'section\s*=\s*\w+',
                f'section={corner}_mim',
                line
            )

        if line != orig:
            changed = True

        out.append(line)

    #if not changed:
        #print(f"⚠️ Warning: no corner lines modified in {netlist_file}")

    with open(netlist_file, "w") as f:
        f.writelines(out)



def pvt(
    
):
    global cd, cm, cc,corner
    for Avdd in [spec.vdd]:
        reload_calculations()
        update_in_file(Avdd, module=calculations)
        reload_calculations()
        for corner in ["tt"]:
            if corner == "tt":
                cd = 'tt_dio'
                cm='tt'
                cc='tt_mim'
                
            elif corner == "ff":
                cd = 'ff_dio'
                cm='ff'
                cc='ff_mim'
            else:
                cd ='ss_dio'
                cm='ss'
                cc='ss_mim'
            
            params, results = run_iteration()
            best= optimise_noise_with_optbandgap( results[0],results[1],results[2],results[3],results[4],results[5],params)
            dict_t_vs_vout = best["dict_t_vs_vout"]

            tp_temp = best["tp_temp"]
            noise_bw = best["flick_bw"]
            noise_rms = best["noise_rms"]

            print(noise_rms, noise_rms)
            for i in best["params"].items():
                print(i)
            temps = np.array(sorted(dict_t_vs_vout.keys()))
            vouts = np.array([dict_t_vs_vout[t] for t in temps])

            plt.figure()
            plt.plot(temps, vouts, marker="o",label ="Vout")

            if tp_temp is not None:
                plt.axvline(
                    tp_temp,
                    color="k",
                    linestyle="--",
                    linewidth=1.5,
                    label=f"Turning Point = {tp_temp:.2f} °C"
                 )
                 
            plt.xlabel("Temperature (°C)")
            plt.ylabel("Vout (V)")
            plt.title(f"Final Vout vs Temperature in corner={corner} and vdd={Avdd}")
            plt.grid(True,which = "both")
            plt.legend()
            plt.show()

            currents = abs(np.array(extract_currents(output_file4_dc)))
            plt.figure()
            plt.plot(temps, currents, marker="o")
            plt.xlabel("Temperature (°C)")
            plt.ylabel("Total Current (A)")
            plt.title(f"Final Current_Total vs Temperature in corner={corner} and vdd={Avdd}")
            plt.grid(True)
            plt.show()


            currents_CTAT = abs(np.array(extract_CTAT_currents(output_file4_dc)))
            currents_PTAT = abs(np.array(extract_PTAT_currents(output_file4_dc)))
            plt.figure()
            plt.plot(temps, currents_CTAT, label="CTAT")
            plt.plot(temps, currents_PTAT, label="PTAT")
            plt.xlabel("Temperature (°C)")
            plt.ylabel("Current (A)")
            plt.legend()
            plt.grid(True)

            plt.show()

            freqs, out_total_noise, out_fn_noise, out_thermal_noise = parse_psf_noise_ascii(output_file4_noise)

            plt.figure()
            plt.loglog(freqs, out_total_noise, label="Total")
            plt.loglog(freqs, out_fn_noise, label="Flicker")
            plt.loglog(freqs, out_thermal_noise, label="Thermal")

            # ---- Noise corner marker ----
            plt.axvline(
                noise_bw,
                color="k",
                linestyle="--",
                linewidth=1.5,
                label=f"Noise BW = {noise_bw:.2e} Hz"
            )

            plt.xlabel("Frequency (Hz)")
            plt.ylabel("Noise (V$^2$/Hz)")
            plt.title(f"Final Output Noise Spectrum in in corner={corner} and vdd={Avdd}")
            plt.grid(True, which="both")
            plt.legend()
            plt.show()
            for i in dict_t_vs_vout.items():
                print(i)
            
        
pvt()       
END = time.time()
duration = END - START
print(f"total time taken = {duration} seconds")        
    
    










