# SENS-1 setup in Aspen Plus: click-by-click guide

Follow the parts **in order**. After Parts 1, 2 and 3, run the simulation once and check the result before going on.
Throughout this guide, **Navigator** means the tree on the left side of the Aspen window, in the Simulation environment.

---

## Part 0: Before you start

1. Open `absorption.apw`.
2. Click **File → Save As**. Name the copy **`absorption_SENS.apw`**. Now the original stays safe.
3. Make sure the DESHEAT1 fix is done. Open **Blocks → DESHEAT1 → Input → Specifications**. It should show **Pressure = 10200 Pa** and **Duty = 0**, with **no temperature**.

---

## Part 1: Set the pressures (one master pressure per side)

The idea: only the **PUMP** decides the high pressure and only **VALVE** decides the low pressure. Every other block gets a pressure of **0**, which in Aspen means "no pressure drop, keep the inlet pressure".

### 1.1 PUMP (check only)
1. In the Navigator, open **Blocks → PUMP → Setup**.
2. On the **Specifications** tab, confirm that **Discharge pressure = 10200 N/sqm** (10200 Pa).
3. Change nothing.

### 1.2 Heater blocks on the high side
Do this for each of these blocks, one at a time: **COLD, HOT, DESHEAT1, DESAT, DESHEAT3.**

1. In the Navigator, open **Blocks → (block name) → Input**.
2. Open the **Specifications** tab.
3. Find the **Pressure** box and type **0**. Keep its unit as N/sqm, or any unit, because 0 is 0 in every unit.
4. Leave the other specification exactly as it is:

| Block | Flash Type row 1 | Flash Type row 2 |
|---|---|---|
| COLD | Pressure = 0 | (nothing else; the duty comes from QSHX) |
| HOT | Pressure = 0 | Temperature = 53.3 C |
| DESHEAT1 | Pressure = 0 | Duty = 0 |
| DESAT | Pressure = 0 | Temperature = 89.9 C |
| DESHEAT3 | Pressure = 0 | Temperature = 78.4 C |

### 1.3 DFLASH (Flash2)
1. Open **Blocks → DFLASH → Input → Specifications**.
2. Set **Flash Type** to **Pressure** and **Duty**.
3. Enter **Pressure = 0** and **Duty = 0**.

### 1.4 CONDENS
1. Open **Blocks → CONDENS → Input → Specifications**.
2. In the first **Flash Type** dropdown, choose **Pressure**. In the second, choose **Vapor fraction**.
3. Enter **Pressure = 0** and **Vapor fraction = 0**.
4. If a Temperature box is still filled, clear it.

The condenser outlet is now saturated liquid. The condenser temperature follows automatically from the pump pressure.

### 1.5 VALVE (check only)
1. Open **Blocks → VALVE → Input → Operation**.
2. Confirm **Calculation type = Adiabatic flash for specified outlet pressure** and **Outlet pressure = 697 N/sqm**.

### 1.6 EVAP and ABSORB
For **both** blocks:
1. Open **Blocks → EVAP** (then **ABSORB**) **→ Input → Specifications**.
2. Set **Pressure = 0**.
3. Keep **Vapor fraction** as it is: EVAP = **1**, ABSORB = **0**.

### 1.7 Run and check
1. On the **Home** ribbon, click **Reinitialize** (or press Shift+F5), then click **OK**.
2. Click **Run** (or press F5).
3. Check **Control Panel**. It should show **no errors**; warnings are acceptable.
4. Open **Results Summary → Streams**. Check:
   - Streams **2, 3, 4, 5, 7, 8, A, B, C** have a pressure of about **0.1007 atm** (10,200 Pa).
   - Streams **6, 9, 10, 1A** have a pressure of about **0.00688 atm** (697 Pa).
   - Stream **8** is liquid, at about **46 °C**.
5. Work out **COP = Q_EVAP / (Q_DESHEAT1 + Q_DESAT + Q_DFLASH + Q_DESHEAT3)**. It should be **about 0.60–0.61**.
6. Click **File → Save**.

---

## Part 2: Create Calculator C-PLOW

This makes SOLVALVE and stream 1 always use the same low pressure as VALVE.

### 2.1 Create it
1. In the Navigator, expand **Flowsheeting Options** and click **Calculator**.
2. Click **New…**. Type the ID **`C-PLOW`** and click **OK**.

### 2.2 Define tab: add 3 variables
For each variable:
- Click **New…**, type the variable name, and click **OK**.
- In the panel that opens, fill in the fields from the table.
- Choose **Import** or **Export** with the radio button.

