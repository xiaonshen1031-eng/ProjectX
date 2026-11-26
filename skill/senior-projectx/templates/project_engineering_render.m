function project_engineering_render(planPath, output)
% Render checked ProjectX geometry as editable vector objects in MATLAB.
file = fopen(planPath, 'r', 'n', 'UTF-8');
assert(file ~= -1, 'Cannot open the figure plan.');
handle = onCleanup(@() fclose(file));
plan = jsondecode(fscanf(file, '%c'));
clear handle
assert(strcmp(plan.schema, 'projectx.engineering-figure.v1'), 'Unsupported figure plan.');
fonts = listfonts;
cjkAliases = {plan.fonts.cjk, char([24494 36719 38597 40657])}; % Localized name Windows can report for Microsoft YaHei.
assert(any(strcmpi(fonts, plan.fonts.latin)) && any(ismember(lower(string(fonts)), lower(string(cjkAliases)))), ...
    'Install the font families requested by the plan before exporting.');
[folder, ~, suffix] = fileparts(output);
assert(any(strcmpi(suffix, {'.emf', '.png', '.pdf'})), 'Use an .emf, .png, or .pdf output.');
if strcmpi(suffix, '.emf'), assert(ispc, 'Native EMF print requires Windows MATLAB.'); end
if ~isempty(folder) && ~isfolder(folder), mkdir(folder); end
sizeIn = plan.canvas_mm(:)' / 25.4;
fig = figure('Color', 'white', 'Visible', 'off', 'Units', 'inches', ...
    'Position', [.5 .5 sizeIn], 'PaperUnits', 'inches', 'PaperPosition', [0 0 sizeIn], 'PaperSize', sizeIn);
closeFig = onCleanup(@() close(fig));
for i = 1:numel(plan.panels)
    spec = plan.panels(i);
    a = axes(fig, 'Position', spec.position, 'Units', 'normalized', 'XLim', spec.xlim, 'YLim', spec.ylim, ...
        'Box', 'off', 'FontName', plan.fonts.latin, 'FontSize', plan.fonts.tick_pt, 'FontWeight', 'normal', ...
        'TickDir', 'out', 'TickLength', [.006 .006], 'LineWidth', .75, ...
        'XColor', tone('ink'), 'YColor', tone('ink'), 'GridColor', tone('grid'), 'GridAlpha', 1, ...
        'TickLabelInterpreter', 'tex');
    hold(a, 'on');
    if ~spec.axis, axis(a, 'off'); end
    xlabel(a, runs(spec.xlabel), 'FontSize', plan.fonts.axis_pt, 'Interpreter', 'tex');
    ylabel(a, runs(spec.ylabel), 'FontSize', plan.fonts.axis_pt, 'Interpreter', 'tex');
    if spec.xtick_explicit, a.XTick = spec.xtick; end
    if spec.ytick_explicit, a.YTick = spec.ytick; end
    if strcmp(spec.grid, 'x'), a.XGrid = 'on'; end
    if strcmp(spec.grid, 'y'), a.YGrid = 'on'; end
    if ~isempty(spec.xticklabels), a.XTickLabel = cellfun(@runs, spec.xticklabels, 'UniformOutput', false); end
    if ~isempty(spec.yticklabels), a.YTickLabel = cellfun(@runs, spec.yticklabels, 'UniformOutput', false); end
    marks = spec.layers;
    if ~iscell(marks), marks = num2cell(marks); end
    for j = 1:numel(marks)
        mark = marks{j};
        switch mark.kind
            case 'line'
                plot(a, mark.x, mark.y, 'Color', tone(mark.color), 'LineWidth', mark.width, 'LineStyle', mark.style);
            case 'polygon'
                patch(a, mark.x, mark.y, tone(mark.face), 'EdgeColor', tone(mark.edge), 'LineWidth', mark.width);
            case 'points'
                symbol = mark.marker;
                if strcmp(symbol, 'P'), symbol = 'p'; end
                plot(a, mark.x, mark.y, 'LineStyle', 'none', 'Marker', symbol, 'MarkerFaceColor', tone(mark.face), ...
                    'MarkerEdgeColor', tone(mark.edge), 'MarkerSize', mark.size, 'LineWidth', mark.width);
            case 'text'
                text(a, mark.x, mark.y, runs(mark.label), 'FontName', plan.fonts.latin, 'FontSize', mark.size, ...
                    'Color', tone(mark.color), 'HorizontalAlignment', mark.align, 'VerticalAlignment', 'middle', 'Interpreter', 'tex');
            otherwise
                error('Unsupported mark kind %s.', mark.kind);
        end
    end
end
drawnow;
for object = reshape(findall(fig, 'Type', 'text'), 1, [])
    if isempty(object.String), continue; end
    oldUnits = object.Units;
    object.Units = 'normalized';
    bounds = object.Extent;
    axesPos = object.Parent.Position;
    lowerBound = axesPos(1:2) + bounds(1:2) .* axesPos(3:4);
    upperBound = lowerBound + bounds(3:4) .* axesPos(3:4);
    object.Units = oldUnits;
    assert(all(lowerBound >= -.003) && all(upperBound <= 1.003), ...
        'Text lies outside the page after MATLAB rendering: %s', object.String);
end
switch lower(suffix)
    case '.emf', print(fig, output, '-dmeta', '-vector');
    case '.pdf', print(fig, output, '-dpdf', '-vector');
    otherwise, print(fig, output, '-dpng', '-r600');
end

    function rgb = tone(role)
        if strcmp(role, 'none'), rgb = 'none'; return; end
        hex = plan.palette.(role);
        rgb = sscanf(hex(2:end), '%2x', [1 3]) / 255;
    end

    function styled = runs(value)
        chars = double(value);
        mask = (chars >= hex2dec('3400') & chars <= hex2dec('9fff')) | ...
               (chars >= hex2dec('3000') & chars <= hex2dec('303f')) | ...
               (chars >= hex2dec('ff00') & chars <= hex2dec('ffef'));
        breaks = find(diff([false mask false]));
        styled = '';
        cursor = 1;
        for index = 1:2:numel(breaks)
            first = breaks(index);
            last = breaks(index+1)-1;
            styled = [styled escape_tex(value(cursor:first-1)) '\fontname{' plan.fonts.cjk '}\bf ' ...
                escape_tex(value(first:last)) '\fontname{' plan.fonts.latin '}\rm ']; %#ok<AGROW>
            cursor = last+1;
        end
        styled = [styled escape_tex(value(cursor:end))];
    end
end

function escaped = escape_tex(value)
escaped = regexprep(value, '([_\^{}])', '\\$1');
end
