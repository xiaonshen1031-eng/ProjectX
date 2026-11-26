function build_matlab_extra(selected,language)
% Eight additional chart families from independent illustrative data.
root=fileparts(fileparts(mfilename('fullpath')));
out=fullfile(root,'docs','downloads','figures','matlab');
if nargin<2,language='en';end
if strcmp(language,'zh'),out=fullfile(out,'zh');end
if ~exist(out,'dir'),mkdir(out);end
d=jsondecode(fileread(fullfile(root,'gallery','extra-data.json')));
set(groot,'DefaultFigureVisible','off','DefaultTextInterpreter','none','DefaultAxesTickLabelInterpreter','none','DefaultLegendInterpreter','none');
names={'sankey','raincloud','polar','parallel','calibration','spectrum','forest','gantt'};
builders={@sankey,@raincloud,@polar,@parallel,@calibration,@spectrum,@forest,@gantt};
for k=1:numel(names)
    if nargin>0 && ~isempty(selected) && ~any(strcmp(cellstr(selected),names{k})),continue;end
    f=builders{k}(d.(names{k}));drawnow;apply_figure_language(f,language);print(f,fullfile(out,[names{k} '.emf']),'-dmeta','-vector');close(f);
    fprintf('MATLAB EMF: %s %s\n',language,names{k});
end
end

function f=canvas()
f=figure('Color','w','Units','inches','Position',[1 1 16 9.6],'PaperUnits','inches','PaperPosition',[0 0 16 9.6],'PaperSize',[16 9.6]);
end
function a=ax(f,p)
a=axes(f,'Position',p,'FontName','Times New Roman','FontSize',12,'XColor',rgb('#131419'),'YColor',rgb('#131419'),'Box','off','LineWidth',.7);hold(a,'on');
end
function c=rgb(s),c=sscanf(s(2:end),'%2x%2x%2x',[1 3])/255;end
function p=palette()
p=gallery_color('categorical');
end
function c=cm(v)
c=gallery_color('sequential',v);
end
function tx(a,x,y,s,varargin),text(a,x,y,s,'FontName','Times New Roman','FontSize',12,'Color',rgb('#131419'),varargin{:});end
function key(f,position,limits,titleText)
a=ax(f,position);v=linspace(limits(1),limits(2),81);
for i=1:80,patch(a,[0 1 1 0],[v(i) v(i) v(i+1) v(i+1)],cm((i-.5)/80),'EdgeColor','none');end
set(a,'XLim',[0 1],'YLim',limits,'XTick',[],'YAxisLocation','right');ylabel(a,titleText,'FontSize',13);
end

function f=sankey(d)
f=canvas();a=ax(f,[.04 .145 .91 .72]);axis(a,'off');p=palette();
for k=1:numel(d.links)
    link=d.links(k);patch(a,link.x,link.y,p(link.color+1,:)*.48+.52,'EdgeColor','w','LineWidth',.6);
end
middle=strings(0);
for j=1:size(d.nodes,1)
    v=d.nodes(j,:);x=.08+v(1)*.43;y=v(3);h=v(4);
    patch(a,x+[0 .028 .028 0],y+[0 0 h h],p(v(2)+1,:),'EdgeColor','w');
    letters='ABC';name=sprintf('%s%d',letters(v(1)+1),v(2)+1);
    if v(1)==0
        tx(a,x-.012,y+h/2,sprintf('%s  %.1f',name,v(5)), ...
            'HorizontalAlignment','right','VerticalAlignment','middle','FontSize',13);
    elseif v(1)==1
        tx(a,x+.014,y+h/2,name,'HorizontalAlignment','center','VerticalAlignment','middle', ...
            'BackgroundColor','w','Margin',1.2);
        middle(end+1)=sprintf('%s %.1f',name,v(5)); %#ok<AGROW>
    else
        tx(a,x+.04,y+h/2,sprintf('%s  %.1f',name,v(5)), ...
            'VerticalAlignment','middle','FontSize',13);
    end
