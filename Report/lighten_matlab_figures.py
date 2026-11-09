"""MATLAB R2025a saved its figures in dark theme. For the printed report, invert only the
neutral (grey/black/white) pixels -- background, axes, text -- and keep coloured data lines unchanged."""
import numpy as np
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for src, dst in [('Transient/output/figures/validation_vs_aspen_SENS1.png', 'figures/fig3_validation_light.png'),
                 ('Transient/output/figures/step_response_hot_water.png', 'figures/fig4_step_light.png')]:
    im = Image.open(ROOT / src).convert('RGBA')
    a4 = np.asarray(im).astype(float)
    a = a4[..., :3].copy()
    a[a4[..., 3] < 128] = 0          # transparent background -> treat as dark theme background
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / np.maximum(mx, 1)
    neutral = (sat < 0.18) & (mn < 248)   # leave the pure-white figure margin as it is
    out = a.copy()
    out[neutral] = 255 - a[neutral]
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(Path(__file__).parent / dst)
    print(dst)
