function fig = matlab_project_figure_template(time, power, available, requested)
% Window-power allocation diagnostic; all arrays come from saved model output.
% power and available: resource x period. requested: resource energy demand.
% time: real time boundaries (one more entry than power columns).
arguments
    time (1,:) double
    power (:,:) double
    available (:,:) logical
    requested (:,1) double
end
assert(isequal(size(power),size(available)) && numel(time)==size(power,2)+1);
assert(numel(requested)==size(power,1) && all(isfinite(power),'all'));
assert(all(diff(time)>0) && all(power>=0,'all'));
fig = figure('Color','w','Units','centimeters','Position',[2 2 16.6 10]);
ax = axes(fig); hold(ax,'on'); box(ax,'off');
pal = parula(256); scale = max(max(power),eps);
for r=1:size(power,1)
    for t=1:size(power,2)
        if available(r,t)
            rectangle(ax,'Position',[time(t),r-.34,time(t+1)-time(t),.68], ...
                'FaceColor',[.93 .93 .93],'EdgeColor','w');
        end
        if power(r,t)>0
            idx=1+round(255*power(r,t)/scale);
            rectangle(ax,'Position',[time(t),r-.34,time(t+1)-time(t),.68], ...
                'FaceColor',pal(idx,:),'EdgeColor','w');
            text(ax,mean(time(t:t+1)),r,sprintf('%.1f',power(r,t)), ...
                'HorizontalAlignment','center','FontName','Times New Roman','FontSize',8);
        end
    end
    delivered=sum(power(r,:).*diff(time));
    text(ax,time(end)+(time(end)-time(1))*.02,r,sprintf('%.1f / %.1f',delivered,requested(r)), ...
        'FontName','Times New Roman','FontSize',8);
end
ax.FontName='Times New Roman'; ax.FontSize=9; ax.YDir='reverse';
ax.YTick=1:size(power,1); xlim(ax,[time(1) time(end)+(time(end)-time(1))*.27]);
xlabel(ax,'时间 / h','FontName','Microsoft YaHei','FontWeight','bold','FontSize',10);
ylabel(ax,'资源','FontName','Microsoft YaHei','FontWeight','bold','FontSize',10);
% Units must match inputs. No standalone mean-ranking bars or sparse scatter.
% Caption identifies window, actual power and delivered/requested energy units.
end