end
for k=1:3,words={'Inputs','Intermediate groups','Outputs'};tx(a,.094+(k-1)*.43,1.025,words{k},'HorizontalAlignment','center','FontSize',15);end
tx(a,.524,.025,strjoin(middle,'   '),'HorizontalAlignment','center','FontSize',13);
set(a,'XLim',[-.085 1.105],'YLim',[-.025 1.07]);
annotation(f,'textbox',[.31 .067 .36 .055],'String',sprintf('Conserved total: %.1f a.u.',d.total), ...
    'HorizontalAlignment','center','EdgeColor','none','FontSize',14,'Color',gallery_color('ink'));
end

function f=raincloud(d)
f=canvas();a=ax(f,[.12 .14 .81 .76]);p=palette();x=d.x(:);den=d.density;
for i=1:4
    y=6-(i-1)*1.65;z=den(i,:)'/max(den(:))*.95;v=d.samples(i,:);q=d.quantiles(i,:);
    fill(a,[x;flipud(x)],[repmat(y,size(x));flipud(y+z)],p(i,:)*.66+.34,'EdgeColor','none');
    plot(a,x,y+z,'Color',gallery_color('ink'),'LineWidth',.8);
    plot(a,v,y+d.jitter(i,:),'.','Color',p(i,:)*.65+.35,'MarkerSize',4);
    plot(a,q([1 5]),[y-.4 y-.4],'Color',rgb('#131419'),'LineWidth',1.4);
    patch(a,q(2)+[0 q(4)-q(2) q(4)-q(2) 0],y+[-.50 -.50 -.30 -.30],'w','EdgeColor',rgb('#131419'),'LineWidth',1.1);
    plot(a,[q(3) q(3)],[y-.5 y-.3],'Color',rgb('#131419'),'LineWidth',2);
end
set(a,'XLim',[min(-1,min(d.samples,[],'all')-.1) max(6.5,max(d.samples,[],'all')+.1)], ...
    'YLim',[.3 7.2],'YTick',fliplr(6-(0:3)*1.65),'YTickLabel',{'C04','C03','C02','C01'});
xlabel(a,'Illustrative response / a.u.','FontSize',14);
annotation(f,'textbox',[.12 .91 .69 .048],'String','Dots: observations    Box: quartiles    Whiskers: P10-P90', ...
    'FontSize',14,'EdgeColor','none','Color',gallery_color('ink'));
end

function f=polar(d)
f=canvas();a=ax(f,[.04 .10 .49 .79]);axis(a,'equal');axis(a,'off');v=d.values;
for i=1:4
    for h=0:23
        t=linspace(pi/2-(h+.5)*2*pi/24,pi/2-(h-.5)*2*pi/24,13)';r0=.25+(i-1)*.16;r1=r0+.15;
        patch(a,[r1*cos(t);r0*cos(flipud(t))],[r1*sin(t);r0*sin(flipud(t))],cm(v(i,h+1)),'EdgeColor','w','LineWidth',.7);
    end
end
for h=0:3:21,t=pi/2-h*2*pi/24;tx(a,1.03*cos(t),1.03*sin(t),sprintf('%02d:00',h),'HorizontalAlignment','center','FontSize',13);end
tx(a,0,.035,'C01-C04','HorizontalAlignment','center','FontSize',14);
tx(a,0,-.085,'Inner to outer','HorizontalAlignment','center','FontSize',12);
set(a,'XLim',[-1.18 1.18],'YLim',[-1.18 1.18]);key(f,[.51 .29 .017 .40],[0 1],'Normalized response');
b=ax(f,[.67 .30 .27 .39]);hours=0:23;spread=max(v,[],1)-min(v,[],1);[peakValue,peak]=max(spread);
% Midpoint steps match the sectors centred on each hour.
edges=[0 reshape([.5:1:22.5;.5:1:22.5],1,[]) 23];
values=repelem(spread,2);
fill(b,[edges fliplr(edges)],[zeros(size(edges)) fliplr(values)],gallery_color('alternative_wash'),'EdgeColor','none');
plot(b,edges,values,'Color',gallery_color('alternative'),'LineWidth',2);
plot(b,peak-1,peakValue,'d','MarkerFaceColor',gallery_color('attention'),'MarkerEdgeColor',gallery_color('ink'),'MarkerSize',7);
if peak-1>12,align='right';else,align='left';end
tx(b,peak-1,peakValue*1.12,sprintf('%02d:00 / %.2f',peak-1,peakValue),'HorizontalAlignment',align,'FontSize',13);
set(b,'XLim',[0 23],'YLim',[0 max(spread)*1.30],'XTick',0:6:23);
xlabel(b,'Hour of day','FontSize',14);ylabel(b,'Between-condition range','FontSize',14);
end

