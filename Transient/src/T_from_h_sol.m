function T = T_from_h_sol(x, h)
%T_FROM_H_SOL  Solution temperature [degC] from enthalpy [kJ/kg] and x [wt%].
%   Inverts the quadratic-in-T ASHRAE correlation used in h_sol.m.
h0 = h_sol(x, 0);                  % a(x)
[~, b] = h_sol(x, 0);              % hT at T=0 equals b(x)
[h1, ~] = h_sol(x, 1);
c = h1 - h0 - b;                   % c(x)
d = h - h0;
% numerically stable small root of c*T^2 + b*T - d = 0
T = 2*d./(b + sqrt(b.^2 + 4*c.*d));
end