| Variable name | Import / Export | Category | Type | Block / Stream | Variable | Units |
|---|---|---|---|---|---|---|
| **PLOW** | **Import** | Blocks | Block-Var | Block = **VALVE** | **P-OUT** (sentence PARAM) | **N/sqm** |
| **PSV** | **Export** | Blocks | Block-Var | Block = **SOLVALVE** | **P-OUT** (sentence PARAM) | **N/sqm** |
| **P1** | **Export** | Streams | Stream-Var | Stream = **1**, Substream = **MIXED** | **PRES** | **N/sqm** |

### 2.3 Calculate tab
1. Select **Fortran**.
2. In the white box, type exactly these two lines. **Start each line with 6 spaces.**
```
      PSV = PLOW
      P1  = PLOW
```

### 2.4 Sequence tab
Select **Use import/export variables**. This is usually the default.

### 2.5 Run and check
1. Click **Reinitialize**, then **Run**.
2. The results should be **the same as Part 1**.
3. Open **Calculator → C-PLOW → Results**. **PSV** and **P1** should both be 697.
4. Click **File → Save**.

---

## Part 3: Edit SENS-1, the Vary tab

1. In the Navigator, expand **Model Analysis Tools → Sensitivity** and click **SENS-1**.
2. If SENS-1 is greyed out, right-click it and choose **Activate**.
3. Open **SENS-1 → Input → Vary** tab.
4. **Delete the old variables.** In the **Variable number** dropdown, select 1. Right-click and choose **Delete**, or use the delete button. Repeat until all 4 old variables are gone.

### 3.1 Add the new Vary variables
In the **Variable** dropdown, choose **New** and fill in the fields. Repeat for each row.

**Vary 1: Generator temperature**
- Manipulated variable: **Type = Block-Var**, **Block = DESAT**, **Variable = TEMP**, **Units = C**.
- Values: select **List of values**. Type: `86 88 90 92 94 96 98 100`.
- Report labels (optional): Line 1 = `TGEN`.

**Vary 2: High pressure (sets the condenser temperature)**
- Manipulated variable: **Type = Block-Var**, **Block = PUMP**, **Variable = PRES**, **Units = N/sqm**.
- Values: select **List of values**. Type: `6632 7384 8209 9112 10200`.
- These values mean T_cond = 38, 40, 42, 44, 46.2 °C.
- Report label: `PHIGH`.

**Vary 3: Low pressure (sets the evaporator temperature)**
- Manipulated variable: **Type = Block-Var**, **Block = VALVE**, **Variable = P-OUT**, **Units = N/sqm**.
- Values: select **List of values**. Type: `696 758 814 873 935 1002`.
- These values mean T_evap = 1.8, 3, 4, 5, 6, 7 °C.
- Report label: `PLOW`.

Do **not** add ABSORB TEMP or EVAP TEMP. They are now results, not inputs. That is why the old error appeared.

Total cases = 8 × 5 × 6 = **240**.

---

## Part 4: Edit SENS-1, the Define tab

1. Open the **Define** tab.
2. **Delete the old variables** (QEVAP, QDES, QABS, QCOND). Select each one and click **Delete**.
3. For each row below:
   - Click **New…**, type the name, and click **OK**.
   - Fill in **Category**, **Type**, **Block/Stream**, **Variable** and **Units**.
   - Click **Close** (or go back to the Define tab).

### 4.1 Block heat duties
For all of these: **Category = Blocks**, **Type = Block-Var**, **Variable = QCALC**, **Units = kcal/hr**.

| Name | Block |
|---|---|
| **QD1** | DESHEAT1 |
| **QDES** | DESAT |
| **QDFL** | DFLASH |
| **QDS3** | DESHEAT3 |
| **QCOND** | CONDENS |
| **QEVAP** | EVAP |
| **QABS** | ABSORB |
| **QSHX** | HOT |

### 4.2 Pump work
| Name | Category | Type | Block | Variable | Units |
|---|---|---|---|---|---|
| **WPUMP** | Blocks | Block-Var | PUMP | **WNET** (net work). If WNET is not in the list, use **ELEC-POWER** or **BRAKE-POWER**. | **kW** |

### 4.3 Stream results
For all of these: **Category = Streams**, **Substream = MIXED**.

| Name | Type | Stream | Variable | Component | Units |
|---|---|---|---|---|---|
| **MREF** | Stream-Var | C | MASS-FLOW | (none) | kg/hr |
| **M4** | Stream-Var | 4 | MASS-FLOW | (none) | kg/hr |
| **T1** | Stream-Var | 1A | TEMP | — | C |
| **T3** | Stream-Var | 3 | TEMP | — | C |
| **T4** | Stream-Var | 4 | TEMP | — | C |
| **T6** | Stream-Var | 6 | TEMP | — | C |
| **T8** | Stream-Var | 8 | TEMP | — | C |
| **T10** | Stream-Var | 10 | TEMP | — | C |
| **VF1A** | Stream-Var | 1A | VFRAC | — | — |
| **VF8** | Stream-Var | 8 | VFRAC | — | — |
| **VF10** | Stream-Var | 10 | VFRAC | — | — |