function f=parallel(d)
f=canvas();a=ax(f,[.10 .16 .82 .71]);p=palette();x=0:5;profiles=d.profiles;groups=d.groups(:);handles=gobjects(1,3);
for i=0:5,plot(a,[i i],[0 1],'Color',rgb('#DADAE2'),'LineWidth',1);end
for k=1:3
    rows=profiles(groups==k-1,:);q=quantile(rows,[.1 .9],1);
    fill(a,[x fliplr(x)],[q(1,:) fliplr(q(2,:))],p(k,:)*.12+.88,'EdgeColor','none');
end
for k=1:3
    rows=profiles(groups==k-1,:);
    for i=1:size(rows,1),plot(a,x,rows(i,:),'Color',p(k,:)*.20+.80,'LineWidth',.7);end
end
for k=1:3
    rows=profiles(groups==k-1,:);
    marks={'o','s','d'};styles={'-',':','--'};
    handles(k)=plot(a,x,mean(rows,1),'Color',p(k,:),'LineWidth',2.45,'LineStyle',styles{k}, ...
        'Marker',marks{k},'MarkerFaceColor',p(k,:),'MarkerEdgeColor',gallery_color('ink'),'MarkerSize',4);
end
set(a,'XLim',[-.05 5.05],'YLim',[0 1],'XTick',0:5,'XTickLabel',compose('Metric %d',1:6));ylabel(a,'Normalized value','FontSize',14);
lg=legend(a,handles,{'Group 1 / n=16','Group 2 / n=16','Group 3 / n=16'},'Box','off','NumColumns',3,'FontSize',12);lg.Units='normalized';lg.Position=[.22 .92 .56 .04];
end

function f=calibration(d)
f=canvas();p=palette();b=d.bins;a=ax(f,[.09 .36 .49 .54]);
h1=plot(a,[0 1],[0 1],'LineStyle','--','Color',rgb('#131419'),'LineWidth',1.3);
h2=errorbar(a,b(:,1),b(:,2),b(:,2)-b(:,3),b(:,4)-b(:,2),'o-','Color',p(1,:),'MarkerFaceColor',p(1,:),'MarkerSize',5,'LineWidth',1.7,'CapSize',6);
set(a,'XLim',[0 1],'YLim',[0 1]);ylabel(a,'Observed fraction','FontSize',14);legend(a,[h1 h2],{'Ideal calibration','Binned fraction / 95% Wilson interval'},'Box','off','Location','northwest','FontSize',11);
c=ax(f,[.09 .14 .49 .15]);
cuts=linspace(0,1,size(b,1)+1);
for i=1:size(b,1)
    patch(c,[cuts(i) cuts(i+1) cuts(i+1) cuts(i)],[0 0 b(i,5) b(i,5)], ...
        gallery_color('observation_wash'),'EdgeColor',gallery_color('ink'),'LineWidth',.7);
