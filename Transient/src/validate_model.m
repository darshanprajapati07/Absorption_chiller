function V = validate_model(P, outdir)
%VALIDATE_MODEL  Validation of the dynamic model before dataset generation.
%   A. Steady state at design inputs vs Aspen base case
%   B. Thermodynamic core vs all 163 valid Aspen SENS-1 cases
%   C. Step response (hot water +10 K): time constants and plot
a = P.D.aspen;
L = {};

%% A. Base case
[xss, S, rate] = steady_state(P.u0, P);
L{end+1} = 'A. STEADY STATE AT DESIGN INPUTS vs ASPEN PLUS BASE CASE';
L{end+1} = sprintf('   (max scaled dx/dt at steady state = %.2e)', rate);
L{end+1} = sprintf('   %-28s %12s %12s %10s', 'Quantity', 'Aspen', 'Model', 'Diff');
rows = {'Generator T [C]', a.T_G, S.T_G; 'Condenser T [C]', a.T_C, S.T_C; ...
    'Evaporator T [C]', a.T_E, S.T_E; 'Absorber T [C]', a.T_A, S.T_A; ...
    'Strong solution x [wt%]', a.x_s, S.x_G; 'Weak solution x [wt%]', a.x_w, S.x_A; ...
    'Refrigerant flow [kg/h]', a.m_ref*3600, S.m_GC*3600; 'SHX strong out T5 [C]', a.T5, S.T5; ...
    'SHX weak out T3 [C]', a.T3, S.T3};
for i = 1:size(rows,1)
    L{end+1} = sprintf('   %-28s %12.3f %12.3f %+9.3f', rows{i,1}, rows{i,2}, rows{i,3}, rows{i,3} - rows{i,2}); %#ok<AGROW>
end
rows = {'Q_gen [kW]', a.Q_gen, S.Q_gen; 'Q_evap [kW]', a.Q_evap, S.Q_evap; ...
    'Q_cond [kW]', a.Q_cond, S.Q_cond; 'Q_abs [kW]', a.Q_abs, S.Q_abs; ...
    'Q_shx [kW]', a.Q_shx, S.Q_shx; 'COP [-]', a.COP, S.Q_evap/S.Q_gen};
for i = 1:size(rows,1)
    L{end+1} = sprintf('   %-28s %12.3f %12.3f %+8.2f %%', rows{i,1}, rows{i,2}, rows{i,3}, (rows{i,3}/rows{i,2} - 1)*100); %#ok<AGROW>
end
res = S.Q_gen + S.Q_evap - S.Q_cond - S.Q_abs;
L{end+1} = sprintf('   Model energy residual Q_gen+Q_evap-Q_cond-Q_abs = %.2e kW', res);
L{end+1} = '   Note: states match Aspen exactly (calibrated). Duties differ by up to ~3.5 %';
L{end+1} = '   because the dynamic model uses ASHRAE LiBr-H2O enthalpies, whereas Aspen uses';
L{end+1} = '   ELECNRTL (different heat of mixing). Q_evap (pure water) matches exactly.';
V.base = S; V.base_rate = rate; V.xss = xss;

%% B. Thermodynamic core vs SENS-1
L{end+1} = '';
L{end+1} = 'B. THERMODYNAMIC CORE vs 163 VALID ASPEN SENS-1 CASES';
L{end+1} = '   (same T_gen, T_cond, T_evap, x_weak = 57.4 wt%, pump 1 kg/s, T5 = 53.3 C)';
Tab = readtable(fullfile(fileparts(outdir), 'data', 'SENS1_ML_dataset.csv'));
n = height(Tab);
M = zeros(n, 6);  Asp = zeros(n, 6);
for i = 1:n
    M(i,:) = core_point(Tab.T_strong_C(i), Tab.T_cond_C(i), Tab.T_evap_C(i), P);
    Asp(i,:) = [Tab.x_strong_wt(i), Tab.m_ref_kg_h(i), Tab.T_abs_out_C(i), Tab.Q_gen_kW(i), Tab.Q_evap_kW(i), Tab.COP(i)];
end
nm = {'x_strong [wt%]', 'm_ref [kg/h]', 'T_abs_out [C]', 'Q_gen [kW]', 'Q_evap [kW]', 'COP [-]'};
L{end+1} = sprintf('   %-16s %12s %12s %12s %14s', 'Quantity', 'mean bias', 'mean |err|', 'max |err|', 'mean |err| %');
for j = 1:6
    e = M(:,j) - Asp(:,j);
    L{end+1} = sprintf('   %-16s %12.3f %12.3f %12.3f %13.2f%%', nm{j}, mean(e), mean(abs(e)), max(abs(e)), mean(abs(e)./abs(Asp(:,j)))*100); %#ok<AGROW>