That makes 20 defined variables in total.

---

## Part 5: Edit SENS-1, the Tabulate tab

1. Open the **Tabulate** tab.
2. Delete the old rows: select each row, right-click and choose **Delete**.
3. Click **Fill Variables**. Aspen adds all 20 defined variables as columns 1–20.
4. Click the first empty row (column 21) and type each expression below in the **Tabulated variable or expression** box:

| Column | Type this expression | What it is |
|---|---|---|
| 21 | `QD1+QDES+QDFL+QDS3` | Q_gen (external generator heat) |
| 22 | `QEVAP/(QD1+QDES+QDFL+QDS3)` | **COP** |
| 23 | `QD1+QDES+QDFL+QDS3+QEVAP+QCOND+QABS+WPUMP*859.845` | Energy residual, which should be close to 0 |
| 24 | `2066.4/M4*100` | Strong-solution LiBr wt% |

5. Optionally, click **Table Format → Column headings** and give columns 21–24 the labels **QGEN**, **COP**, **RES** and **XSTRONG**.

---

## Part 6: Run SENS-1

1. Click **Reinitialize**, then **OK**.
2. Click **Run** (F5). The 240 cases take a few minutes. Watch the **Control Panel**; it shows "Sensitivity Block SENS-1 Row … begins".
3. When it finishes, check that the Control Panel's last line says **Results available** or **with warnings**. Warnings are acceptable. **Errors are not.**
4. Click **File → Save**.

---

## Part 7: Export the results to Excel

1. In the Navigator, open **Model Analysis Tools → Sensitivity → SENS-1 → Results**.
2. Open the **Summary** tab. You will see 240 rows, a **Status** column, the 3 varied inputs, and the 24 result columns.
3. Click the top-left corner of the table to select everything. Press **Ctrl+C**.
4. Open a new Excel file and press **Ctrl+V** in cell A1.
5. Save it as **`SENS1_results.xlsx`**.

---

## Part 8: Clean the data in Excel (delete bad rows)

Add a column **VALID** with this formula. Replace the column letters with your own.

```
=AND(Status="OK", MREF>0.5, VF8<0.001, VF10>0.999, VF1A<0.001, T3<T4, XSTRONG<=64, ABS(RES)/QGEN<0.005)
```

Keep only the rows where VALID = TRUE. Here is what each check means:

| Check | Why |
|---|---|
| Status = OK | The case converged |
| MREF > 0.5 kg/h | The generator really boils off water. If not, the generator temperature is too low. |
| VF8 ≈ 0 | The condenser outlet is liquid |
| VF10 ≈ 1 | The evaporator outlet is vapour |
| VF1A ≈ 0 | The absorber outlet is liquid |
| T3 < T4 | The solution heat exchanger is feasible (no temperature cross) |
| XSTRONG ≤ 64 % | No crystallisation risk |
| \|RES\| / QGEN < 0.5 % | The energy balance closes |

---

## Part 9: Quick sanity check of the trends

Make 3 quick charts from the valid rows:

| Chart | Expected trend |
|---|---|
| COP vs generator temperature (fixed T_cond, T_evap) | Rises, then flattens |
| COP vs PHIGH (condenser temperature) | **Falls** as the pressure goes up |
| COP vs PLOW (evaporator temperature) | **Rises** as the pressure goes up |
| MREF vs PLOW | Stays constant. This is expected, because stream 1 fixes the weak solution at 57.4 %. |

If all the trends match, the dataset is ready for ML. Send me `SENS1_results.xlsx` and I will check it.

---

## If you get an error

| Message | Fix |
|---|---|
| "VARIABLE IS NOT SPECIFIED IN THE BLOCK" | You are varying something that is not an input spec in that block, for example a temperature in a block set by vapour fraction. Check the Vary tab against Part 3. |
| Calculator error about stream 1 PRES | Open **Streams → 1 → Input → Mixed**. The state variables must be **Pressure** and **Vapor fraction (= 0)**. Then the Calculator can overwrite the pressure. |
| Some sensitivity rows show "Errors" | Usually these are cases with a very low generator temperature (no boiling) or a high one (concentration too high). They are removed in Part 8, so this is acceptable. |
| Wegstein / QSHX not converging | Open **Convergence → Conv Options → Defaults → Sequential Modular** and raise **Maximum flowsheet evaluations** to **200**. |
