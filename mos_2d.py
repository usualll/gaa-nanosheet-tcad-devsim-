# Copyright 2013 DEVSIM LLC
#
# SPDX-License-Identifier: Apache-2.0

from devsim.python_packages.simple_physics import (
    GetContactBiasName,
    SetOxideParameters,
    SetSiliconParameters,
    CreateSiliconPotentialOnly,
    CreateSiliconPotentialOnlyContact,
    CreateSiliconDriftDiffusion,
    CreateSiliconDriftDiffusionAtContact,
    CreateOxidePotentialOnly,
    CreateSiliconOxideInterface,
)
from devsim.python_packages.model_create import CreateSolution
from devsim import (
    get_contact_list,
    get_device_list,
    get_parameter,
    get_parameter_list,
    get_region_list,
    node_model,
    set_node_values,
    set_parameter,
    solve,
    write_devices,
)

import mos_2d_create  # noqa: F401, E402

device = "mymos"
silicon_regions = ("gate", "bulk")
oxide_regions = ("oxide",)
regions = ("gate", "bulk", "oxide")
interfaces = ("bulk_oxide", "gate_oxide")

for i in regions:
    CreateSolution(device, i, "Potential")

for i in silicon_regions:
    SetSiliconParameters(device, i, 300)
    CreateSiliconPotentialOnly(device, i)

for i in oxide_regions:
    SetOxideParameters(device, i, 300)
    CreateOxidePotentialOnly(device, i, "log_damp")

### Set up contacts
contacts = get_contact_list(device=device)
for i in contacts:
    tmp = get_region_list(device=device, contact=i)
    r = tmp[0]
    print("%s %s" % (r, i))
    CreateSiliconPotentialOnlyContact(device, r, i)
    set_parameter(device=device, name=GetContactBiasName(i), value=0.0)

for i in interfaces:
    CreateSiliconOxideInterface(device, i)

solve(type="dc", absolute_error=1.0e-13, relative_error=1e-12, maximum_iterations=30)
solve(type="dc", absolute_error=1.0e-13, relative_error=1e-12, maximum_iterations=30)
#
##write_devices -file gmsh_mos2d_potentialonly.tec -type tecplot
write_devices(file="gmsh_mos2d_potentialonly", type="vtk")

for i in silicon_regions:
    CreateSolution(device, i, "Electrons")
    CreateSolution(device, i, "Holes")
    set_node_values(
        device=device, region=i, name="Electrons", init_from="IntrinsicElectrons"
    )
    set_node_values(device=device, region=i, name="Holes", init_from="IntrinsicHoles")
    CreateSiliconDriftDiffusion(device, i, "mu_n", "mu_p")

for c in contacts:
    tmp = get_region_list(device=device, contact=c)
    r = tmp[0]
    CreateSiliconDriftDiffusionAtContact(device, r, c)

solve(type="dc", absolute_error=1.0e30, relative_error=1e-5, maximum_iterations=30)

for r in silicon_regions:
    node_model(
        device=device, region=r, name="logElectrons", equation="log(Electrons)/log(10)"
    )

write_devices(file="mos_2d_dd.msh", type="devsim")

with open("mos_2d_params.py", "w", encoding="utf-8") as ofh:
    ofh.write("import devsim\n")
    for p in get_parameter_list():
        if p in ("solver_callback", "direct_solver", "info"):
            continue
        v = repr(get_parameter(name=p))
        ofh.write('devsim.set_parameter(name="%s", value=%s)\n' % (p, v))
    for i in get_device_list():
        for p in get_parameter_list(device=i):
            v = repr(get_parameter(device=i, name=p))
            ofh.write(
                'devsim.set_parameter(device="%s", name="%s", value=%s)\n' % (i, p, v)
            )

    for i in get_device_list():
        for j in get_region_list(device=i):
            for p in get_parameter_list(device=i, region=j):
                v = repr(get_parameter(device=i, region=j, name=p))
                ofh.write(
                    'devsim.set_parameter(device="%s", region="%s", name="%s", value=%s)\n'
                    % (i, j, p, v)
                )

# My Iterations and Project to Find the Vth Roll-Off

import numpy as np
import matplotlib.pyplot as plt
from devsim import get_contact_current, set_parameter

print("\n--- Starting Id-Vg Sweep ---")

# Apply a small Drain Voltage 50mV
vds = 0.05
set_parameter(device=device, name=GetContactBiasName("drain"), value=vds)
solve(type="dc", absolute_error=1.0e30, relative_error=1e-5, maximum_iterations=30)


vg_steps = np.linspace(-1.5, 0.5, 21) 
id_list = []

for vg in vg_steps:
    
    set_parameter(device=device, name=GetContactBiasName("gate"), value=vg)
    solve(type="dc", absolute_error=1.0e30, relative_error=1e-5, maximum_iterations=30)
    
    
    current = get_contact_current(device=device, contact="drain", equation="ElectronContinuityEquation")
    
    
    id_list.append(abs(current))
    print(f"Vg = {vg:.2f} V | Id = {abs(current):.3e} A/cm")


plt.figure(figsize=(8, 6))
plt.plot(vg_steps, id_list, 'b.-', markersize=10, linewidth=2)
plt.yscale('log') 
plt.xlabel('Gate Voltage, Vg (V)', fontsize=12)
plt.ylabel('Drain Current, Id (A/cm)', fontsize=12)
plt.title('Id-Vg Curve (20nm Nanosheet / UTB)', fontsize=14)
plt.grid(True, which="both", ls="--", alpha=0.5)


plot_filename = 'id_vg_curve_Lg20.png'
plt.savefig(plot_filename, dpi=300)


#parameter extraction

target_current = 1e-7
# Convert lists to numpy arrays for interpolation
vg_array = np.array(vg_steps)
id_array = np.array(id_list)

# Interpolate to find Vth
vth = np.interp(target_current, id_array, vg_array)
print(f"\n--- Extracted Metrics ---")
print(f"Threshold Voltage (Vth) = {vth:.3f} V")


idx_low = np.abs(id_array - 1e-10).argmin()
idx_high = np.abs(id_array - 1e-8).argmin()

dVg = vg_array[idx_high] - vg_array[idx_low]
dLogId = np.log10(id_array[idx_high]) - np.log10(id_array[idx_low])

if dLogId != 0:
    ss = (dVg / dLogId) * 1000 
    print(f"Subthreshold Swing (SS) = {ss:.1f} mV/decade")
else:
    print("Could not extract SS accurately.")
print(f"\nSimulation complete! Plot saved as '{plot_filename}'")
