% =============================================================
% Project Nira - Microplastic Detection Sensor Analysis
% GNU Octave Analysis Script
% GitHub: https://github.com/only-foss/Project-Nira
% =============================================================
% Sensor: nira_esp32 | Fields: ch1_raw, ch4_raw, diff_c1_c4
% Test 0: Clean Water
% Test 1: Water with Microplastics
% =============================================================

clear; clc; close all;

printf('==============================================\n');
printf(' Project Nira - Microplastic Sensor Analysis\n');
printf('==============================================\n\n');

% ---- Load Data -----------------------------------------------
% CSV columns: _time, ch1_raw, ch4_raw, diff_c1_c4
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

% ---- Two-Sample Welch t-Test (manual, no statistics package needed) ---
n1 = n_clean; n2 = n_micro;
m1 = mean(clean_diff); m2 = mean(micro_diff);
v1 = var(clean_diff);  v2 = var(micro_diff);
t_stat = (m1 - m2) / sqrt(v1/n1 + v2/n2);
% Welch-Satterthwaite degrees of freedom
df = (v1/n1 + v2/n2)^2 / ((v1/n1)^2/(n1-1) + (v2/n2)^2/(n2-1));
% Two-tailed p-value via betainc (base Octave, no package needed)
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

% ---- Visualizations -------------------------------------------
nira_plot_timeseries(clean_ch1, clean_ch4, clean_diff, ...
                     micro_ch1, micro_ch4, micro_diff);
nira_plot_comparison(clean_diff, micro_diff, threshold);
nira_plot_histogram(clean_diff, micro_diff, threshold);
nira_plot_scatter(clean_ch1, clean_ch4, micro_ch1, micro_ch4);

printf('>> All plots saved as PNG in current directory.\n');
