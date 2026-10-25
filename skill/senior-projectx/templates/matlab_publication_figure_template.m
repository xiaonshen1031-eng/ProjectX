function matlab_publication_figure_template(outDir, requiredFormats)
%MATLAB_PUBLICATION_FIGURE_TEMPLATE Evidence-rich publication figure skeleton.
% Replace deterministic demo values with saved experiment data. The layout
% uses explicit physical geometry so EMF export cannot silently crop labels,
% colorbars, or legends. Select the view from the engineering relationship;
% decorative objects or repeated panels cannot create new evidence.
% Lines for true trajectories, regression/identity references or intervals are
% primitives in scientifically sourced diagnostic views, not ranking charts.
% Select the recipe in references/figure-pattern-pool.md first:
% CORR_DUAL_TRI_STREE: one shared data-derived order, masks and aligned tree.
% REGRESSION_ALL_BASELINES: all methods, shared limits/sample IDs, y=x.
% ABLATION_EFFECT_FOREST: retain Full, signed effects and uncertainty.
% Existing one-argument calls remain valid; request FIG/EMF only when needed.

if nargin < 1 || isempty(outDir)
    outDir = fullfile(pwd, 'figure_exports');
end
if nargin < 2 || isempty(requiredFormats), requiredFormats={'pdf','png'}; end
requiredFormats=cellstr(lower(string(requiredFormats)));
assert(all(ismember(requiredFormats,{'fig','emf','pdf','png'})), 'Unsupported export format');
if ~exist(outDir, 'dir'), mkdir(outDir); end

figName = 'Fig_publication_template';
canvas = [16.5 10.2]; % centimeters: final insertion size, rather than a larger authoring canvas
fig = figure('Units','centimeters','Position',[2 2 canvas], ...
    'Color','w','Renderer','painters','PaperUnits','centimeters', ...
    'PaperPosition',[0 0 canvas],'PaperSize',canvas, ...
    'PaperPositionMode','manual','InvertHardcopy','off');
set(fig,'DefaultAxesFontName','Times New Roman', ...
    'DefaultTextFontName','Times New Roman', ...
    'DefaultLegendFontName','Times New Roman');

% Explicit safe regions. Increase canvas or move axes before reducing fonts.
ax1 = axes('Parent',fig,'Units','normalized','Position',[.085 .20 .37 .72]);
ax2 = axes('Parent',fig,'Units','normalized','Position',[.68 .20 .30 .72]);

% Demo evidence: matched mission-level errors for four methods.
rng(7,'twister');
n = 32;
data = [2.82+.20*randn(n,1), 2.69+.18*randn(n,1), ...
        2.61+.17*randn(n,1), 2.50+.15*randn(n,1)];
methodNames = {'Baseline A','Baseline B','Baseline C','Proposed'};
colors = [.34 .53 .72; .30 .66 .50; .88 .58 .18; .80 .16 .18];
% Reuse this keyed identity map across figures; colors are illustrative only.
methodStyle=containers.Map(methodNames,num2cell(colors,2));
% For scalar cells use scientific_colormap(kind,n), then annotation_color(rgb).

