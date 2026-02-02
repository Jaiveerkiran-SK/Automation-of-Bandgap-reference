#File that contains specifications given by user


Max_power =eval(input("Maximum power consumption accepted:"))
reference_voltage =eval(input("Output reference voltage needed:"))
error_percentage_vref =eval(input("Error percentage in output:"))
vdd = eval(input("vdd:"))
error_percentage_vdd = eval(input("Error percentage in vdd:"))
spot = input("Want to enter spot noise specs ? y/n: ").strip().lower()
if spot == "y":
    no_points = eval(input("No. of points to check for spot noise:"))
    entry = {}
    for i in range(no_points):
        entry[i] = eval(input("enter freq,output noise in list [freq,output_noise[V^2/Hz]]"))
    noise_corner = eval(input("1/f noise corner:"))

integrated = input("Want to enter integrated noise spec ? y/n: ").strip().lower()    
if integrated == "y":
    start_freq = eval(input("start frequency for integration:")) 
    stop_freq = eval(input("stop frequency for integration:"))
    integ_noise = eval(input("integrated noise:"))
    
    


