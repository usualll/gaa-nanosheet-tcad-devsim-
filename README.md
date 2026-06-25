# GAA Nanosheet TCAD Scaling Study

A DEVSIM-based TCAD investigation of short-channel effects (SCE) and punch-through in a gate-all-around (GAA) nanosheet / ultra-thin-body (UTB) MOSFET, scaled from a 100nm baseline down to a 20nm gate length.

> This repository contains only the project's own scripts and analysis. It depends on [DEVSIM](https://github.com/devsim/devsim) as an external TCAD solver — install it separately per DEVSIM's own build instructions before running `mos_2d_create.py` / `mos_2d.py`.

## Motivation

As gate length ($L_g$) scales down, the source and drain depletion regions occupy a growing fraction of the channel. Below a critical $L_g$, these depletion regions merge — a failure mode known as **punch-through** — and the gate loses electrostatic control over the channel. This project simulates that transition directly using drift-diffusion TCAD, rather than relying on compact-model approximations, and extracts the two metrics that most directly expose the effect: threshold voltage ($V_{th}$) roll-off and subthreshold swing (SS) degradation.

## Tech stack

| Component | Tool |
| :--- | :--- |
| TCAD solver | [DEVSIM](https://devsim.org/) (drift-diffusion) |
| Geometry / meshing | DEVSIM Python API |
| Data analysis | NumPy, Matplotlib |
| Visualization | Custom interactive Matplotlib widget |

## Repository structure

```
.
├── mos_2d.py               # DC sweep driver: solves drift-diffusion, extracts Vth/SS
├── mos_2d_create.py        # Device geometry, mesh, and doping profile definition
├── utils/
│   └── mosfet_viz.html     # Interactive depletion-region / punch-through visualizer
├── docs/                   # Derivation notes, extracted figures
├── results/                # Id-Vg curves, summarized Vth/SS output
└── README.md
```

## Methodology

1. **Geometry (`mos_2d_create.py`)** — Defines a 2D cross-section of the device mesh with doping profiles representative of a scaled nanosheet/UTB structure, parametrized so that gate length can be swept from 100nm to 20nm without rebuilding the mesh from scratch.
2. **Physics solve (`mos_2d.py`)** — Runs a DC gate-voltage sweep at fixed drain bias, solving the Poisson and drift-diffusion equations self-consistently at each mesh node. $V_{th}$ is extracted via the constant-current method on the $I_D$–$V_{GS}$ curve; SS is extracted from the slope of $\log_{10}(I_D)$ vs. $V_{GS}$ in the subthreshold region.
3. **Visualization (`utils/mosfet_viz.html`)** — A standalone interactive tool (independent of the DEVSIM run) that illustrates the geometric mechanism behind the data: as $L_g$ shrinks, source/drain depletion width grows relative to channel length until the two regions overlap, flagging punch-through.

## Results

| Gate length ($L_g$) | Threshold voltage ($V_{th}$) | Subthreshold swing (SS) |
| :--- | :--- | :--- |
| 100 nm (baseline) | −0.292 V | 84.1 mV/dec |
| 50 nm | −0.366 V | 89.6 mV/dec |
| 20 nm | −0.680 V | 171.1 mV/dec |

**Reading the trend:**

- **100nm → 50nm:** $V_{th}$ shifts by 74 mV and SS degrades modestly (84.1 → 89.6 mV/dec). This is classical, gradual short-channel roll-off — the depletion regions are growing but still well separated from each other.
- **50nm → 20nm:** $V_{th}$ shifts by a further 314 mV — more than 4x the previous step — while SS nearly doubles to 171.1 mV/dec, well above the room-temperature ideal limit of ~60 mV/dec. This disproportionate jump in both metrics is the simulation's signature of **punch-through**: the source and drain depletion regions have merged, the channel can no longer be fully depleted/controlled by the gate, and subthreshold leakage rises sharply. The 20nm point is not "more of the same scaling trend" as 100→50nm — it is a qualitatively different failure regime.

Full $I_D$ – $V_{GS}$ sweep curves for each gate length are in `results/`:
- `results/id_vg_curve_100nm.png`
- `results/id_vg_curve_50nm.png`
- `results/id_vg_curve_20nm.png`

## Why this matters for scaling

This progression is exactly why planar bulk MOSFETs cannot scale below roughly the 20–30nm gate-length range, and why the industry moved to FinFET and now gate-all-around (GAA) nanosheet architectures: wrapping the gate around the channel on multiple sides suppresses depletion-region growth from the source/drain and restores electrostatic control, pushing the punch-through-limited $L_g$ to much smaller geometries than a planar device could achieve.

## Visualization

`utils/mosfet_viz.html` provides an interactive view of the mechanism described above — drag the gate-length slider and watch the depletion regions grow and merge, with live readouts for depletion width, effective channel length, and punch-through status. Open it directly in any browser (no server or build step required).

## Running the simulation

```bash
python mos_2d_create.py   # builds device geometry/mesh (requires DEVSIM installed)
python mos_2d.py          # runs DC sweep, extracts Vth/SS
```

Open `utils/mosfet_viz.html` directly in a browser for the interactive visualization — it has no dependency on DEVSIM or Python.

## Limitations / future work

- Current results cover three discrete gate lengths (100/50/20nm); a finer sweep would better localize the exact punch-through onset point.
- Simulation is 2D drift-diffusion; a full GAA nanosheet treatment would require a 3D mesh with explicit multi-gate wraparound geometry.
- `utils/mosfet_viz.html` uses an illustrative (non-fitted) depletion-width model for visualization purposes — it is a teaching aid for the mechanism, not a substitute for the DEVSIM solve.
