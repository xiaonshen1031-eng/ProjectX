function build_matlab_engineering(selected, language)
% Draw the saved engineering examples as native MATLAB plots and vector EMFs.
root = fileparts(fileparts(mfilename('fullpath')));
if nargin < 1, selected = []; end
if nargin < 2, language = 'en'; end
catalog = jsondecode(fileread(fullfile(root, 'gallery', 'catalog.json')));
data = jsondecode(fileread(fullfile(root, 'gallery', 'engineering-data.json')));
out = fullfile(root, 'docs', 'downloads', 'figures', 'matlab');
if strcmp(language, 'zh'), out = fullfile(out, 'zh'); end
if ~exist(out, 'dir'), mkdir(out); end
for i = 1:numel(catalog.charts)
    if iscell(catalog.charts), chart = catalog.charts{i}; else, chart = catalog.charts(i); end
    if ~isfield(chart, 'source') || ~strcmp(chart.source, 'engineering'), continue; end
    if ~isempty(selected) && ~any(strcmp(cellstr(selected), chart.id)), continue; end
    fixture = data.charts.(matlab.lang.makeValidName(chart.id));
    fig = render_figure(fixture.panels);
    cleanup = onCleanup(@()close(fig));
    apply_figure_language(fig, language);
    print(fig, fullfile(out, [chart.id '.emf']), '-dmeta', '-vector');
    clear cleanup
    fprintf('MATLAB EMF: %s %s\n', language, chart.id);
end
end

function fig = render_figure(panels)
fig = figure('Color', 'w', 'Visible', 'off', 'Units', 'inches', 'Position', [1 1 16 9.6], ...
    'PaperUnits', 'inches', 'PaperPosition', [0 0 16 9.6], 'PaperSize', [16 9.6]);
ink = gallery_color('ink');
gridColor = gallery_color('grid');
for i = 1:numel(panels)
    spec = panels(i);
    a = axes(fig, 'Position', spec.position, 'FontName', 'Times New Roman', 'FontSize', 13, ...
        'Box', 'off', 'XColor', ink, 'YColor', ink, 'LineWidth', .7, ...
        'XLim', spec.xlim, 'YLim', spec.ylim, 'GridColor', gridColor, ...
        'GridAlpha', 1, 'TickDir', 'out', 'TickLength', [.004 .004]);
    hold(a, 'on');
    if ~spec.axis, axis(a, 'off'); end
    if ~isempty(spec.xlabel), xlabel(a, spec.xlabel, 'FontSize', 16); end
    if ~isempty(spec.ylabel), ylabel(a, spec.ylabel, 'FontSize', 16); end
    if ~isempty(spec.xtick) || (isempty(spec.xtick) && isempty(spec.xticklabels) && ...
            (spec.axis && isempty(spec.xlabel)))
        a.XTick = spec.xtick;
    end
    if ~isempty(spec.ytick) || (spec.axis && isempty(spec.ylabel))
        a.YTick = spec.ytick;
    end
    if ~isempty(spec.xticklabels), a.XTickLabel = spec.xticklabels; end
    if ~isempty(spec.yticklabels), a.YTickLabel = spec.yticklabels; end
    if strcmp(spec.grid, 'x'), a.XGrid = 'on'; end
    if strcmp(spec.grid, 'y'), a.YGrid = 'on'; end
    marks = spec.layers;
    if ~iscell(marks), marks = num2cell(marks); end
    for j = 1:numel(marks)
        mark = marks{j};
        switch mark.kind
            case 'line'
                plot(a, mark.x, mark.y, 'Color', figure_color(mark.color), ...
                    'LineWidth', mark.width, 'LineStyle', mark.style);
            case 'polygon'
                patch(a, mark.x, mark.y, figure_color(mark.face), ...
                    'EdgeColor', figure_color(mark.edge), 'LineWidth', mark.width);
            case 'points'
                plot(a, mark.x, mark.y, 'LineStyle', 'none', 'Marker', mark.marker, ...
                    'MarkerFaceColor', figure_color(mark.face), 'MarkerEdgeColor', figure_color(mark.edge), ...
                    'MarkerSize', mark.size, 'LineWidth', mark.width);
            case 'text'
                text(a, mark.x, mark.y, mark.label, 'FontName', 'Times New Roman', ...
                    'FontSize', mark.size, 'Color', figure_color(mark.color), ...
                    'HorizontalAlignment', mark.align, 'VerticalAlignment', 'middle', 'Interpreter', 'none');
            otherwise
                error('Unknown engineering mark %s.', mark.kind);
        end
    end
end
drawnow;
end

function value = figure_color(role)
switch role
    case 'none'
        value = 'none';
    case 'white'
        value = [1 1 1];
    otherwise
        value = gallery_color(role);
end
end
