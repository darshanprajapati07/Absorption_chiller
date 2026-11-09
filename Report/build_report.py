"""Builds the project report (Word) from the text below and the project's own figures.

Usage (from the Report folder):  py -3.12 build_report.py
Output: Absorption_Chiller_AI_Report.docx
"""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'Absorption_Chiller_AI_Report.docx'
BODY, HEAD = 'Cambria', 'Calibri'
GREY = RGBColor(0x55, 0x55, 0x55)

doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
sec.left_margin = sec.right_margin = Cm(2.4)
sec.top_margin, sec.bottom_margin = Cm(2.3), Cm(2.2)

# ---------------------------------------------------------------- styles
st = doc.styles['Normal']
st.font.name = BODY; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn('w:eastAsia'), BODY)
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.line_spacing = 1.15
for name, size, before, after in [('Heading 1', 15, 18, 6), ('Heading 2', 12, 12, 4)]:
    h = doc.styles[name]
    h.font.name = HEAD; h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    h.element.rPr.rFonts.set(qn('w:asciiTheme'), '') if False else None
    rf = h.element.rPr.find(qn('w:rFonts'))
    for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if rf is not None and rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    h.element.rPr.rFonts.set(qn('w:ascii'), HEAD); h.element.rPr.rFonts.set(qn('w:hAnsi'), HEAD)
    h.paragraph_format.space_before = Pt(before); h.paragraph_format.space_after = Pt(after)
    h.paragraph_format.keep_with_next = True


def para(text='', bold_lead=None, italic=False, align=None, size=None, color=None, after=None, style=None):
    p = doc.add_paragraph(style=style)
    if bold_lead:
        r = p.add_run(bold_lead); r.bold = True
    r = p.add_run(text); r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    if align is not None: p.alignment = align
    if after is not None: p.paragraph_format.space_after = Pt(after)
    return p


def bullets(items):
    for it in items:
        p = doc.add_paragraph(style='List Bullet')
        if isinstance(it, tuple):
            r = p.add_run(it[0]); r.bold = True; p.add_run(it[1])
        else:
            p.add_run(it)
        p.paragraph_format.space_after = Pt(3)


FIG = [0]
TAB = [0]


def figure(path, caption, width_cm=16.0):
    FIG[0] += 1
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = c.add_run(f'Figure {FIG[0]}. '); r.bold = True; r.font.size = Pt(9.5)
    r = c.add_run(caption); r.font.size = Pt(9.5); r.font.color.rgb = GREY
    c.paragraph_format.space_after = Pt(10)


def set_cell_border(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn('w:tcBorders'))
    if b is None:
        b = OxmlElement('w:tcBorders'); tcPr.append(b)
    for edge, (sz, color) in kw.items():
        e = OxmlElement(f'w:{edge}'); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), str(sz)); e.set(qn('w:color'), color)
        b.append(e)


def table(caption, header, rows, widths_cm, num_cols=()):
    TAB[0] += 1
    c = doc.add_paragraph(); c.paragraph_format.keep_with_next = True; c.paragraph_format.space_after = Pt(3)
    r = c.add_run(f'Table {TAB[0]}. '); r.bold = True; r.font.size = Pt(9.5)
    r = c.add_run(caption); r.font.size = Pt(9.5); r.font.color.rgb = GREY
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, row in enumerate([header] + rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j); cell.width = Cm(widths_cm[j])
            cell.text = ''
            p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(1); p.paragraph_format.line_spacing = 1.0
            run = p.add_run(str(val)); run.font.size = Pt(9.5); run.bold = (i == 0)
            if j in num_cols and i > 0: p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if j in num_cols and i == 0: p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if i == 0: set_cell_border(cell, top=(12, '000000'), bottom=(6, '000000'))
            if i == len(rows): set_cell_border(cell, bottom=(12, '000000'))
    for j, w in enumerate(widths_cm):
        t.columns[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_field(run, instr):
    f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = instr
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'end')
    run._r.append(f1); run._r.append(it); run._r.append(f2)


# ---------------------------------------------------------------- title page
for _ in range(5):
    doc.add_paragraph()
