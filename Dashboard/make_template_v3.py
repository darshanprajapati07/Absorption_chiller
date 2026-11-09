"""Assemble dashboard_template.html (v3 UI) from ui_v3_shell.html plus the tested core
sections (data/physics, scenarios, descriptions, 3D plant) of dashboard_template_v2_3d.html."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
v2 = (HERE / 'dashboard_template_v2_3d.html').read_text(encoding='utf-8')
shell = (HERE / 'ui_v3_shell.html').read_text(encoding='utf-8')
M = '/* ================================================================ '


def between(start, end):
    a = v2.index(start)
    b = v2.index(end, a)
    return v2[a:b]


pre = between('const D = /*__DATA__*/null;', M + 'charts')
scn = between(M + 'scenarios + live twin', M + 'controls')
desc = between(M + 'plain-language descriptions', M + '3D plant')
td = between(M + '3D plant', M + 'selection + info panel')

edits = [
    (scn, [("name: 'Normal operation', desc: 'The chiller runs at its design conditions. Move any slider to change them, and the AI predicts how the plant responds over the next hour.'",
            "name: 'Design point, manual inputs', desc: 'Design conditions. Change any input below and the model predicts how the plant responds over the following hour.'"),
           ("name: 'Sunny day (12 h)'", "name: 'Solar day, 12 h'"),
           ("name: 'Heat source drops'", "name: 'Hot water 105 → 90 °C'"),
           ("name: 'Hot weather'", "name: 'Cooling water 27 → 32 °C'"),
           ("name: 'Building needs more cooling'", "name: 'Chilled return 12 → 15 °C'"),
           ("name: 'Warm start'", "name: 'Warm start, 80 → 105 °C'"),
           ("name: 'Pump slows down'", "name: 'Solution pump to 85 %'")]),
    (desc, [("name: 'Generator (boiler)'", "name: 'Generator'"),
            ("name: 'Evaporator (makes the cold)'", "name: 'Evaporator'"),
            ("name: 'Pre-heater (pass-through)'", "name: 'Preheater, zero duty'"),
            ("name: 'Heat recovery, cold side'", "name: 'Solution HX, cold side'"),
            ("name: 'Heat recovery, hot side'", "name: 'Solution HX, hot side'")]),
    (td, [("el.innerHTML = `<b>${EQ[key].name}</b><span>${key}</span><em></em>`;",
           "el.innerHTML = `<b>${key}</b><span>${EQ[key].name}</span><em></em>`; el.title = EQ[key].name;"),
          ("vp.insertBefore(labels.domElement, vp.querySelector('.vp-tools'));", "vp.insertBefore(labels.domElement, vp.querySelector('.vp-legend'));"),
          ("DESHEAT1: '0 kW (pass-through)'", "DESHEAT1: '0 kW'"),
          ("EVAP: `${st.y[T.Q_evap_kW].toFixed(1)} kW cooling · ${st.Te.toFixed(1)} °C`", "EVAP: `${st.y[T.Q_evap_kW].toFixed(1)} kW · ${st.Te.toFixed(1)} °C`"),
          ("COLD: `≈ ${st.qshx.toFixed(0)} kW recovered`", "COLD: `≈ ${st.qshx.toFixed(0)} kW`"),
          ("DFLASH: `${st.mr.toFixed(0)} kg/h steam`", "DFLASH: `${st.mr.toFixed(0)} kg/h vap.`"),
          ("const sun = new THREE.DirectionalLight(0xffffff, 1.35);", "const sun = new THREE.DirectionalLight(0xffffff, 1.2);")]),
]
out = []
for text, reps in edits:
    for a, b in reps:
        assert a in text, a[:70]
        text = text.replace(a, b)
    out.append(text)
scn, desc, td = out

# The descriptions section also defines the readout CARDS in v2? (no: cards live in their own section, not copied)
html = (shell.replace('/*@KEEP:pre@*/', pre).replace('/*@KEEP:scn@*/', scn)
        .replace('/*@KEEP:desc@*/', desc).replace('/*@KEEP:3d@*/', td))
assert '/*@KEEP' not in html
(HERE / 'dashboard_template.html').write_text(html, encoding='utf-8')
print('dashboard_template.html written', len(html))
