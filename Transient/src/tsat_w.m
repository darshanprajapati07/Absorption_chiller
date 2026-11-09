function T = tsat_w(P)
%TSAT_W  Saturation temperature of water [degC] from pressure [Pa].
%   IAPWS-IF97 region 4 backward equation (vectorised).
n = [0.11670521452767e4, -0.72421316703206e6, -0.17073846940092e2, ...
     0.12020824702470e5, -0.32325550322333e7,  0.14915108613530e2, ...
    -0.48232657361591e4,  0.40511340542057e6, -0.23855557567849, ...
     0.65017534844798e3];
beta = (P/1e6).^0.25;
E = beta.^2 + n(3)*beta + n(6);
F = n(1)*beta.^2 + n(4)*beta + n(7);
G = n(2)*beta.^2 + n(5)*beta + n(8);
D = 2*G./(-F - sqrt(F.^2 - 4*E.*G));
T = (n(10) + D - sqrt((n(10) + D).^2 - 4*(n(9) + n(10)*D)))/2 - 273.15;
end