end
V.core_model = M; V.core_aspen = Asp;
r = corrcoef(M(:,6), Asp(:,6));
L{end+1} = sprintf('   COP correlation model vs Aspen: R = %.4f', r(1,2));

fig = figure('Position', [100 100 900 380]);
subplot(1,2,1); plot(Asp(:,6), M(:,6), 'o'); hold on; lims = [min(Asp(:,6)) max(Asp(:,6))]; plot(lims, lims, 'k--');
xlabel('COP Aspen'); ylabel('COP dynamic-model core'); title('COP: model vs Aspen (163 cases)'); grid on
subplot(1,2,2); plot(Asp(:,2), M(:,2), 'o'); hold on; lims = [min(Asp(:,2)) max(Asp(:,2))]; plot(lims, lims, 'k--');
xlabel('m_{ref} Aspen [kg/h]'); ylabel('m_{ref} model [kg/h]'); title('Refrigerant flow'); grid on
exportgraphics(fig, fullfile(outdir, 'figures', 'validation_vs_aspen_SENS1.png'), 'Resolution', 150); close(fig);

%% C. Step response: hot water +10 K
L{end+1} = '';
L{end+1} = 'C. STEP RESPONSE: HOT WATER INLET +10 K AT t = 0';
u1 = P.u0; u1(1) = u1(1) + 10;
opts = odeset('RelTol', 1e-7, 'AbsTol', 1e-8, 'MaxStep', 10);
[t, x] = ode15s(@(t, x) model_ode(t, x, @(t) u1, P), 0:10:4*3600, xss, opts);
Y = zeros(numel(t), 5);
for i = 1:numel(t)
    s = model_algebraic(x(i,:)', u1, P);
    Y(i,:) = [s.Q_gen, s.Q_evap, s.T_chw_out, s.x_G, s.Q_evap/s.Q_gen];
end
lbl = {'Q_gen [kW]', 'Q_evap [kW]', 'T_chw_out [C]', 'x_strong [wt%]', 'COP [-]'};
L{end+1} = sprintf('   %-16s %10s %10s %10s %10s', 'Output', 'initial', 'final', 't63 [min]', 't95 [min]');
for j = 2:4
    y0 = [S.Q_gen, S.Q_evap, S.T_chw_out, S.x_G, S.Q_evap/S.Q_gen]; y0 = y0(j);
    yf = Y(end, j);  d = abs(Y(:,j) - y0)/abs(yf - y0);
    t63 = t(find(d >= 0.632, 1))/60;  t95 = t(find(d >= 0.95, 1))/60;
    L{end+1} = sprintf('   %-16s %10.3f %10.3f %10.1f %10.1f', lbl{j}, y0, yf, t63, t95); %#ok<AGROW>
end
L{end+1} = sprintf('   %-16s %10.3f %10.3f   (peak %.1f kW just after the step, then decays)', lbl{1}, S.Q_gen, Y(end,1), max(Y(:,1)));
L{end+1} = sprintf('   %-16s %10.3f %10.3f', lbl{5}, S.Q_evap/S.Q_gen, Y(end,5));
fig = figure('Position', [100 100 1000 600]);
for j = 1:5
    subplot(2,3,j); plot(t/60, Y(:,j), 'LineWidth', 1.2); grid on; xlabel('time [min]'); title(lbl{j});
end
sgtitle('Step response: hot water inlet 105 \rightarrow 115 C');
exportgraphics(fig, fullfile(outdir, 'figures', 'step_response_hot_water.png'), 'Resolution', 150); close(fig);
V.lines = L;
end

function y = core_point(TG, TC, TE, P)
% Steady-state thermodynamic core (same correlations as the dynamic model)
xw = P.D.aspen.x_w;  mp = 1;  T5 = P.D.aspen.T5;
xs  = fzero(@(x) duhring_T(x, TC) + P.dTG_eq - TG, [50 75]);
mr  = mp*(1 - xw/xs);  mss = mp - mr;
TA  = duhring_T(xw, TE) + P.dTA_eq;
hG  = h_sol(xs, TG);
Qshx = mss*(hG - h_sol(xs, T5));
h3  = h_sol(xw, TA) + Qshx/mp;
TvG = min(TG, duhring_T(xw, TC) + P.dTG_eq);
[~, hvG] = water_h(TvG);  [hfC, ~] = water_h(TC);  [~, hvE] = water_h(TE);
QG = mss*hG + mr*hvG - mp*h3;
QE = mr*(hvE - hfC);
y = [xs, mr*3600, TA, QG, QE, QE/QG];
end
