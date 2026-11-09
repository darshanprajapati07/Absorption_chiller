# LiBr Chiller Digital Twin: dashboard

This is a live prototype of a single-effect H2O–LiBr absorption chiller.

- A 3D model of the plant is laid out like the Aspen Plus flowsheet: blocks PUMP, COLD, DESHEAT1, DESAT, DFLASH, DESHEAT3, CONDENS, VALVE, EVAP, ABSORB, HOT and SOLVALVE, and streams 1–10, A, B, C and QSHX.
- The trained LSTM ensemble from `../ML_model` runs inside the browser and drives every value you see.

## Open it

Double-click `chiller_dashboard.html` (Chrome or Edge).

The AI and all the numbers work offline. The 3D view loads the three.js library from the internet, so it needs a connection the first time.

## Views

- **3D plant.** This is the main view.
  - The plant is shown as 3D equipment: shell-and-tube exchangers, the separator drum, plate heat exchangers, the pump and the valves. Arrows inside the pipes move with the flow.
  - Click any machine or stream tag to get a plain-language explanation and its live values. A guided tour follows the cycle.
  - Six cards explain what the numbers mean: cooling, efficiency, cold-water temperature, heat used, crystallisation risk and freezing risk.
  - Use situations (sunny day, heat source drops, hot weather, …) or the sliders to change conditions.
- **Trends & numbers**
  - Trend charts.
  - A live stream table for every Aspen stream.
  - All 16 AI outputs with the spread between the 3 networks.
  - The energy check and the water circuits.
- **Is the AI accurate?**
  - Replay 5 unseen test runs against the physics simulation.
  - A comparison of the 4 models and the accuracy of each output.
- **How it works**
  - The cycle in six steps, a glossary and the build pipeline.
  - The design point, the model card, the valid input ranges and the limits.

## Stream values

The AI predicts 16 outputs directly. The values in this table are calculated from those outputs and are marked ≈ on the page:

| Value | How it is calculated |
|---|---|
| SHX outlets (streams 3, A, 5, 6) | Effectiveness 0.606 / 0.645, the medians of the transient dataset. RMSE 0.85 / 0.95 K against the MATLAB SHX temperatures. |
| Stream 7 | T_gen − 11.5 K, the drop across DESHEAT3 in the Aspen base case. |
| Stream 6 and flash fraction of stream 9 | Dühring equilibrium and an energy balance. |
| QSHX | m_strong · 1.93 kJ/kg·K · (T_gen − T5). |

In the corrected Aspen model, DESHEAT1 and DFLASH have zero duty, so streams A = 3 and B = generator state.

## Interface (v1.3)

The layout follows plant-HMI conventions (ANSI/ISA-101): grey ground, square panels with 1 px rules, and colour only for process lines and alarms. The Plant screen has:
- a model browser listing the Aspen blocks and streams;
- the 3D view;
- an instrument readout strip;
- a properties grid;
- an operating-conditions table with numeric inputs;
- a status bar.

Validation and Notes are set as report pages with numbered sections, booktabs tables, figure captions and references.

To change the interface, edit `ui_v3_shell.html`, then run `py -3.12 make_template_v3.py` followed by `py -3.12 build_dashboard.py`. The script reuses the tested model, physics and 3D code from `dashboard_template_v2_3d.html`.

## Rebuild after retraining

```
py -3.12 build_dashboard.py
```

The script writes two files:

| File | What it is |
|---|---|
| `chiller_dashboard.html` | Standalone page; opens by double-click. |
| `artifact_page.html` | Published version. |

The page is made from `dashboard_template.html`, with the model maths in `twin_engine.js`. `dashboard_template_v1_2d.html` is the earlier 2D version.

The full documentation is in [docs/05_digital_twin_dashboard.md](../docs/05_digital_twin_dashboard.md).