end
set(c,'XLim',[0 1]);xlabel(c,'Predicted probability','FontSize',14);ylabel(c,'Count','FontSize',14);
a=ax(f,[.68 .23 .25 .58]);x=d.x(:);
fill(a,[x;flipud(x)],[zeros(size(x));flipud(d.density0(:))],p(2,:)*.30+.70,'EdgeColor','none');
fill(a,[x;flipud(x)],[zeros(size(x));flipud(d.density1(:))],p(1,:)*.25+.75,'EdgeColor','none');
h1=plot(a,x,d.density0,'Color',p(2,:),'LineWidth',2);h2=plot(a,x,d.density1,'Color',p(1,:),'LineWidth',2);
set(a,'XLim',[0 1]);xlabel(a,'Predicted probability','FontSize',14);ylabel(a,'Density','FontSize',14);
lg=legend(a,[h1 h2],{'Label 0','Label 1'},'Box','off','NumColumns',2,'FontSize',11);
lg.Units='normalized';lg.Position=[.69 .821 .22 .032];
annotation(f,'textbox',[.68 .89 .27 .05],'String',sprintf('N = %d   Brier = %.3f',d.n,d.brier),'FontName','Times New Roman','FontSize',14,'Color',rgb('#131419'),'EdgeColor','none');
end

function f=spectrum(d)
f=canvas();a=ax(f,[.08 .76 .70 .17]);plot(a,d.time,d.signal,'Color',rgb('#00A878'),'LineWidth',.8);set(a,'XLim',[0 8],'XTickLabel',[]);ylabel(a,'Signal','FontSize',14);
a=ax(f,[.08 .15 .70 .54]);x=d.window(:);y=d.frequency(:);z=d.db;dx=x(2)-x(1);dy=y(2)-y(1);
for i=1:numel(y)
    for j=1:numel(x)
        patch(a,x(j)+[-.5 .5 .5 -.5]*dx,y(i)+[-.5 -.5 .5 .5]*dy,cm((z(i,j)+45)/45),'EdgeColor','none');
    end
end
set(a,'XLim',[0 8],'YLim',[0 32]);xlabel(a,'Time / s','FontSize',14);ylabel(a,'Frequency / Hz','FontSize',14);
b=ax(f,[.83 .15 .12 .54]);
fill(b,[zeros(size(y));flipud(d.energy(:))],[y;flipud(y)],gallery_color('alternative_wash'),'EdgeColor','none');
plot(b,d.energy,y,'Color',gallery_color('alternative'),'LineWidth',1.7);
set(b,'YLim',[0 32],'YTickLabel',[]);xlabel(b,'Summed STFT power','FontSize',14);
c=ax(f,[.83 .79 .12 .025]);v=linspace(-45,0,81);
for i=1:80,patch(c,[v(i) v(i+1) v(i+1) v(i)],[0 0 1 1],cm((i-.5)/80),'EdgeColor','none');end
set(c,'XLim',[-45 0],'YLim',[0 1],'YTick',[],'FontSize',10);xlabel(c,'Relative power / dB','FontSize',11);
end

function f=forest(d)
f=canvas();a=ax(f,[.10 .13 .47 .76]);x=d.x(:);density=d.density;
for i=1:14
    y=14-i;z=density(i,:)'/max(density(:))*.72;
    fill(a,[x;flipud(x)],[repmat(y,size(x));flipud(y+z)],cm(.34+(i-1)*.012),'EdgeColor','w','LineWidth',.7);
end
plot(a,[0 0],[-.3 14],'LineStyle','--','Color',rgb('#131419'),'LineWidth',1);set(a,'XLim',[-2.5 3],'YLim',[-.3 14],'YTick',0:13,'YTickLabel',compose('C%02d',14:-1:1));xlabel(a,'Paired difference distribution','FontSize',14);
b=ax(f,[.65 .13 .28 .76]);plot(b,[0 0],[-.3 14],'LineStyle','--','Color',rgb('#131419'),'LineWidth',1);p=palette();
for i=1:14
    if d.ci(i,2)<0
        color=gallery_color('exceedance');mark='<';
    elseif d.ci(i,1)>0
        color=p(1,:);mark='>';
    else
        color=gallery_color('ink');mark='s';
    end
    errorbar(b,d.mean(i),14-i,d.mean(i)-d.ci(i,1),d.ci(i,2)-d.mean(i),'horizontal', ...
        'LineStyle','none','Color',color,'LineWidth',1.7,'CapSize',6,'Marker',mark, ...
        'MarkerFaceColor',color,'MarkerEdgeColor',gallery_color('ink'),'MarkerSize',6);
