function fig = matlab_project_figure_template(time, power, available, requested, width_cm)
% Window-power allocation diagnostic; all arrays come from saved model output.
% power and available: resource x period. requested: resource energy demand.
% time: real time boundaries (one more entry than power columns).
arguments
    time (1,:) double
    power (:,:) double
    available (:,:) logical
    requested (:,1) double
    width_cm (1,1) double {mustBeFinite,mustBePositive} = 16.6
end
assert(isequal(size(power),size(available)) && numel(time)==size(power,2)+1);
assert(~isempty(power) && numel(requested)==size(power,1) && all(isfinite(power),'all'));
assert(all(isfinite(time)) && all(diff(time)>0) && all(power>=0,'all'));
assert(all(isfinite(requested)) && all(requested>=0));
fontList = string(listfonts);
zh = ["Microsoft YaHei","微软雅黑","Microsoft YaHei UI","SimHei","黑体", ...
      "Noto Sans CJK SC","Noto Sans SC","Source Han Sans SC","SimSun","宋体"];
zh = zh(ismember(zh,fontList));
latin = ["Times New Roman","Liberation Serif","DejaVu Serif"];
latin = latin(ismember(latin,fontList));
assert(~isempty(zh) && ~isempty(latin),"Required figure fonts or approved fallbacks are unavailable.");
zh = zh(1);
latin = latin(1);
palette = jsondecode(fileread(fullfile(fileparts(mfilename("fullpath")),"research_figure_palette.json")));
ink = hexrgb(palette.colors.ink);
violation = hexrgb(palette.colors.raspberry);
availableFill = hexrgb(palette.colors.cobalt_wash);
height_cm = max(6,2.6+.62*size(power,1));
fig = figure('Color','w','Units','centimeters','Position',[2 2 width_cm height_cm]);
fig.PaperUnits = 'centimeters';
fig.PaperSize = [width_cm height_cm];
fig.PaperPosition = [0 0 width_cm height_cm];
ax = axes(fig); hold(ax,'on'); box(ax,'off');
anchors = zeros(numel(palette.project_sequential),3);
for k=1:numel(palette.project_sequential)
    anchors(k,:) = hexrgb(palette.colors.(palette.project_sequential{k}));
end
pal = interp1(linspace(0,1,size(anchors,1)),anchors,linspace(0,1,256));
scale = max(max(power,[],'all'),eps);
for r=1:size(power,1)
    for t=1:size(power,2)
        if available(r,t)
            rectangle(ax,'Position',[time(t),r-.34,time(t+1)-time(t),.68], ...
                'FaceColor',availableFill,'EdgeColor',ink,'LineWidth',.5);
            if power(r,t)==0
                text(ax,mean(time(t:t+1)),r,'0','HorizontalAlignment','center', ...
                    'FontName',latin,'FontSize',8,'Color',ink);
            end
        end
        if power(r,t)>0
            idx=1+round(255*power(r,t)/scale);
            fill=pal(idx,:);
            edge=ink;
            if ~available(r,t)
                edge=violation;
            end
            rectangle(ax,'Position',[time(t),r-.34,time(t+1)-time(t),.68], ...
                'FaceColor',fill,'EdgeColor',edge,'LineWidth',.5);
            textColor=ink;
            linear=fill/12.92;
            bright=fill>.04045;
            linear(bright)=((fill(bright)+.055)/1.055).^2.4;
            if dot(linear,[.2126 .7152 .0722]) < .179
                textColor=[1 1 1];
            end
            text(ax,mean(time(t:t+1)),r,sprintf('%.1f',power(r,t)), ...
                'HorizontalAlignment','center','FontName',latin,'FontSize',8,'Color',textColor);
        end
    end
    delivered=sum(power(r,:).*diff(time));
    text(ax,time(end)+(time(end)-time(1))*.02,r,sprintf('%.1f / %.1f',delivered,requested(r)), ...
        'FontName',latin,'FontSize',8,'Color',ink);
end
ax.FontName=latin; ax.FontSize=9; ax.YDir='reverse'; ax.XColor=ink; ax.YColor=ink;
ax.YTick=1:size(power,1); ax.XTick=time;
xlim(ax,[time(1) time(end)+(time(end)-time(1))*.27]); ylim(ax,[0 size(power,1)+.5]);
text(ax,time(end)+(time(end)-time(1))*.02,.22, ...
    sprintf('{\\fontname{%s}\\bf交付/需求}{\\rm\\fontname{%s} (kWh)}',zh,latin), ...
    'FontName',zh,'FontWeight','normal','FontSize',8,'Color',ink);
xlabel(ax,sprintf('{\\fontname{%s}\\bf时间}{\\rm\\fontname{%s} / h}',zh,latin), ...
    'FontName',zh,'FontWeight','normal','FontSize',10);
ylabel(ax,'资源','FontName',zh,'FontWeight','bold','FontSize',10);
if any(power>0,'all')
    colormap(ax,pal); clim(ax,[0 max(power,[],'all')]);
    cb = colorbar(ax,'Location','southoutside');
    cb.FontName=latin; cb.FontSize=8; cb.Color=ink;
    cb.Ticks=[0 max(power,[],'all')/2 max(power,[],'all')];
    cb.Label.String=sprintf('{\\fontname{%s}\\bf实际功率}{\\rm\\fontname{%s} / kW}',zh,latin);
    cb.Label.FontName=zh; cb.Label.FontWeight='normal'; cb.Label.FontSize=10;
end
% Units must match inputs. No standalone mean-ranking bars or sparse scatter.
% Caption identifies power in kW, time in h and delivered/requested energy in kWh.
% Zero-filled cobalt-wash cells are available but unused. Unpainted cells are outside the window.
end

function rgb = hexrgb(value)
rgb = sscanf(value(2:end),'%2x',[1 3])/255;
end