para('Project Report', size=12, color=GREY, align=WD_ALIGN_PARAGRAPH.LEFT, after=4)
t = doc.add_paragraph(); r = t.add_run('Predicting the Transient Behaviour of an Absorption Chiller with Artificial Intelligence')
r.font.name = HEAD; r.font.size = Pt(24); r.bold = True; t.paragraph_format.space_after = Pt(10)
para('A single-effect water / lithium-bromide chiller, from an Aspen Plus model to a working digital twin', size=13, color=GREY, after=40)
for lab in ['Submitted by', 'Roll number', 'Supervisor']:
    p = doc.add_paragraph(); r = p.add_run(f'{lab}:  '); r.bold = True
    p.add_run('______________________________'); p.paragraph_format.space_after = Pt(10)
for _ in range(6):
    doc.add_paragraph()
para('Department of Chemical Engineering', size=11.5, after=0)
para('Indian Institute of Technology Jodhpur', size=11.5, after=0)
para('7th Semester  ·  November 2026', size=11.5, color=GREY)

# body section with page numbers
body = doc.add_section(WD_SECTION.NEW_PAGE)
body.footer.is_linked_to_previous = False
fp = body.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_field(fp.add_run(), 'PAGE')
hp = body.header.paragraphs[0]; body.header.is_linked_to_previous = False
hr = hp.add_run('AI prediction of absorption chiller transients'); hr.font.size = Pt(8.5); hr.font.color.rgb = GREY
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
doc.sections[0].different_first_page_header_footer = True

# ---------------------------------------------------------------- abstract
doc.add_heading('Abstract', level=1)
para('Absorption chillers make cold water from heat instead of electricity, which makes them a good fit for solar heat and '
     'industrial waste heat. Their weak point is that they react slowly: after a change in the hot water or the weather, '
     'the machine takes a quarter of an hour or more to settle, and a steady-state simulator cannot show what happens in between.')
para('In this project we started from an Aspen Plus model of a single-effect water / lithium-bromide chiller, found and fixed '
     'the reasons its energy balance did not close, and used the corrected model to build a dynamic model in MATLAB. That model '
     'produced about 200 realistic operating scenarios, which we used to train a long short-term memory (LSTM) neural network. '
     'Given only the seven water-side inputs, the network predicts sixteen quantities of the chiller minute by minute. '
     'On 34 test runs it had never seen, it reached an average R² of 0.9991, with a typical error of 0.3 kW on a cooling '
     'capacity of about 80 kW. Finally, we built a web dashboard where the trained network runs live inside the browser, '
     'with a 3D view of the plant laid out like the Aspen flowsheet.')

# ---------------------------------------------------------------- 1 introduction
doc.add_heading('1. Introduction', level=1)
para('A single-effect absorption chiller uses water as the refrigerant and a lithium-bromide (LiBr) salt solution to absorb it. '
     'Heat, here from hot water at about 105 °C, boils water out of the salt solution in the generator. The vapour is condensed, '
     'expanded to a deep vacuum, and boiled again at about 2 °C in the evaporator, where it takes heat from the building\'s '
     'chilled water. The salt solution then soaks the vapour back up in the absorber, and a small pump returns it to the generator.')
para('Because the vessels hold a lot of metal and liquid, the machine responds slowly. Operators and designers would like to know '
     'how the chiller will behave over the next hour when, for example, the sun goes behind a cloud or the cooling tower warms up. '
     'Detailed dynamic simulators can answer that, but they are slow and need expert setup. An AI model trained on good simulation '
     'data can give the same answer in milliseconds.')
para('The aim of the project was therefore:')
bullets(['to correct and validate the steady-state Aspen Plus model of the chiller;',
         'to build a dynamic model calibrated to it and use it to generate transient data;',
         'to train an AI model that predicts the chiller\'s behaviour over time from its inputs alone;',
         'to make the trained model easy to use through an interactive dashboard.'])
para('One rule guided the whole project: the Aspen flowsheet was not to be rebuilt, and the efficiency (COP) was never to be '
     'adjusted to match a textbook value. Every correction had to have a physical reason.')
figure(HERE / 'figures/fig1_workflow.png', 'How the project fits together, from the Aspen model to the live dashboard.', 16.5)

