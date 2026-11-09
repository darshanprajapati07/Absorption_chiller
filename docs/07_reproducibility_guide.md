# 7. Reproducibility guide

Every stage can be re-run from the files in this repository. The random seeds are fixed, so re-runs give the same data and very nearly the same model. PyTorch on a different CPU can differ in the last digits.

## 7.0 Get the repository

```bash
git lfs install
git clone https://github.com/darshanprajapati07/Absorption_chiller.git
cd Absorption_chiller
git lfs pull
```

Check that `Transient/output/transient_dataset.csv` is about 174 MB. If it is only a few hundred bytes, it is an LFS pointer and `git lfs pull` has not run.

## 7.1 Stage 1 — Aspen Plus (optional, outputs already included)

1. Open `Steady_state/absorption.apw` in Aspen Plus. The corrected specifications from `Aspen_fix_parameters.md` §3 and §5b are already in the model.
2. Run the base case. Check that COP ≈ 0.608 and the residual is < 0.1 %. Q_gen = QDESHEAT1 + QDESAT + QDFLASH + QDESHEAT3.
3. To regenerate the sensitivity data, follow `SENS-1_setup_guide.md`: activate SENS-1, Run, export the results to Excel, then filter with the rules in `Aspen_fix_parameters.md` §5b Step F. The result is `SENS1_clean_dataset.xlsx`.

## 7.2 Stage 2 — MATLAB transient dataset

Requirements: base MATLAB R2021a or newer, with no toolboxes. It was tested on R2025a.

```matlab
cd Transient
run_all('quick')   % optional smoke test, about 2 min, 6 runs
run_all            % full dataset, about 5 min
```

or, from a terminal:

```bash
cd Transient
matlab -batch "run_all"
```

Check `output/validation_report.txt`:
- section A: states equal Aspen;
- section B: R = 0.9998;
- section D: 197 valid runs, 291,437 rows.

## 7.3 Stage 3 — Machine learning

Requirements: Python 3.12 and the packages in `ML_model/requirements.txt`. A GPU is not needed.

```bash
cd ML_model
python -m venv .venv && .venv\Scripts\activate      # Windows (optional)
pip install -r requirements.txt
python run_ml.py --quick     # about 5 min smoke test: 20 epochs, 1 seed
python run_ml.py             # full: 600 epochs x 3 seeds, about 2.4 h on an 8-thread CPU
```

On Windows with the `py` launcher, use `py -3.12 run_ml.py`.

The script reads `../Transient/output/transient_dataset.csv` and writes everything to `outputs/`. Check `outputs/training_log.txt`: the LSTM ensemble should reach mean R² ≈ 0.9991.

## 7.4 Stage 4 — Dashboard

```bash
cd Dashboard
python build_dashboard.py    # reads ML_model/outputs and Transient/output
```

Open `chiller_dashboard.html` in a browser.

If you change the interface: edit `ui_v3_shell.html`, run `python make_template_v3.py`, then `python build_dashboard.py`.

### Optional: verify the JavaScript engine against PyTorch (Node.js ≥ 18)

```bash
cd Dashboard
node -e "const E=require('./twin_engine.js'),D=require('./dashboard_data.json');const t=new E.Twin(D);const r=D.test_runs[0];t.reset(r.U[0]);let m=0;r.U.forEach((u,i)=>{const p=t.step(u).mean;m=Math.max(m,Math.abs(p[0]-r.Y[i][0]))});console.log('max |Q_evap error| vs MATLAB truth (kW):',m.toFixed(3))"
```

This compares against the MATLAB truth. It should print a value of about 0.1–0.3 kW, which is the model error. Agreement with PyTorch to within 0.0014 kW was checked separately against `test_predictions_best_model.csv`.

## 7.5 Paths

All scripts use relative paths:
- `ML_model` reads `../Transient/output`;
- `Dashboard` reads `../ML_model/outputs` and `../Transient/output`.

Keep the folder layout unchanged. `Transient/README.md` mentions the original Windows path of the project laptop as an example only.
