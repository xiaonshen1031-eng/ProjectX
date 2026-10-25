function matlab_spatial_evidence_template(outDir, requiredFormats)
%MATLAB_SPATIAL_EVIDENCE_TEMPLATE Spatial field/error-map template.
% Replace demo arrays with saved geospatial results. Geometry, units, common
% limits, contours, and vector-safe layout are explicit by design.
% Real spatial geometry, fields and contours answer a physical question;
% add layers only when their actual spatial values answer that question.

if nargin < 1 || isempty(outDir), outDir=fullfile(pwd,'figure_exports'); end
if nargin < 2 || isempty(requiredFormats), requiredFormats={'pdf','png'}; end
requiredFormats=cellstr(lower(string(requiredFormats)));
assert(all(ismember(requiredFormats,{'fig','emf','pdf','png'})), 'Unsupported export format');
if ~exist(outDir,'dir'), mkdir(outDir); end
name='Fig_spatial_evidence_template';
canvas=[16.5 12.2];
fig=figure('Units','centimeters','Position',[2 2 canvas],'Color','w', ...
    'Renderer','painters','PaperUnits','centimeters','PaperPosition',[0 0 canvas], ...
    'PaperSize',canvas,'PaperPositionMode','manual','InvertHardcopy','off');
set(fig,'DefaultAxesFontName','Times New Roman','DefaultTextFontName','Times New Roman');
ax=axes(fig,'Units','normalized','Position',[.14 .13 .68 .78]);

% Deterministic demo field; replace with saved result arrays.
x=linspace(0,100,41); y=linspace(0,80,33); [X,Y]=meshgrid(x,y);
Z=2.4*exp(-((X-28).^2+(Y-50).^2)/700)-1.8*exp(-((X-74).^2+(Y-30).^2)/520)+.35*sin(X/13).*cos(Y/11);
imagesc(ax,x,y,Z); set(ax,'YDir','normal'); axis(ax,'image'); hold(ax,'on');
contour(ax,x,y,Z,10,'Color',[.12 .12 .12],'LineWidth',.65);
colormap(ax,balanced_map(256)); clim(ax,[-max(abs(Z(:))) max(abs(Z(:)))]);
cb=colorbar(ax,'Units','normalized','Position',[.85 .17 .027 .69]);
cb.Label.String='Signed spatial error (m)';
set(cb,'FontName','Times New Roman','FontSize',9.5,'LineWidth',1.1);
set(cb.Label,'FontName','Times New Roman','FontSize',11,'FontWeight','bold');
xlabel(ax,'Survey X position (m)'); ylabel(ax,'Survey Y position (m)');
style_axes(ax);
annotation(fig,'textbox',[.08 .94 .86 .05],'String','DEMO - illustrative layout, not research evidence', ...
    'EdgeColor','none','HorizontalAlignment','center','FontName','Times New Roman','FontSize',9);
export_all(fig,outDir,name,canvas,requiredFormats); close(fig);
end

function cm=balanced_map(n)
anchor=[.16 .32 .67; .58 .77 .91; .98 .98 .96; .96 .72 .48; .70 .10 .16];
t=linspace(0,1,size(anchor,1)); tq=linspace(0,1,n);
cm=[interp1(t,anchor(:,1),tq)' interp1(t,anchor(:,2),tq)' interp1(t,anchor(:,3),tq)'];
end

function style_axes(ax)
set(ax,'Box','on','LineWidth',1.1,'FontName','Times New Roman','FontSize',9.5, ...
    'TickDir','out','Layer','top');
set(ax.XLabel,'FontSize',11,'FontWeight','bold'); set(ax.YLabel,'FontSize',11,'FontWeight','bold');
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
% preserved spatial aspect ratio and actual insertion at the declared size.
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