# ---------------------------------------------------------------- 2 aspen
doc.add_heading('2. The Aspen Plus model', level=1)
para('The chiller was modelled in Aspen Plus with the ELECNRTL property method, which handles salt solutions. The flowsheet in '
     'Figure 2 uses twelve blocks. The generator is split into four steps (DESHEAT1, DESAT, DFLASH and DESHEAT3), and the '
     'solution heat exchanger is shown as two heaters, HOT and COLD, linked by the heat stream QSHX. The loop is deliberately '
     'broken between streams 1A and 1 so that Aspen can converge it.')
figure(ROOT / 'Steady_state/Screenshot 2026-11-04 164508.png', 'Aspen Plus flowsheet of the chiller (screenshot from the software).', 16.5)

doc.add_heading('2.1 What was wrong', level=2)
para('The original results gave a COP of about 0.21, roughly a third of what a machine like this should reach, and the energy '
     'balance was off by more than 42,000 kcal/h. Stranger still, the COP went down when the generator was made hotter, which is '
     'the opposite of what happens in a real chiller. Recalculating every block\'s duty from the stream enthalpies showed why:')
bullets([('The flash drum was acting as a cooler. ', 'DFLASH was set to a fixed temperature, so it condensed about 290 kg/h of the '
          'vapour that DESAT had just boiled off. Some 206,000 kcal/h of heat disappeared inside it without being counted.'),
         ('The loop did not close. ', 'The absorber outlet (1A) still carried unabsorbed vapour and did not match the pump inlet (1).'),
         ('A preheater was cooling. ', 'DESHEAT1 pushed the solution back down to 63.8 °C before the generator.'),
         ('The sensitivity study varied the wrong things. ', 'With every pressure fixed, its inputs barely touched the cycle.')])
para('The thermodynamic states themselves were sound. The problem was in how the heat was booked.')

doc.add_heading('2.2 What we changed', level=2)
para('We changed seven block specifications and added no new blocks. The generator (DESAT) was set to the true generator '
     'temperature, the flash drum was made adiabatic, the preheater became a pass-through, and the absorber, the evaporator '
     'and the loop-closing stream were specified by phase (saturated liquid or vapour) instead of by temperature. We also let the pump and the expansion valve '
     'set the two pressure levels, so that condenser and evaporator temperatures follow from the pressures as they do in a real machine.')
table('The Aspen model before and after the corrections.',
      ['Quantity', 'Before', 'After'],
      [['COP (cooling ÷ heat input)', '0.21', '0.608'],
       ['Energy balance error', '> 42,000 kcal/h', '< 0.05 %'],
       ['COP when the generator gets hotter', 'falls (wrong)', 'rises (correct)'],
       ['Blocks added or removed', '–', 'none']],
      [7.5, 4.2, 4.2])
para('A COP of 0.61 is lower than the 0.7 often quoted for this kind of chiller. This is not an error: the condenser in this '
     'model runs at about 10 kPa, which limits how much water can be boiled out of the solution. We kept the result rather than '
     'tuning it.')

# ---------------------------------------------------------------- 3 sens
doc.add_heading('3. A steady-state dataset', level=1)
para('With the model fixed, we rebuilt the sensitivity study around the three things that really drive the cycle: the generator '
     'temperature, the condenser pressure and the evaporator pressure. Eight, five and six values of each gave 240 cases, plus '
     'the base case. All 241 converged. We removed 78 cases where the strong solution went above 64 % LiBr, where it could '
     'crystallise and block the pipes, which left 163 valid operating points with COP between 0.23 and 0.79.')
para('Each valid case was checked outside Aspen as well. Mass and salt balances close exactly, the energy balance closes within '
     '0.24 %, the saturation temperatures agree with steam tables, no case breaks the second law, and COP rises and falls with '
     'each input in the direction physics expects.')

# ---------------------------------------------------------------- 4 matlab
doc.add_heading('4. A dynamic model of the chiller', level=1)
para('Aspen Plus Dynamics was not a practical route: the steady-state model has no vessel sizes, no water circuits and a broken '
     'loop, and converting it would have meant rebuilding the flowsheet. Instead, we followed the approach of Kohlenbach and Ziegler '
     '(2008) and wrote a compact dynamic model in MATLAB. Each of the four main vessels is treated as one well-mixed volume with its '
     'own metal mass, temperature and liquid inventory, which gives nine differential equations in total. Water and salt-solution '
     'properties come from standard correlations (IAPWS for water, ASHRAE for LiBr solution).')
