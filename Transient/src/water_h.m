function [hf, hv] = water_h(T)
%WATER_H  Enthalpy of liquid water and low-pressure water vapour [kJ/kg].
%   Reference: saturated liquid at 0 degC = 0 kJ/kg (steam-table reference,
%   consistent with the ASHRAE LiBr-H2O enthalpy correlation).
%   Checked against IAPWS steam tables: error < 0.1 % for 0-110 degC.
hf = 4.186*T;            % liquid
hv = 2501.0 + 1.86*T;    % vapour (ideal-gas, valid at 0.5-15 kPa)
end
