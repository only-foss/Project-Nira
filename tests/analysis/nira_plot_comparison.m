% =============================================================
% nira_plot_comparison.m
% Bar chart + box plot: mean diff with std error, detection threshold
% Project Nira - https://github.com/only-foss/Project-Nira
% No external packages required.
% =============================================================

function nira_plot_comparison(clean_diff, micro_diff, threshold)

  fig = figure('Position', [100 100 900 500], 'Visible', 'off');

  m1 = mean(clean_diff); m2 = mean(micro_diff);
  s1 = std(clean_diff);  s2 = std(micro_diff);
  bar_w = 0.35;
  cap_w = 0.08;

  % ---- Subplot 1: Bar + manual error bars -----
  subplot(1, 2, 1);
  hold on;

  patch([1-bar_w 1+bar_w 1+bar_w 1-bar_w], [0 0 m1 m1], ...
        [0.2 0.5 0.9], 'EdgeColor', 'k', 'FaceAlpha', 0.85);
  patch([2-bar_w 2+bar_w 2+bar_w 2-bar_w], [0 0 m2 m2], ...
        [0.9 0.3 0.3], 'EdgeColor', 'k', 'FaceAlpha', 0.85);

  for xi = 1:2
    if xi == 1; mu = m1; sg = s1; else mu = m2; sg = s2; end
    plot([xi xi],             [mu-sg mu+sg], 'k-',  'LineWidth', 1.5);
    plot([xi-cap_w xi+cap_w], [mu+sg mu+sg], 'k-',  'LineWidth', 1.5);
    plot([xi-cap_w xi+cap_w], [mu-sg mu-sg], 'k-',  'LineWidth', 1.5);
  end

  plot([0.4 2.6], [threshold threshold], 'g--', 'LineWidth', 1.8);
  plot([0.4 2.6], [0 0],                 'k:',  'LineWidth', 1.0);
  text(2.45, threshold, sprintf('%.0f', threshold), ...
       'Color', [0 0.6 0], 'FontSize', 8);
  set(gca, 'XTick', [1 2], 'XTickLabel', {'Clean Water', 'Microplastics'});
  xlim([0.4 2.6]);
  ylabel('\DeltaADC (CH1 - CH4)');
  title('Mean Differential Signal +/- 1 sigma');
  grid on;

  % ---- Subplot 2: Hand-drawn box plot (no statistics package) -----
  subplot(1, 2, 2);
  hold on;

  datasets = {clean_diff, micro_diff};
  colors   = {[0.2 0.5 0.9], [0.9 0.3 0.3]};
  bw = 0.35;  % box half-width

  for xi = 1:2
    d  = sort(datasets{xi});
    n  = length(d);
    q1 = d(max(1, round(0.25 * n)));
    q2 = d(round(0.50 * n));          % median
    q3 = d(min(n, round(0.75 * n)));
    iqr_val = q3 - q1;
    wlo = max(d(d >= q1 - 1.5*iqr_val));
    whi = min(d(d <= q3 + 1.5*iqr_val));
    outliers = d(d < wlo | d > whi);
    fc = colors{xi};

    % Box
    patch([xi-bw xi+bw xi+bw xi-bw], [q1 q1 q3 q3], fc, ...
          'EdgeColor', 'k', 'FaceAlpha', 0.7, 'LineWidth', 1.2);
    % Median line
    plot([xi-bw xi+bw], [q2 q2], 'k-', 'LineWidth', 2);
    % Whiskers
    plot([xi xi], [wlo q1], 'k-', 'LineWidth', 1.2);
    plot([xi xi], [q3 whi], 'k-', 'LineWidth', 1.2);
    % Whisker caps
    plot([xi-bw*0.5 xi+bw*0.5], [wlo wlo], 'k-', 'LineWidth', 1.2);
    plot([xi-bw*0.5 xi+bw*0.5], [whi whi], 'k-', 'LineWidth', 1.2);
    % Outliers
    if ~isempty(outliers)
      plot(xi * ones(size(outliers)), outliers, 'o', ...
           'MarkerEdgeColor', fc, 'MarkerSize', 5);
    end
  end

  plot([0.4 2.6], [threshold threshold], 'g--', 'LineWidth', 1.8);
  plot([0.4 2.6], [0 0],                 'k:',  'LineWidth', 1.0);
  text(2.35, threshold, sprintf('%.0f', threshold), ...
       'Color', [0 0.6 0], 'FontSize', 8);
  set(gca, 'XTick', [1 2], 'XTickLabel', {'Clean Water', 'Microplastics'});
  xlim([0.4 2.6]);
  ylabel('\DeltaADC (CH1 - CH4)');
  title('Distribution Comparison (Box Plot)');
  grid on;

  axes('Position', [0 0 1 1], 'Visible', 'off');
  text(0.5, 0.99, 'Project Nira - Differential Signal Comparison', ...
       'HorizontalAlignment', 'center', 'VerticalAlignment', 'top', ...
       'FontSize', 13, 'FontWeight', 'bold');

  print(fig, 'nira_02_comparison.png', '-dpng', '-r150');
  close(fig);
  printf('  Saved: nira_02_comparison.png\n');

end
