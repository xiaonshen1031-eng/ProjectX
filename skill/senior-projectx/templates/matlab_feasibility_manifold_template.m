function matlab_feasibility_manifold_template(outDir, requiredFormats)
%MATLAB_FEASIBILITY_MANIFOLD_TEMPLATE Raw-to-projected feasibility evidence.
% Replace demo candidates and projections with saved optimization outputs.
% This is a constraint/projection view using actual candidate coordinates.
% Additional panels require distinct engineering information.

if nargin < 1 || isempty(outDir), outDir=fullfile(pwd,'figure_exports'); end
if nargin < 2 || isempty(requiredFormats), requiredFormats={'pdf','png'}; end
requiredFormats=cellstr(lower(string(requiredFormats)));
assert(all(ismember(requiredFormats,{'fig','emf','pdf','png'})), 'Unsupported export format');
if ~exist(outDir,'dir'), mkdir(outDir); end
name='Fig_feasibility_manifold_template'; canvas=[16.5 11.0];
fig=figure('Units','centimeters','Position',[2 2 canvas],'Color','w', ...
    'Renderer','painters','PaperUnits','centimeters','PaperPosition',[0 0 canvas], ...
    'PaperSize',canvas,'PaperPositionMode','manual','InvertHardcopy','off');
set(fig,'DefaultAxesFontName','Times New Roman','DefaultTextFontName','Times New Roman', ...
    'DefaultLegendFontName','Times New Roman');
ax=axes(fig,'Units','normalized','Position',[.14 .18 .79 .74]); hold(ax,'on');

rng(11,'twister'); n=75;
raw=[-.42+.30*randn(n,1), .14+.13*randn(n,1)];
projected=[max(raw(:,1),0), max(raw(:,2),0)];
xl=[-.9 .55]; yl=[-.28 .62];
patch(ax,[0 xl(2) xl(2) 0],[0 0 yl(2) yl(2)],[.86 .95 .88], ...
    'EdgeColor','none','FaceAlpha',.75);
patch(ax,[xl(1) 0 0 xl(1)],[yl(1) yl(1) 0 0],[.98 .88 .88], ...
    'EdgeColor','none','FaceAlpha',.60);
for i=1:n
    plot(ax,[raw(i,1) projected(i,1)],[raw(i,2) projected(i,2)],'-', ...
        'Color',[.68 .68 .68],'LineWidth',.65);
end
h1=scatter(ax,raw(:,1),raw(:,2),28,[.88 .40 .08],'filled', ...
    'MarkerEdgeColor',[.35 .18 .04],'LineWidth',.45,'MarkerFaceAlpha',.72);
h2=scatter(ax,projected(:,1),projected(:,2),32,[.20 .48 .62],'o', ...
    'MarkerFaceColor','w','MarkerEdgeColor',[.12 .28 .36],'LineWidth',1.0);
xline(ax,0,'-','Color',[.15 .15 .15],'LineWidth',1.1); yline(ax,0,'-','Color',[.15 .15 .15],'LineWidth',1.1);
xlim(ax,xl); ylim(ax,yl);
xlabel(ax,'Constraint margin 1 (unit)'); ylabel(ax,'Constraint margin 2 (unit)');
lg=legend(ax,[h1 h2],{'Raw candidate','Projected candidate'},'Location','northwest', ...
    'Orientation','horizontal','Box','off','FontSize',9.5);
lg.ItemTokenSize=[18 12]; style_axes(ax);
annotation(fig,'textbox',[.08 .94 .86 .05],'String','DEMO - illustrative layout, not research evidence', ...
    'EdgeColor','none','HorizontalAlignment','center','FontName','Times New Roman','FontSize',9);
export_all(fig,outDir,name,canvas,requiredFormats); close(fig);
end

function style_axes(ax)
set(ax,'Box','on','LineWidth',1.1,'FontName','Times New Roman','FontSize',9.5, ...
    'TickDir','out','Layer','top');
set(ax.XLabel,'FontSize',11,'FontWeight','bold'); set(ax.YLabel,'FontSize',11,'FontWeight','bold');
grid(ax,'on'); ax.GridAlpha=.12;
end

function export_all(fig,outDir,name,canvas,requiredFormats)
drawnow; set(fig,'PaperPosition',[0 0 canvas],'PaperSize',canvas);
for format=reshape(unique(string(requiredFormats),'stable'),1,[])
    target=fullfile(outDir,[name '.' char(format)]);
    switch format
        case "fig", savefig(fig,target);
        case {"emf","pdf"}, export_vector(fig,target,canvas,format);
        case "png", print(fig,target,'-dpng','-r600');
    end
end
% R2025a API: adapt to supported exports on older releases. Inspect vector,
% full frames, font scale and actual manuscript insertion separately.
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
