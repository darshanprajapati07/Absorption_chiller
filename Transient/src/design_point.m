function D = design_point()
%DESIGN_POINT  All fixed data for the dynamic model.
%   Section 1 : validated Aspen Plus base case (SENS-1 row 241)
%   Section 2 : external water circuits (design choice)
%   Section 3 : thermal masses and inventories (assumed, scaled from
%               Kohlenbach & Ziegler 2008, 10 kW unit -> ~80 kW)
%   Section 4 : numerical settings

%% 1. Aspen Plus base case (stream results, 35 degC case after fixes)
D.aspen.T_G   = 89.893;          % generator / strong solution (stream 4) [degC]
D.aspen.T_C   = 46.140;          % condenser outlet (stream 8) [degC]
D.aspen.T_E   = 1.7426;          % evaporator outlet (stream 10) [degC]
D.aspen.T_A   = 33.304;          % absorber outlet (stream 1A) [degC]
D.aspen.T3    = 67.943;          % weak solution leaving SHX [degC]
D.aspen.T5    = 53.300;          % strong solution leaving SHX (HOT spec) [degC]
D.aspen.x_w   = 57.400;          % weak solution LiBr [wt%]
D.aspen.x_s   = 59.488;          % strong solution LiBr [wt%]
D.aspen.m_p   = 3600/3600;       % solution pump flow [kg/s]
D.aspen.m_ss  = 3473.646/3600;   % strong solution flow [kg/s]
D.aspen.m_ref = 126.354/3600;    % refrigerant flow [kg/s]
D.aspen.Q_gen  = 114653.6/859.845;   % [kW]
D.aspen.Q_evap = 69750.05/859.845;   % [kW]
D.aspen.Q_cond = 74074.85/859.845;   % [kW] (heat rejected, positive)
D.aspen.Q_abs  = 110168.5/859.845;   % [kW] (heat rejected, positive)
D.aspen.Q_shx  = 58495.3/859.845;    % [kW]
D.aspen.COP    = D.aspen.Q_evap/D.aspen.Q_gen;

%% 2. External water circuits (design choice, typical single-effect unit)
D.cpw = 4.186;                   % water specific heat [kJ/kg/K]
D.hw.T_in  = 105.0;              % hot water inlet [degC]
D.hw.dT    = 8.0;                % hot water temperature drop at design [K]
D.cw.T_in  = 27.0;               % cooling water inlet [degC] (absorber, then condenser)
D.cw.dT_A  = 3.5;                % cooling water rise in absorber at design [K]
D.chw.T_in = 12.0;               % chilled water inlet [degC]
D.chw.T_out = 7.0;               % chilled water outlet at design [degC]

%% 3. Thermal masses (metal + fixed fluid) and inventories (assumed)
D.Mc.G = 800;                    % generator [kJ/K]
D.Mc.C = 400;                    % condenser [kJ/K]
D.Mc.E = 600;                    % evaporator [kJ/K]
D.Mc.A = 800;                    % absorber  [kJ/K]
D.M0.G = 120;                    % solution hold-up in generator sump [kg]
D.M0.A = 200;                    % solution hold-up in absorber sump [kg]
D.M0.E = 30;                     % refrigerant pool in evaporator [kg]
D.ME_dry = 1.0;                  % evaporator dry-out mass scale [kg]

%% 4. Vapour transfer (quasi-equilibrium) settings
D.dP_frac_G = 0.01;              % generator->condenser driving dP at design (1 % of P)
D.dP_frac_A = 0.01;              % evaporator->absorber driving dP at design (1 % of P)
D.eps_G = 2.0;                   % smoothing of max(dP,0) [Pa]
D.eps_A = 0.2;                   % smoothing of max(dP,0) [Pa]

%% Limits used to flag invalid operation
D.lim.x_cryst = 64.0;            % crystallisation-risk limit on strong solution [wt%]
D.lim.T_E_min = 0.0;             % refrigerant (water) freezing limit [degC]
D.lim.energy_err_pct = 1.0;      % max run energy-closure error [%]
end