end
limits=[min(d.ci,[],'all') max(d.ci,[],'all')];pad=diff(limits)*.08;
set(b,'XLim',limits+[-pad pad],'YLim',[-.3 14],'YTick',0:13,'YTickLabel',[]);xlabel(b,'Mean difference / 95% bootstrap CI','FontSize',14);
annotation(f,'textbox',[.10 .91 .3 .047],'String',sprintf('n = %d / condition',d.n), ...
    'EdgeColor','none','FontSize',14,'Color',gallery_color('ink'));
end

function f=gantt(d)
f=canvas();a=ax(f,[.09 .47 .73 .43]);p=palette();power=d.power;top=max(power(:));
for i=1:16
    y=16-i;x=d.arrival(i);w=d.departure(i)-x;
    patch(a,x+[0 w w 0],y+[-.40 -.40 .40 .40],gallery_color('alternative_wash'),'EdgeColor','none');
    for h=1:24
        if power(i,h)>0
            fraction=.3+.7*power(i,h)/top;c=p(ceil(i/4),:)*fraction+1-fraction;
            patch(a,(h-1+.025)+[0 .95 .95 0],y+[-.28 -.28 .28 .28],c,'EdgeColor','none');
        end
    end
    tx(a,24.5,y,sprintf('%.1f',sum(power(i,:))),'FontSize',11,'VerticalAlignment','middle');
end
set(a,'XLim',[0 24],'YLim',[-.6 15.7],'YTick',0:15,'YTickLabel',compose('R%02d',16:-1:1),'XTickLabel',[]);
tx(a,24.5,16.15,'Energy / kWh','FontSize',13);
b=ax(f,[.09 .27 .73 .155]);x=0:24;lower=zeros(1,24);handles=gobjects(1,5);
[steps,~]=stairs(x,zeros(size(x)));
for i=1:4
    upper=lower+d.groups(i,:);
    [~,baseline]=stairs(x,[lower lower(end)]);
    [~,outline]=stairs(x,[upper upper(end)]);
    handles(i)=fill(b,[steps;flipud(steps)],[baseline;flipud(outline)],p(i,:)*.78+.22,'EdgeColor','none');
    lower=upper;
end
handles(5)=plot(b,[0 24],[d.capacity d.capacity],'Color',gallery_color('ink'),'LineStyle','--','LineWidth',1.35);
set(b,'XLim',[0 24],'XTickLabel',[]);ylabel(b,'Power / kW','FontSize',14);
lg=legend(b,handles,{'Group 1','Group 2','Group 3','Group 4','Study cap'},'Box','off','NumColumns',5,'FontSize',11);lg.Units='normalized';lg.Position=[.21 .431 .50 .031];
c=ax(f,[.09 .115 .73 .10]);headroom=d.capacity-sum(d.groups,1);
[~,remaining]=stairs(x,[headroom headroom(end)]);
fill(c,[steps;flipud(steps)],[zeros(size(steps));flipud(remaining)],gallery_color('observation_wash'),'EdgeColor','none');
plot(c,steps,remaining,'Color',gallery_color('observation'),'LineWidth',1.45);
[minimum,peak]=min(headroom);
plot(c,peak-.5,minimum,'d','MarkerFaceColor',gallery_color('attention'),'MarkerEdgeColor',gallery_color('ink'),'MarkerSize',6);
tx(c,peak-.1,minimum+max(headroom)*.24,sprintf('%.1f',minimum),'FontSize',12);
set(c,'XLim',[0 24],'YLim',[0 max(headroom)*1.05],'XTick',0:3:24);
xlabel(c,'Time / h','FontSize',14);ylabel(c,'Headroom / kW','FontSize',14);
end