para('We added the three water circuits the Aspen model lacks: hot water at 105 °C, cooling water at 27 °C passing through the '
     'absorber and then the condenser, and chilled water returning at 12 °C and leaving at 7 °C. The heat-transfer coefficients were '
     'then calibrated so that, at design conditions, the dynamic model settles exactly on the Aspen base case.')
figure(HERE / 'figures/fig3_validation_light.png',
       'The dynamic model\'s steady state compared with the 163 Aspen cases (COP correlation R = 0.9998).', 14.5)
para('When the hot water is raised by 10 K, the cooling output climbs from 81 to 94 kW, reaching 63 % of the change after 18 minutes '
     'and settling after about 45 (Figure 4). This slow response is exactly what the AI has to learn.')
figure(HERE / 'figures/fig4_step.png', 'Response of the dynamic model to a 10 K rise in hot-water temperature at time zero.', 16.5)

doc.add_heading('4.1 Transient data', level=2)
para('We used the model to simulate 199 operating scenarios, chosen to cover what a real chiller sees:')
table('Scenarios used to generate the transient dataset.',
      ['Type', 'Runs', 'What changes'],
      [['Steps', '20', 'one input jumps suddenly (hot water, cooling water, load, flows, pump)'],
       ['Ramps', '16', 'an input changes gradually over 10 to 60 minutes'],
       ['Start-up / shut-down', '8', 'hot water rises from 80 to 105 °C, or falls back'],
       ['Daily profiles', '5', '12-hour solar-type days with changing weather and load'],
       ['Random sequences', '150', 'all seven inputs change at random every 5 to 30 minutes']],
      [3.6, 1.4, 10.9], num_cols=(1,))
para('Every run was checked for crystallisation, freezing in the evaporator and energy conservation. 197 runs passed, giving '
     '291,437 rows of data at 10-second intervals. The largest energy-balance error in any run was 0.03 %. The runs were divided '
     'into 134 for training, 29 for validation and 34 for testing, always as whole runs, so the test runs were completely new to the AI.')

# ---------------------------------------------------------------- 5 ml
doc.add_heading('5. Teaching an AI to predict the chiller', level=1)
para('The AI is given only what an operator can measure from outside the machine: the inlet temperatures and flows of the three '
     'water circuits and the solution pump speed. From these seven inputs it has to predict sixteen quantities, including the '
     'cooling output, the chilled-water temperature, the heat drawn, all four vessel temperatures, both pressures and the salt '
     'concentrations. It never sees the true outputs while predicting, so it has to keep track of the plant\'s state on its own.')
para('A long short-term memory (LSTM) network suits this, because it carries a memory of what has happened so far. We used two '
     'LSTM layers of 128 units, trained three copies with different random starting points, and average their predictions. '
     'For comparison, we also trained two simpler models based on gradient boosting: one that sees only the current inputs, and one '
     'that also sees the recent history of the inputs.')
table('Accuracy on the 34 unseen test runs (average over all outputs).',
      ['Model', 'R²', 'Average error*'],
      [['Gradient boosting, current inputs only', '0.745', '6.1 %'],
       ['Gradient boosting with input history', '0.978', '2.1 %'],
       ['LSTM, single network', '0.9991', '0.39 %'],
       ['LSTM, three networks averaged (final)', '0.9991', '0.38 %']],
      [8.6, 2.4, 3.6], num_cols=(1, 2))
para('* Root-mean-square error as a percentage of each output\'s range.', size=9, color=GREY)
para('The model without memory cannot cope with a machine that takes half an hour to settle, and the history-based model still '
     'misses where the chiller finally settles after a step. The LSTM follows both almost exactly (Figure 5). In practical terms, '
     'its typical error is 0.3 kW in cooling output, 0.02 °C in chilled-water temperature and 0.01 % in salt concentration. On the '
     'five 12-hour daily profiles, which are the closest to real operation, the R² is 0.9999.')
figure(ROOT / 'ML_model/outputs/figures/test_runs_prediction.png',
       'Three test runs the AI never saw: random changes (top), a single step (middle) and a full day (bottom). '
       'Black: dynamic model; blue dashes: LSTM; orange: history-based gradient boosting.', 16.5)

