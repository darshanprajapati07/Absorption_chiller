function [T, info] = simulate_scenario(sc, P, run_id, dt)
%SIMULATE_SCENARIO  Run one transient scenario from the steady state that
%   corresponds to its initial inputs. Returns a table sampled every dt
%   seconds and a summary struct with validity checks.
if nargin < 4, dt = 10; end
lim = P.D.lim;
F = griddedInterpolant(sc.t, sc.U, 'linear', 'nearest');
uFun = @(t) F(t);

info = struct('run_id', run_id, 'type', sc.type, 'desc', sc.desc, 'duration_h', sc.tend/3600, ...
    'ok_solver', false, 'max_x_strong', NaN, 'min_T_evap', NaN, 'min_M_evap', NaN, ...
    'energy_err_pct', NaN, 'valid', false, 'reason', '');
T = table();
try
    % 1. initial steady state for the initial inputs
    [x_init, ~, rate] = steady_state(sc.U(1,:), P);
    if rate > 1e-5, error('initial steady state not reached (rate %.2g)', rate); end
    % 2. transient
    tgrid = (0:dt:sc.tend)';
    opts = odeset('RelTol', 1e-6, 'AbsTol', 1e-7, 'MaxStep', dt);
    [t, x] = ode15s(@(t, x) model_ode(t, x, uFun, P), tgrid, x_init, opts);
    if numel(t) ~= numel(tgrid), error('solver stopped at t = %.0f s', t(end)); end
    info.ok_solver = true;
catch err
    info.reason = ['solver: ' err.message];
    return
end

%% 3. post-processing
n = numel(t);
names = {'T_gen_C','T_cond_C','T_evap_C','T_abs_C','T_shx_weak_out_C','T_shx_strong_out_C', ...
    'x_strong_wt','x_weak_wt','P_high_kPa','P_low_kPa','m_ref_gen_kg_s','m_ref_abs_kg_s', ...
    'm_strong_kg_s','M_gen_kg','M_abs_kg','M_evap_kg','Q_gen_kW','Q_cond_kW','Q_evap_kW', ...
    'Q_abs_kW','Q_shx_kW','T_hw_out_C','T_cw_mid_C','T_cw_out_C','T_chw_out_C','COP_inst'};
Y = zeros(n, numel(names));  Uin = zeros(n, 7);  Ust = zeros(n, 1);
for i = 1:n
    u = uFun(t(i));  Uin(i,:) = u;
    a = model_algebraic(x(i,:)', u, P);
    Y(i,:) = [a.T_G, a.T_C, a.T_E, a.T_A, a.T3, a.T5, a.x_G, a.x_A, a.P_C/1e3, a.P_E/1e3, ...
        a.m_GC, a.m_EA, a.m_ss, a.M_G, a.M_A, a.M_E, a.Q_gen, a.Q_cond, a.Q_evap, a.Q_abs, ...
        a.Q_shx, a.T_hw_out, a.T_cw_mid, a.T_cw_out, a.T_chw_out, a.Q_evap/a.Q_gen];
    Ust(i) = a.U;
end

%% 4. checks
% energy conservation: dU = integral of (Q_gen + Q_evap - Q_cond - Q_abs)
Qnet = Y(:,17) + Y(:,19) - Y(:,18) - Y(:,20);
dU = Ust(end) - Ust(1);
info.energy_err_pct = abs(dU - trapz(t, Qnet))/trapz(t, abs(Y(:,17)))*100;
info.max_x_strong = max(Y(:,7));
info.min_T_evap   = min(Y(:,3));
info.min_M_evap   = min(Y(:,16));
flag_cryst  = Y(:,7) > lim.x_cryst;
flag_freeze = Y(:,3) < lim.T_E_min;
reasons = {};
if any(flag_cryst),  reasons{end+1} = sprintf('x_strong > %g wt%% (crystallisation risk)', lim.x_cryst); end
if any(flag_freeze), reasons{end+1} = sprintf('T_evap < %g C (freezing risk)', lim.T_E_min); end
if info.min_M_evap < 2, reasons{end+1} = 'evaporator dry-out'; end
if info.energy_err_pct > lim.energy_err_pct, reasons{end+1} = 'energy closure > 1%'; end
info.valid  = isempty(reasons);
info.reason = strjoin(reasons, '; ');

%% 5. table
T = array2table([t, Uin, Y], 'VariableNames', [{'time_s'}, P.input_names, names]);
T = addvars(T, repmat(run_id, n, 1), repmat(string(sc.type), n, 1), 'Before', 1, ...
    'NewVariableNames', {'run_id', 'scenario_type'});
% energy-based COP over a trailing 30-min window (robust to thermal storage)
w = round(1800/dt);
T.COP_avg30 = movsum(Y(:,19), [w-1 0])./movsum(Y(:,17), [w-1 0]);
T.flag_crystallisation = flag_cryst;
T.flag_freezing = flag_freeze;
end
