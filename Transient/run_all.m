function run_all(mode)
%RUN_ALL  One-command pipeline: calibrate -> validate -> simulate -> export.
%
%   run_all            full dataset (199 transient runs, ~5-10 min)
%   run_all('quick')   6 runs only, to test the installation (~2 min)
%
%   Outputs (folder ./output):
%     transient_dataset.csv        valid runs, 10-s samples (main ML file)
%     transient_dataset_all.mat    all runs incl. invalid + parameters
%     run_summary.csv              one row per run with checks
%     data_dictionary.csv          column names, units, descriptions
%     model_parameters.csv         calibrated model parameters
%     validation_report.txt        validation against Aspen + dataset checks
%     figures/*.png                validation and example plots
if nargin < 1, mode = 'full'; end
t_start = tic;
root = fileparts(mfilename('fullpath'));
addpath(fullfile(root, 'src'));
outdir = fullfile(root, 'output');
if ~exist(fullfile(outdir, 'figures'), 'dir'), mkdir(fullfile(outdir, 'figures')); end
set(0, 'DefaultFigureVisible', 'off');
warning('off', 'MATLAB:ode15s:IntegrationTolNotMet');

fprintf('\n=== Absorption chiller transient dataset generator (%s mode) ===\n', mode);

%% 1. Calibrate the dynamic model on the validated Aspen base case
fprintf('[1/5] Calibrating model on Aspen base case ... ');
D = design_point();
P = calibrate_model(D);
write_parameters(P, fullfile(outdir, 'model_parameters.csv'));
fprintf('done (nominal steady-state residual %.1e)\n', P.design.max_dxdt);

%% 2. Validate before generating data
fprintf('[2/5] Validating model (base case, 163 Aspen cases, step test) ... ');
V = validate_model(P, outdir);
fprintf('done\n');

%% 3. Scenarios
S = make_scenarios(P, mode);
fprintf('[3/5] %d transient scenarios created\n', numel(S));

%% 4. Simulate
fprintf('[4/5] Simulating ...\n');
tables = cell(numel(S), 1);
infos  = cell(numel(S), 1);
for i = 1:numel(S)
    [tables{i}, infos{i}] = simulate_scenario(S(i), P, i, 10);
    if mod(i, 10) == 0 || i == numel(S)
        el = toc(t_start);
        fprintf('      run %3d / %3d  (%5.1f min elapsed, ~%4.1f min left)\n', i, numel(S), el/60, el/60/i*(numel(S) - i));
    end
end
info = struct2table([infos{:}]', 'AsArray', true);
info.type = string(info.type);  info.desc = string(info.desc);

%% 5. Export
fprintf('[5/5] Exporting ...\n');
valid = info.valid;
% train/validation/test split by whole run (daily profiles kept for test)
rng(7);
split = strings(height(info), 1);
idx = find(valid & info.type ~= "daily");
idx = idx(randperm(numel(idx)));
nt = round(0.70*numel(idx));  nv = round(0.15*numel(idx));
split(idx(1:nt)) = "train";  split(idx(nt+1:nt+nv)) = "validation";  split(idx(nt+nv+1:end)) = "test";
split(valid & info.type == "daily") = "test";
split(~valid) = "excluded";
info.split = split;

for i = 1:numel(tables)
    if ~isempty(tables{i})
        tables{i}.split = repmat(split(i), height(tables{i}), 1);
    end
end
Tall = vertcat(tables{:});
Tvalid = Tall(ismember(Tall.run_id, info.run_id(valid)), :);
writetable(Tvalid, fullfile(outdir, 'transient_dataset.csv'));
writetable(info, fullfile(outdir, 'run_summary.csv'));
write_dictionary(fullfile(outdir, 'data_dictionary.csv'));
save(fullfile(outdir, 'transient_dataset_all.mat'), 'Tall', 'info', 'P', 'S', 'V', '-v7.3');
plot_examples(Tvalid, info, fullfile(outdir, 'figures'));

%% Report
L = V.lines;
L{end+1} = '';
L{end+1} = 'D. TRANSIENT DATASET';
L{end+1} = sprintf('   Runs simulated: %d   valid: %d   excluded: %d', height(info), sum(valid), sum(~valid));
types = unique(info.type);
for k = 1:numel(types)
    m = info.type == types(k);
    L{end+1} = sprintf('   %-9s runs %3d  valid %3d', types(k), sum(m), sum(m & valid)); %#ok<AGROW>
end
L{end+1} = sprintf('   Rows in transient_dataset.csv: %d  (sample time 10 s)', height(Tvalid));
L{end+1} = sprintf('   Split (runs): train %d, validation %d, test %d', sum(split == "train"), sum(split == "validation"), sum(split == "test"));
L{end+1} = sprintf('   Energy conservation error per run: max %.4f %%, mean %.4f %% (limit %.1f %%)', ...
    max(info.energy_err_pct), mean(info.energy_err_pct, 'omitnan'), D.lim.energy_err_pct);
L{end+1} = sprintf('   Valid data ranges: COP_avg30 %.3f-%.3f, Q_evap %.1f-%.1f kW, x_strong %.2f-%.2f wt%%, T_evap %.2f-%.2f C', ...
    min(Tvalid.COP_avg30), max(Tvalid.COP_avg30), min(Tvalid.Q_evap_kW), max(Tvalid.Q_evap_kW), ...
    min(Tvalid.x_strong_wt), max(Tvalid.x_strong_wt), min(Tvalid.T_evap_C), max(Tvalid.T_evap_C));
reasons = info.reason(~valid);
ur = unique(reasons);
for k = 1:numel(ur)
    L{end+1} = sprintf('   excluded because "%s": %d runs', ur{k}, sum(strcmp(reasons, ur{k}))); %#ok<AGROW>
end
L{end+1} = '';
L{end+1} = sprintf('Total run time: %.1f min', toc(t_start)/60);
fid = fopen(fullfile(outdir, 'validation_report.txt'), 'w');
fprintf(fid, 'VALIDATION REPORT - single-effect H2O-LiBr absorption chiller dynamic model\n');
fprintf(fid, 'Generated %s (%s mode)\n\n', char(datetime('now')), mode);
fprintf(fid, '%s\n', L{:});
fclose(fid);
fprintf('%s\n', L{:});
fprintf('\nAll files written to: %s\n', outdir);
end

%% ------------------------------------------------------------------------
function write_parameters(P, file)
n = {'UA_gen','UA_cond','UA_evap','UA_abs','UA_shx','k_vap_gen','k_vap_abs', ...
     'dT_eq_gen','dT_eq_abs','dT_dyn_gen','dT_dyn_abs','m_strong_nominal', ...
     'Mc_gen','Mc_cond','Mc_evap','Mc_abs','M_sol_gen0','M_sol_abs0','M_ref_evap0', ...
     'T_hw_in_nom','m_hw_nom','T_cw_in_nom','m_cw_nom','T_chw_in_nom','m_chw_nom','m_pump_nom'};
v = [P.UA_G, P.UA_C, P.UA_E, P.UA_A, P.UA_shx, P.kG, P.kA, P.dTG_eq, P.dTA_eq, P.dTG, P.dTA, P.mss0, ...
     P.Mc.G, P.Mc.C, P.Mc.E, P.Mc.A, P.MG0, P.MA0, P.ME0, P.u0];
u = {'kW/K','kW/K','kW/K','kW/K','kW/K','kg/s/Pa','kg/s/Pa','K','K','K','K','kg/s', ...
     'kJ/K','kJ/K','kJ/K','kJ/K','kg','kg','kg','C','kg/s','C','kg/s','C','kg/s','kg/s'};
s = {'calibrated','calibrated','calibrated','calibrated','calibrated (Aspen T5)','calibrated','calibrated', ...
     'Aspen vs ASHRAE equilibrium','Aspen vs ASHRAE equilibrium','incl. vapour driving dP','incl. vapour driving dP', ...
     'Aspen base','assumed','assumed','assumed','assumed','assumed','assumed','assumed', ...
     'design choice','design (8 K drop)','design choice','design (3.5 K rise in absorber)','design choice','design (12->7 C)','Aspen base'};
writetable(table(n', v', u', s', 'VariableNames', {'parameter','value','unit','source'}), file);
end

function write_dictionary(file)
d = {
'run_id','-','Run number (see run_summary.csv)'
'scenario_type','-','step / ramp / startup / shutdown / daily / aprbs'
'time_s','s','Time since start of the run (inputs constant before t = 0)'
'T_hw_in_C','C','INPUT: hot water inlet temperature (generator)'
'm_hw_kg_s','kg/s','INPUT: hot water flow'
'T_cw_in_C','C','INPUT: cooling water inlet temperature (absorber, then condenser in series)'
'm_cw_kg_s','kg/s','INPUT: cooling water flow'
'T_chw_in_C','C','INPUT: chilled water inlet temperature (evaporator)'
'm_chw_kg_s','kg/s','INPUT: chilled water flow'
'm_pump_kg_s','kg/s','INPUT: weak solution pump flow'
'T_gen_C','C','Generator solution temperature (= strong solution outlet)'
'T_cond_C','C','Condenser temperature (= Tsat at high pressure)'
'T_evap_C','C','Evaporator temperature (= Tsat at low pressure)'
'T_abs_C','C','Absorber solution temperature (= weak solution outlet)'
'T_shx_weak_out_C','C','Weak solution leaving SHX to generator (Aspen stream 3)'
'T_shx_strong_out_C','C','Strong solution leaving SHX to absorber (Aspen stream 5)'
'x_strong_wt','wt% LiBr','Strong solution concentration (generator)'
'x_weak_wt','wt% LiBr','Weak solution concentration (absorber)'
'P_high_kPa','kPa','High-side pressure (condenser)'
'P_low_kPa','kPa','Low-side pressure (evaporator)'
'm_ref_gen_kg_s','kg/s','Refrigerant vapour generated (generator -> condenser)'
'm_ref_abs_kg_s','kg/s','Refrigerant vapour absorbed (evaporator -> absorber)'
'm_strong_kg_s','kg/s','Strong solution flow generator -> absorber'
'M_gen_kg','kg','Solution inventory in generator'
'M_abs_kg','kg','Solution inventory in absorber'
'M_evap_kg','kg','Refrigerant inventory in evaporator'
'Q_gen_kW','kW','Heat input to generator from hot water (briefly negative if hot water drops below the generator temperature)'
'Q_cond_kW','kW','Heat rejected by condenser to cooling water'
'Q_evap_kW','kW','Cooling capacity (heat taken from chilled water)'
'Q_abs_kW','kW','Heat rejected by absorber to cooling water'
'Q_shx_kW','kW','Internal heat recovered in solution heat exchanger'
'T_hw_out_C','C','Hot water outlet temperature'
'T_cw_mid_C','C','Cooling water between absorber and condenser'
'T_cw_out_C','C','Cooling water outlet temperature'
'T_chw_out_C','C','Chilled water outlet temperature (main controlled output of a chiller)'
'COP_inst','-','Instantaneous Q_evap / Q_gen (can exceed 1 briefly when hot water drops, because stored refrigerant keeps cooling)'
'COP_avg30','-','Energy-based COP over trailing 30 min = sum(Q_evap)/sum(Q_gen) (recommended COP target; >1 only during shut-down, when stored refrigerant still cools)'
'flag_crystallisation','bool','TRUE if x_strong > 64 wt% (never TRUE in the valid file)'
'flag_freezing','bool','TRUE if T_evap < 0 C (never TRUE in the valid file)'
'split','-','Suggested ML split by whole run: train / validation / test'};
writetable(cell2table(d, 'VariableNames', {'column','unit','description'}), file);
end

function plot_examples(T, info, figdir)
types = ["step", "ramp", "aprbs", "daily"];
fig = figure('Position', [100 100 1200 800]);
for k = 1:numel(types)
    id = info.run_id(find(info.valid & info.type == types(k), 1));
    if isempty(id), continue, end
    r = T(T.run_id == id, :);
    th = r.time_s/3600;
    subplot(4,3,3*k-2); plot(th, r.T_hw_in_C, th, r.T_cw_in_C, th, r.T_chw_in_C); grid on
    ylabel('T_{in} [C]'); title(sprintf('%s (run %d): inputs', types(k), id)); legend('hot','cooling','chilled','Location','best');
    subplot(4,3,3*k-1); plot(th, r.Q_gen_kW, th, r.Q_evap_kW); grid on; ylabel('kW'); title('Q_{gen}, Q_{evap}'); legend('Q_{gen}','Q_{evap}','Location','best');
    subplot(4,3,3*k);   plot(th, r.T_chw_out_C); grid on; ylabel('C'); title('Chilled water outlet');
    for c = 3*k-2:3*k, subplot(4,3,c); xlim([0 max(th)]); end
end
for k = 10:12, subplot(4,3,k); xlabel('time [h]'); end
exportgraphics(fig, fullfile(figdir, 'example_runs.png'), 'Resolution', 130); close(fig);
end