# ---------------------------------------------------------------- 6 dashboard
doc.add_heading('6. The digital twin dashboard', level=1)
para('To make the model usable without Python, we exported the trained weights and rewrote the network\'s calculation in '
     'JavaScript, so it runs directly in a web browser. Its predictions agree with the original PyTorch model to within 0.002 kW, '
     'and one minute of plant time takes about 1.5 milliseconds to compute.')
para('The dashboard is laid out like a plant control screen. A 3D model of the chiller, arranged like the Aspen flowsheet, '
     'shows the flow in every pipe and the live temperature, pressure and flow of every stream. Users can pick a situation, such '
     'as a sunny day, a drop in hot-water temperature or a hot afternoon at the cooling tower, or move the inputs themselves and '
     'watch the chiller respond. Separate pages show trend charts, a full stream table and a replay of the test runs, so the '
     'accuracy can be checked by anyone.')
figure(ROOT / 'docs/images/dashboard_plant_light.jpg', 'Plant screen of the dashboard: model browser, 3D view, properties and live readings.', 15.0)
figure(HERE / 'figures/fig7_3d_generator.png', 'The generator (DESAT) selected in the 3D view, with the separator drum on the right and the live readings below.', 10.0)
para('The dashboard is hosted on Vercel at libr-chiller-twin.vercel.app, and the complete project, including models, data, code '
     'and documentation, is available on GitHub at github.com/darshanprajapati07/Absorption_chiller.')

# ---------------------------------------------------------------- 7 conclusions
doc.add_heading('7. Conclusions', level=1)
bullets(['The Aspen model\'s low COP came from bookkeeping errors, not from the chemistry. Seven specification changes, with no new '
         'blocks, brought the energy balance within 0.05 % and the COP to a physically sound 0.61.',
         'A compact dynamic model, calibrated to the corrected Aspen case, reproduces it exactly and agrees with all 163 sensitivity cases.',
         'An LSTM trained on 197 simulated runs predicts sixteen chiller quantities from seven inputs with an average R² of 0.9991 on '
         'runs it never saw, far better than models without memory.',
         'The trained model runs in an ordinary web browser, which makes a fast, interactive digital twin of the chiller possible.'])

doc.add_heading('8. Limitations and next steps', level=1)
para('The AI has learned from the dynamic model, not from a real machine, so it is only as good as that model. The metal masses '
     'and liquid hold-ups were estimated by scaling a published 10 kW unit, and they set how fast the chiller responds. The '
     'predictions are reliable only within the range of conditions used in training, and runs that crystallised or froze were left '
     'out, so the model can warn when the plant nears those limits but cannot describe what happens beyond them.')
para('The natural next steps are to calibrate the dynamic model and fine-tune the network with measured data from a real chiller, '
     'to add the chiller\'s own control system, and to use the network inside a predictive controller that keeps the chilled water '
     'on target while staying clear of crystallisation.')

# ---------------------------------------------------------------- references
doc.add_heading('References', level=1)
refs = ['Herold, K.E., Radermacher, R. and Klein, S.A. (2016). Absorption Chillers and Heat Pumps, 2nd ed. CRC Press.',
        'Kohlenbach, P. and Ziegler, F. (2008). A dynamic simulation model for transient absorption chiller performance. '
        'Part I: The model. International Journal of Refrigeration, 31, 217–225.',
        'ASHRAE (2021). ASHRAE Handbook — Fundamentals. Properties of water / lithium-bromide solutions.',
        'Wagner, W. and Kretzschmar, H.-J. (2008). International Steam Tables: IAPWS-IF97. Springer.',
        'Hochreiter, S. and Schmidhuber, J. (1997). Long short-term memory. Neural Computation, 9, 1735–1780.',
        'AspenTech. Aspen Plus user documentation: ELECNRTL property method.']
for i, rtext in enumerate(refs, 1):
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.8); p.paragraph_format.first_line_indent = Cm(-0.8)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f'[{i}]  {rtext}'); r.font.size = Pt(10)

doc.save(OUT)
print('saved', OUT.name, 'figures:', FIG[0], 'tables:', TAB[0])
