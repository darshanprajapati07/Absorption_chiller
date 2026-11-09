function [xss, A, max_rate] = steady_state(u, P, xinit)
%STEADY_STATE  Steady state of the dynamic model for constant inputs u.
%   Integrates the ODEs with constant inputs for 12 h (stiff solver, so this
%   is cheap) and returns the final state. Total solution, LiBr and
%   refrigerant charge are conserved, so the steady state is unique.
if nargin < 3, xinit = P.x0; end
opts = odeset('RelTol', 1e-7, 'AbsTol', 1e-8);
[~, x] = ode15s(@(t, x) model_ode(t, x, @(t) u, P), [0 12*3600], xinit, opts);
xss = x(end, :)';
A = model_algebraic(xss, u, P);
dx = model_ode(0, xss, @(t) u, P);
scale = [1 100 100 1 1 10 1 100 100]';
max_rate = max(abs(dx./scale));
end
