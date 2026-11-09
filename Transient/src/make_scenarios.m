function S = make_scenarios(P, mode)
%MAKE_SCENARIOS  Input profiles for the transient dataset.
%   Inputs u = [T_hw m_hw T_cw m_cw T_chw m_chw m_pump].
%   Each scenario: knot times t [s] and input matrix U (linear interpolation
%   between knots; steps are applied as 1-s ramps).
%   mode = 'full' (about 200 runs) or 'quick' (6 runs, for testing).
if nargin < 2, mode = 'full'; end
rng(2026);                                    % reproducible dataset
u0 = P.u0;
S = struct('type', {}, 'desc', {}, 't', {}, 'U', {}, 'tend', {});

% Operating ranges (absolute for temperatures, relative for flows)
% (chosen so that a chiller without freeze-protection control stays above
%  0 degC in the evaporator for most combinations; nominal T_evap is 1.74 C)
R.T_hw  = [90 110];  R.T_cw = [25 32];  R.T_chw = [11.5 16];
R.flow  = [0.80 1.15];  R.pump = [0.85 1.10];

%% 1. Single steps (step at 15 min, 3 h run)
steps = {1,  [5 10 -5 -10], 'abs', 'Hot water inlet T';
         2,  [0.2 -0.2],    'rel', 'Hot water flow';
         3,  [2 4 -2 -4],   'abs', 'Cooling water inlet T';
         4,  [0.2 -0.2],    'rel', 'Cooling water flow';
         5,  [2 -2 3 -1.5], 'abs', 'Chilled water inlet T';
         6,  [0.2 -0.2],    'rel', 'Chilled water flow';
         7,  [0.1 -0.1],    'rel', 'Solution pump flow'};
for i = 1:size(steps, 1)
    k = steps{i,1};
    for d = steps{i,2}
        u1 = u0;
        if strcmp(steps{i,3}, 'abs'), u1(k) = u0(k) + d; else, u1(k) = u0(k)*(1 + d); end
        S(end+1) = mk('step', sprintf('%s step %+g%s', steps{i,4}, d, unit(steps{i,3})), ...
            [0 900 901 3*3600], [u0; u0; u1; u1], 3*3600); %#ok<AGROW>
    end
end

%% 2. Ramps (start at 15 min, 4 h run)
ramps = {1, 10, [10 30 60]; 1, -10, [10 30 60]; 3, 3, [30 60]; 3, -3, [30 60]; 5, 2.5, [30 60]; 5, -2, [30 60]};
for i = 1:size(ramps, 1)
    k = ramps{i,1};
    for dur = ramps{i,3}
        u1 = u0; u1(k) = u0(k) + ramps{i,2};
        S(end+1) = mk('ramp', sprintf('%s ramp %+g K over %d min', P.input_names{k}, ramps{i,2}, dur), ...
            [0 900 900+60*dur 4*3600], [u0; u0; u1; u1], 4*3600); %#ok<AGROW>
    end
end
for sgn = [1 -1]
    u1 = u0; u1(1) = u0(1) + 10*sgn; u1(3) = u0(3) + 3*sgn;
    S(end+1) = mk('ramp', sprintf('Combined hot + cooling water ramp (%+d) over 30 min', sgn), ...
        [0 900 2700 4*3600], [u0; u0; u1; u1], 4*3600); %#ok<AGROW>
end

%% 3. Start-up / shut-down style (low hot water <-> design hot water)
for Tlow = [80 85]
    for Thigh = [105 110]
        ul = u0; ul(1) = Tlow; uh = u0; uh(1) = Thigh;
        S(end+1) = mk('startup',  sprintf('Hot water %g -> %g C', Tlow, Thigh),  [0 900 1500 4*3600], [ul; ul; uh; uh], 4*3600); %#ok<AGROW>
        S(end+1) = mk('shutdown', sprintf('Hot water %g -> %g C', Thigh, Tlow), [0 900 1500 4*3600], [uh; uh; ul; ul], 4*3600); %#ok<AGROW>
    end
end

%% 4. Daily profiles (12 h, solar-type hot water, ambient cooling water, load)
for r = 1:5
    tk = (0:600:12*3600)';  ph = tk/(12*3600);
    U = repmat(u0, numel(tk), 1);
    U(:,1) = 92 + (15 + 4*rand)*sin(pi*ph) + 0.8*randn(size(tk));
    U(:,3) = 25 + (3 + 2*rand)*sin(pi*ph) + 0.3*randn(size(tk));
    U(:,5) = 11 + (2.5 + rand)*sin(pi*ph) + 0.3*randn(size(tk));
    U(:,1) = min(max(U(:,1), 85), 115);
    S(end+1) = mk('daily', sprintf('Daily profile %d (12 h)', r), tk, U, 12*3600); %#ok<AGROW>
end

%% 5. APRBS random multi-input sequences (4 h)
nA = 150;
for r = 1:nA
    tend = 4*3600;
    lo = [R.T_hw(1), u0(2)*R.flow(1), R.T_cw(1), u0(4)*R.flow(1), R.T_chw(1), u0(6)*R.flow(1), u0(7)*R.pump(1)];
    hi = [R.T_hw(2), u0(2)*R.flow(2), R.T_cw(2), u0(4)*R.flow(2), R.T_chw(2), u0(6)*R.flow(2), u0(7)*R.pump(2)];
    % each input switches independently; hold 5-30 min, 30-s transition
    tk_all = [];
    seg = cell(1, 7);
    for k = 1:7
        tt = 0; vv = lo(k) + (hi(k) - lo(k))*rand;
        while tt(end) < tend
            hold = 300 + 1500*rand;
            tn = tt(end) + hold;
            vn = lo(k) + (hi(k) - lo(k))*rand;
            tt = [tt, tn, tn + 30]; vv = [vv, vv(end), vn]; %#ok<AGROW>
        end
        seg{k} = [tt; vv];
        tk_all = [tk_all, tt]; %#ok<AGROW>
    end
    tk = unique([tk_all, tend]); tk = tk(tk <= tend)';
    U = zeros(numel(tk), 7);
    for k = 1:7, U(:,k) = interp1(seg{k}(1,:), seg{k}(2,:), tk, 'linear', 'extrap'); end
    S(end+1) = mk('aprbs', sprintf('Random multi-input sequence %d', r), tk, U, tend); %#ok<AGROW>
end

if strcmp(mode, 'quick')
    pick = [1, 3, find(strcmp({S.type}, 'ramp'), 1), find(strcmp({S.type}, 'startup'), 1), ...
            find(strcmp({S.type}, 'daily'), 1), find(strcmp({S.type}, 'aprbs'), 1)];
    S = S(pick);
end
end

function s = mk(type, desc, t, U, tend)
s = struct('type', type, 'desc', desc, 't', t(:), 'U', U, 'tend', tend);
end

function s = unit(kind)
if strcmp(kind, 'abs'), s = ' K'; else, s = ' (fraction)'; end
end