% Panel (a): raincloud distributions with raw units and mean/95% CI.
hold(ax1,'on');
for k = 1:size(data,2)
    [yy,dd] = simple_kde(data(:,k),140);
    dd = .32*dd/max(dd);
    patch(ax1,[k+dd fliplr(k+zeros(size(dd)))],[yy fliplr(yy)],methodStyle(methodNames{k}), ...
        'FaceAlpha',.28,'EdgeColor',methodStyle(methodNames{k}),'LineWidth',1.0);
    jitter = -.20 + .10*sin((1:n)'*2.399);
    scatter(ax1,k+jitter,data(:,k),18,methodStyle(methodNames{k}),'filled', ...
        'MarkerFaceAlpha',.58,'MarkerEdgeColor','w','LineWidth',.35);
    mu = mean(data(:,k)); ci = 1.96*std(data(:,k))/sqrt(n);
    errorbar(ax1,k,mu,ci,'k','LineStyle','none','LineWidth',1.4,'CapSize',8);
    scatter(ax1,k,mu,42,'d','MarkerFaceColor','w','MarkerEdgeColor','k','LineWidth',1.1);
end
set(ax1,'XTick',1:4,'XTickLabel',methodNames,'XLim',[.55 4.55]);
ylabel(ax1,'Primary error (unit)');
xlabel(ax1,'Method');
% Add panel letters only when the caption/body refers to them.
set_panel_style(ax1); xtickangle(ax1,18);

% Panel (b): matched effect-size forest versus the first baseline.
hold(ax2,'on');
effectMean=zeros(1,size(data,2)-1); effectCI=zeros(size(effectMean));
for k = 2:size(data,2)
    delta = data(:,k)-data(:,1);
    mu = mean(delta); ci = 1.96*std(delta)/sqrt(n);
    effectMean(k-1)=mu; effectCI(k-1)=ci;
    errorbar(ax2,mu,k-1,ci,'horizontal','Color',methodStyle(methodNames{k}), ...
        'LineStyle','none','LineWidth',1.6,'CapSize',9);
    scatter(ax2,mu,k-1,62,'o','MarkerFaceColor',methodStyle(methodNames{k}), ...
        'MarkerEdgeColor','k','LineWidth',.8);
end
xline(ax2,0,'--','Color',[.35 .35 .35],'LineWidth',1.0);
% Automatic axes limits can omit errorbar endpoint/cap extents. Include every
% saved interval and the reference, then leave visible clearance on both ends.
effectBounds=[effectMean-effectCI effectMean+effectCI 0];
effectPad=max(.08*(max(effectBounds)-min(effectBounds)),1e-3);
xlim(ax2,[min(effectBounds)-effectPad max(effectBounds)+effectPad]);
assert(all(effectBounds>ax2.XLim(1) & effectBounds<ax2.XLim(2)), ...
    'An effect interval endpoint or zero reference is clipped');
ax2.UserData=struct('intervalLower',effectMean-effectCI,'intervalUpper',effectMean+effectCI, ...
    'limits',ax2.XLim,'endpointClearanceChecked',true);
set(ax2,'YTick',1:3,'YTickLabel',methodNames(2:4),'YLim',[.5 3.5]);
xlabel(ax2,'Effect vs. Baseline A (unit)');
ylabel(ax2,'Comparator');
set_panel_style(ax2);

annotation(fig,'textbox',[.08 .94 .86 .05],'String','DEMO - illustrative layout, not research evidence', ...
    'EdgeColor','none','HorizontalAlignment','center','FontName','Times New Roman','FontSize',9);
export_all(fig,outDir,figName,canvas,requiredFormats);
close(fig);
end

function [grid,density] = simple_kde(x,nGrid)
% Toolbox-free Gaussian KDE for the visual template.
x = x(:);
spread = std(x);
if spread <= eps, spread = max(abs(mean(x)),1)*.01; end
bw = 1.06*spread*numel(x)^(-1/5);
grid = linspace(min(x)-2*bw,max(x)+2*bw,nGrid);
z = (grid(:)-x')/bw;
density = mean(exp(-.5*z.^2),2)'/(bw*sqrt(2*pi));
grid = grid(:)';
end

function set_panel_style(ax)
set(ax,'Box','on','LineWidth',1.1,'FontName','Times New Roman', ...
    'FontSize',9.5,'TickDir','out','Layer','top');
set(ax.XLabel,'FontName','Times New Roman','FontSize',11,'FontWeight','bold');
set(ax.YLabel,'FontName','Times New Roman','FontSize',11,'FontWeight','bold');
grid(ax,'on'); ax.GridAlpha=.14; ax.GridLineStyle='-';
end

function export_all(fig,outDir,figName,canvas,requiredFormats)
drawnow;
set(fig,'PaperUnits','centimeters','PaperPosition',[0 0 canvas], ...
    'PaperSize',canvas,'PaperPositionMode','manual');
for format=reshape(unique(string(requiredFormats),'stable'),1,[])
    target=fullfile(outDir,[figName '.' char(format)]);
    switch format
        case "fig", savefig(fig,target);
        case {"emf","pdf"}, export_vector(fig,target,canvas,format);
        case "png", print(fig,target,'-dpng','-r600'); % preserve physical canvas, no tight crop
    end
end
% Inspect requested vectors and actual manuscript pages at insertion width.
% File export alone never proves no clipping, overlap or unreadable statistics.
% This helper uses R2025a physical-size arguments. For an older installed
% release use supported export/print APIs and verify geometry/vector content;
% Renderer/Painters alone is not a guarantee. Font sizes scale with insertion.
end

function cm=scientific_colormap(kind,n)
if nargin<2, n=256; end
switch kind
    case 'sequential', cm=parula(n);
    case 'categorical', cm=lines(n);
    case 'diverging'
        anchors=[.15 .35 .65; .98 .98 .98; .70 .20 .15];
        cm=interp1([0 .5 1],anchors,linspace(0,1,n));
    otherwise, error('Choose sequential, diverging or categorical semantics');
end
end

function export_vector(fig,target,canvas,format)
if ~verLessThan('matlab','25.1')
    exportgraphics(fig,target,'ContentType','vector','Padding',0,'Units','centimeters', ...
        'Width',canvas(1),'Height',canvas(2),'PreserveAspectRatio','on');
elseif format=="emf"
    print(fig,target,'-dmeta','-painters');
else
    print(fig,target,'-dpdf','-painters');
end
end

function color=annotation_color(rgb)
linear=rgb/12.92;
mask=rgb>.04045;
linear(mask)=((rgb(mask)+.055)/1.055).^2.4;
lum=sum(linear.*[.2126 .7152 .0722]);
if (lum+.05)/.05 >= 1.05/(lum+.05), color=[0 0 0]; else, color=[1 1 1]; end
end
