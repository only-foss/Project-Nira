% =============================================================
% Project Nira — Open Hardware Microplastics Detector
% File:    nira_analysis.m
% Purpose: Main analysis entry point — load data, compute
%          statistics, run Welch t-test, call all plot functions
%
% SPDX-License-Identifier: GPL-3.0-or-later
% Copyright (C) 2026  only-foss
% Repository: https://github.com/only-foss/Project-Nira
%
% This program is free software: you can redistribute it and/or
% modify it under the terms of the GNU General Public License as
% published by the Free Software Foundation, either version 3 of
% the License, or (at your option) any later version.
%
% This program is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
% GNU General Public License for more details.
% <https://www.gnu.org/licenses/>
%
% Hardware licensed under CERN-OHL-P v2
% <https://cern-ohl.web.cern.ch/>
% =============================================================
%
% Usage:
%   cd tests/analysis/
%   octave nira_analysis.m
%
% Input files (must be in same directory):
%   clean_water.csv   — pivoted clean water data
%   micro_water.csv   — pivoted microplastic data
%
% Output:
%   Console: statistics report + t-test result
%   tests/results/nira_01_timeseries.png
%   tests/results/nira_02_comparison.png
%   tests/results/nira_03_histogram.png
%   tests/results/nira_04_scatter.png
%
% CSV column order: _time, ch1_raw, ch4_raw, diff_c1_c4
% Data exported from InfluxDB measurement: nira_sensor
% Device tag: nira_esp32
% =============================================================

clear; clc; close all;

printf('==============================================\n');
printf(' Project Nira - Microplastic Sensor Analysis\n');
printf(' v1.0  |  github.com/only-foss/Project-Nira  \n');
printf('==============================================\n\n');

% ---- Load Data -----------------------------------------------
% textscan skips timestamp string; no extra packages required

fid = fopen('clean_water.csv');
fgetl(fid);  % skip header line
raw_clean = textscan(fid, '%s %f %f %f', 'Delimiter', ',');
fclose(fid);

fid = fopen('micro_water.csv');
fgetl(fid);  % skip header line
raw_micro = textscan(fid, '%s %f %f %f', 'Delimiter', ',');
fclose(fid);

clean_ch1  = raw_clean{2};
clean_ch4  = raw_clean{3};
clean_diff = raw_clean{4};

micro_ch1  = raw_micro{2};
micro_ch4  = raw_micro{3};
micro_diff = raw_micro{4};

n_clean = length(clean_diff);
n_micro = length(micro_diff);

% ---- Console Statistics Report --------------------------------
printf('--- Clean Water (%d samples) ---\n', n_clean);
printf('  ch1_raw    : mean=%.2f  std=%.2f  min=%.2f  max=%.2f\n', ...
       mean(clean_ch1), std(clean_ch1), min(clean_ch1), max(clean_ch1));
printf('  ch4_raw    : mean=%.2f  std=%.2f  min=%.2f  max=%.2f\n', ...
       mean(clean_ch4), std(clean_ch4), min(clean_ch4), max(clean_ch4));
printf('  diff(c1-c4): mean=%.2f  std=%.2f  min=%.2f  max=%.2f\n\n', ...
       mean(clean_diff), std(clean_diff), min(clean_diff), max(clean_diff));

printf('--- Water with Microplastics (%d samples) ---\n', n_micro);
printf('  ch1_raw    : mean=%.2f  std=%.2f  min=%.2f  max=%.2f\n', ...
       mean(micro_ch1), std(micro_ch1), min(micro_ch1), max(micro_ch1));
printf('  ch4_raw    : mean=%.2f  std=%.2f  min=%.2f  max=%.2f\n', ...
       mean(micro_ch4), std(micro_ch4), min(micro_ch4), max(micro_ch4));
printf('  diff(c1-c4): mean=%.2f  std=%.2f  min=%.2f  max=%.2f\n\n', ...
       mean(micro_diff), std(micro_diff), min(micro_diff), max(micro_diff));

% ---- Detection Metric -----------------------------------------
delta_mean = mean(micro_diff) - mean(clean_diff);
printf('--- Key Detection Metric ---\n');
printf('  Clean baseline mean : %.2f ADC\n', mean(clean_diff));
printf('  Microplastic mean   : %.2f ADC\n', mean(micro_diff));
printf('  Shift               : %.2f ADC  (%.1f sigma above clean)\n', ...
       delta_mean, delta_mean / std(clean_diff));

threshold = (mean(clean_diff) + mean(micro_diff)) / 2;
printf('  Suggested threshold : %.2f ADC units\n\n', threshold);

% ---- Two-Sample Welch t-Test ----------------------------------
% Manual implementation — no statistics package required
n1 = n_clean; n2 = n_micro;
m1 = mean(clean_diff); m2 = mean(micro_diff);
v1 = var(clean_diff);  v2 = var(micro_diff);
t_stat = (m1 - m2) / sqrt(v1/n1 + v2/n2);
% Welch-Satterthwaite degrees of freedom
df = (v1/n1 + v2/n2)^2 / ((v1/n1)^2/(n1-1) + (v2/n2)^2/(n2-1));
% Two-tailed p-value via betainc (base Octave built-in)
x  = df / (df + t_stat^2);
p  = betainc(x, df/2, 0.5);

printf('--- Two-Sample Welch t-Test (diff_c1_c4) ---\n');
printf('  t-statistic        : %.4f\n', t_stat);
printf('  Degrees of freedom : %.1f\n', df);
printf('  p-value            : %.2e\n\n', p);
if p < 0.001
  printf('  >> HIGHLY significant difference (p < 0.001)\n\n');
elseif p < 0.05
  printf('  >> Significant difference (p < 0.05)\n\n');
else
  printf('  >> No significant difference detected.\n\n');
end

% ---- Create results directory if needed -----------------------
results_dir = fullfile('..', 'results');
if ~exist(results_dir, 'dir')
  mkdir(results_dir);
  printf('Created output directory: %s\n\n', results_dir);
end

% ---- Visualizations (PNGs saved to tests/results/) ------------
nira_plot_timeseries(clean_ch1, clean_ch4, clean_diff, ...
                     micro_ch1, micro_ch4, micro_diff, results_dir);
nira_plot_comparison(clean_diff, micro_diff, threshold, results_dir);
nira_plot_histogram(clean_diff, micro_diff, threshold, results_dir);
nira_plot_scatter(clean_ch1, clean_ch4, micro_ch1, micro_ch4, results_dir);

printf('>> All plots saved to: %s\n', results_dir);
printf('>> Analysis complete.\n');
