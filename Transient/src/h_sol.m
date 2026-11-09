function [h, hT, hx] = h_sol(x, T)
%H_SOL  Specific enthalpy of aqueous LiBr solution [kJ/kg] and derivatives.
%   x : LiBr mass fraction [wt%]   (valid 40-70 wt%)
%   T : temperature [degC]         (valid 15-165 degC)
%   hT = dh/dT [kJ/kg/K], hx = dh/dx [kJ/kg per wt%]
%   Source: ASHRAE Handbook - Fundamentals, LiBr-H2O enthalpy correlation
%   h = sum(A_n x^n) + T*sum(B_n x^n) + T^2*sum(C_n x^n)
A = [-2024.33, 163.309, -4.88161, 6.302948e-2, -2.913705e-4];
B = [18.2829, -1.1691757, 3.248041e-2, -4.034184e-4, 1.8520569e-6];
C = [-3.7008214e-2, 2.8877666e-3, -8.1313015e-5, 9.9116628e-7, -4.4441207e-9];
[a, da] = poly4(A, x);
[b, db] = poly4(B, x);
[c, dc] = poly4(C, x);
h  = a + T.*b + T.^2.*c;
hT = b + 2*T.*c;
hx = da + T.*db + T.^2.*dc;
end

function [p, dp] = poly4(K, x)
p  = K(1) + x.*(K(2) + x.*(K(3) + x.*(K(4) + x.*K(5))));
dp = K(2) + x.*(2*K(3) + x.*(3*K(4) + x.*4*K(5)));
end
