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
a=axes(f,'Position',p,'FontName','Times New Roman','FontSize',12,'XColor',rgb('#193b33'),'YColor',rgb('#193b33'),'Box','off','LineWidth',.7);hold(a,'on');
end
function c=rgb(s),c=sscanf(s(2:end),'%2x%2x%2x',[1 3])/255;end
function p=palette()
p=[rgb('#286b56');rgb('#54849c');rgb('#bc8856');rgb('#837799');rgb('#7e9a67');rgb('#ae6f78');rgb('#5b9c9b');rgb('#b4a269')];
end
function c=cm(v)
p=[rgb('#f1f3dc');rgb('#c3d8a4');rgb('#74a78f');rgb('#286b56');rgb('#163c36')];c=interp1(linspace(0,1,5),p,min(1,max(0,v)));
end
function tx(a,x,y,s,varargin),text(a,x,y,s,'FontName','Times New Roman','FontSize',12,'Color',rgb('#193b33'),varargin{:});end
function key(f,position,limits,titleText)
a=ax(f,position);v=linspace(limits(1),limits(2),81);
for i=1:80,patch(a,[0 1 1 0],[v(i) v(i) v(i+1) v(i+1)],cm((i-.5)/80),'EdgeColor','none');end
set(a,'XLim',[0 1],'YLim',limits,'XTick',[],'YAxisLocation','right');ylabel(a,titleText,'FontSize',13);
end

function f=sankey(d)
f=canvas();a=ax(f,[.05 .10 .90 .80]);axis(a,'off');p=palette();
for k=1:numel(d.links)
    link=d.links(k);patch(a,link.x,link.y,p(link.color+1,:)*.40+.60,'EdgeColor','w','LineWidth',.6);
end
for j=1:size(d.nodes,1)
    v=d.nodes(j,:);x=.08+v(1)*.43;y=v(3);h=v(4);
    patch(a,x+[0 .028 .028 0],y+[0 0 h h],p(v(2)+1,:),'EdgeColor','w');
    letters='ABC';tx(a,x+.04,y+h/2,sprintf('%s%d  %.0f',letters(v(1)+1),v(2)+1,v(5)),'VerticalAlignment','middle');
end
for k=1:3,words={'Inputs','Intermediate groups','Outputs'};tx(a,.08+(k-1)*.43,.97,words{k},'FontSize',15);end
set(a,'XLim',[0 1.09],'YLim',[0 1.02]);
end

function f=raincloud(d)
f=canvas();a=ax(f,[.12 .14 .81 .76]);p=palette();x=d.x(:);den=d.density;
for i=1:4
    y=6-(i-1)*1.65;z=den(i,:)'/max(den(:))*.95;v=d.samples(i,:);q=d.quantiles(i,:);
    fill(a,[x;flipud(x)],[repmat(y,size(x));flipud(y+z)],p(i,:)*.8+.2,'EdgeColor','none');
    plot(a,v,y+d.jitter(i,:),'.','Color',p(i,:)*.5+.5,'MarkerSize',3);
    plot(a,q([1 5]),[y-.4 y-.4],'Color',rgb('#193b33'),'LineWidth',1.4);
    patch(a,q(2)+[0 q(4)-q(2) q(4)-q(2) 0],y+[-.50 -.50 -.30 -.30],'w','EdgeColor',rgb('#193b33'),'LineWidth',1.1);
    plot(a,[q(3) q(3)],[y-.5 y-.3],'Color',rgb('#193b33'),'LineWidth',2);
end
set(a,'XLim',[-1 6.5],'YLim',[.3 7.2],'YTick',fliplr(6-(0:3)*1.65),'YTickLabel',{'C04','C03','C02','C01'});xlabel(a,'Illustrative response / a.u.','FontSize',14);
end

function f=polar(d)
f=canvas();a=ax(f,[.07 .10 .76 .81]);axis(a,'equal');axis(a,'off');v=d.values;
for i=1:4
    for h=0:23
        t=linspace(pi/2-(h+1)*2*pi/24,pi/2-h*2*pi/24,13)';r0=.25+(i-1)*.16;r1=r0+.15;
        patch(a,[r1*cos(t);r0*cos(flipud(t))],[r1*sin(t);r0*sin(flipud(t))],cm(v(i,h+1)),'EdgeColor','w','LineWidth',.7);
    end
end
t=pi/2-(0:24)'*2*pi/24;profile=[mean(v,1) mean(v(:,1))]';r=.98+.16*profile/max(profile);plot(a,r.*cos(t),r.*sin(t),'Color',rgb('#286b56'),'LineWidth',2);
for h=0:3:21,t=pi/2-h*2*pi/24;tx(a,1.25*cos(t),1.25*sin(t),sprintf('%02d:00',h),'HorizontalAlignment','center','FontSize',13);end
tx(a,0,.045,'24 h','HorizontalAlignment','center','FontSize',24);tx(a,0,-.10,'4 CONDITIONS','HorizontalAlignment','center','FontSize',10);
set(a,'XLim',[-1.45 1.45],'YLim',[-1.45 1.45]);key(f,[.86 .23 .022 .51],[0 1],'Normalized response');
end

function f=parallel(d)
f=canvas();a=ax(f,[.10 .16 .82 .71]);p=palette();x=0:5;profiles=d.profiles;groups=d.groups(:);handles=gobjects(1,3);
for i=0:5,plot(a,[i i],[0 1],'Color',rgb('#b7c7b7'),'LineWidth',1);end
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
    handles(k)=plot(a,x,mean(rows,1),'Color',p(k,:),'LineWidth',2.6);
end
set(a,'XLim',[-.05 5.05],'YLim',[0 1],'XTick',0:5,'XTickLabel',compose('Metric %d',1:6));ylabel(a,'Normalized value','FontSize',14);
lg=legend(a,handles,{'Group 1 / n=16','Group 2 / n=16','Group 3 / n=16'},'Box','off','NumColumns',3,'FontSize',12);lg.Units='normalized';lg.Position=[.22 .92 .56 .04];
end

function f=calibration(d)
f=canvas();p=palette();b=d.bins;a=ax(f,[.09 .36 .49 .54]);
h1=plot(a,[0 1],[0 1],'LineStyle','--','Color',rgb('#879581'),'LineWidth',1.3);
h2=errorbar(a,b(:,1),b(:,2),b(:,2)-b(:,3),b(:,4)-b(:,2),'o-','Color',p(1,:),'MarkerFaceColor',p(1,:),'MarkerSize',5,'LineWidth',1.7,'CapSize',6);
set(a,'XLim',[0 1],'YLim',[0 1]);ylabel(a,'Observed fraction','FontSize',14);legend(a,[h1 h2],{'Ideal calibration','Binned fraction / 95% Wilson interval'},'Box','off','Location','northwest','FontSize',11);
c=ax(f,[.09 .14 .49 .15]);bar(c,b(:,1),b(:,5),.65,'FaceColor',rgb('#b6cda0'),'EdgeColor','none');set(c,'XLim',[0 1]);xlabel(c,'Predicted probability','FontSize',14);ylabel(c,'Count','FontSize',14);
a=ax(f,[.68 .23 .25 .58]);x=d.x(:);
fill(a,[x;flipud(x)],[zeros(size(x));flipud(d.density0(:))],p(2,:)*.30+.70,'EdgeColor','none');
fill(a,[x;flipud(x)],[zeros(size(x));flipud(d.density1(:))],p(1,:)*.25+.75,'EdgeColor','none');
h1=plot(a,x,d.density0,'Color',p(2,:),'LineWidth',2);h2=plot(a,x,d.density1,'Color',p(1,:),'LineWidth',2);
set(a,'XLim',[0 1]);xlabel(a,'Predicted probability','FontSize',14);ylabel(a,'Density','FontSize',14);legend(a,[h1 h2],{'Label 0','Label 1'},'Box','off','FontSize',11);
annotation(f,'textbox',[.68 .87 .27 .05],'String',sprintf('N = %d   Brier = %.3f',d.n,d.brier),'FontName','Times New Roman','FontSize',14,'Color',rgb('#193b33'),'EdgeColor','none');
end

function f=spectrum(d)
f=canvas();a=ax(f,[.08 .76 .70 .17]);plot(a,d.time,d.signal,'Color',rgb('#286b56'),'LineWidth',.8);set(a,'XLim',[0 8],'XTickLabel',[]);ylabel(a,'Signal','FontSize',14);
a=ax(f,[.08 .15 .70 .54]);x=d.window(:);y=d.frequency(:);z=d.db;dx=x(2)-x(1);dy=y(2)-y(1);
for i=1:numel(y)
    for j=1:numel(x)
        patch(a,x(j)+[-.5 .5 .5 -.5]*dx,y(i)+[-.5 -.5 .5 .5]*dy,cm((z(i,j)+45)/45),'EdgeColor','none');
    end
end
set(a,'XLim',[0 8],'YLim',[0 32]);xlabel(a,'Time / s','FontSize',14);ylabel(a,'Frequency / Hz','FontSize',14);
b=ax(f,[.83 .15 .12 .54]);plot(b,d.energy,y,'Color',rgb('#286b56'),'LineWidth',1.7);set(b,'YLim',[0 32],'YTickLabel',[]);xlabel(b,'Energy','FontSize',14);
c=ax(f,[.83 .79 .12 .025]);v=linspace(-45,0,81);
for i=1:80,patch(c,[v(i) v(i+1) v(i+1) v(i)],[0 0 1 1],cm((i-.5)/80),'EdgeColor','none');end
set(c,'XLim',[-45 0],'YLim',[0 1],'YTick',[],'FontSize',10);xlabel(c,'Relative power / dB','FontSize',11);
end

function f=forest(d)
f=canvas();a=ax(f,[.10 .13 .47 .76]);x=d.x(:);density=d.density;
for i=1:14
    y=14-i;z=density(i,:)'/max(density(:))*.72;
    fill(a,[x;flipud(x)],[repmat(y,size(x));flipud(y+z)],cm(.3+(i-1)*.04),'EdgeColor','w','LineWidth',.7);
end
plot(a,[0 0],[-.3 14],'LineStyle','--','Color',rgb('#8b9c84'),'LineWidth',1);set(a,'XLim',[-2.5 3],'YLim',[-.3 14],'YTick',0:13,'YTickLabel',compose('C%02d',14:-1:1));xlabel(a,'Paired difference distribution','FontSize',14);
b=ax(f,[.65 .13 .28 .76]);plot(b,[0 0],[-.3 14],'LineStyle','--','Color',rgb('#8b9c84'),'LineWidth',1);p=palette();
for i=1:14
    if d.mean(i)>=0,color=p(1,:);else,color=p(4,:);end
    plot(b,d.ci(i,:),[14-i 14-i],'Color',color,'LineWidth',2);plot(b,d.mean(i),14-i,'o','Color',color,'MarkerFaceColor',color,'MarkerSize',5);
end
set(b,'XLim',[-1 1.3],'YLim',[-.3 14],'YTick',0:13,'YTickLabel',[]);xlabel(b,'Mean difference / 95% bootstrap CI','FontSize',14);
end

function f=gantt(d)
f=canvas();a=ax(f,[.09 .40 .79 .53]);p=palette();power=d.power;top=max(power(:));
for i=1:16
    y=16-i;x=d.arrival(i);w=d.departure(i)-x;
    patch(a,x+[0 w w 0],y+[-.35 -.35 .35 .35],rgb('#edf0e8'),'EdgeColor','none');
    for h=1:24
        if power(i,h)>0
            fraction=.3+.7*power(i,h)/top;c=p(ceil(i/4),:)*fraction+1-fraction;
            patch(a,(h-1+.025)+[0 .95 .95 0],y+[-.34 -.34 .34 .34],c,'EdgeColor','none');
        end
    end
    tx(a,24.4,y,sprintf('%.1f',sum(power(i,:))),'FontSize',10,'VerticalAlignment','middle');
end
set(a,'XLim',[0 24],'YLim',[-.6 15.7],'YTick',0:15,'YTickLabel',compose('R%02d',16:-1:1),'XTickLabel',[]);tx(a,24.4,16,'Energy','FontSize',11);
b=ax(f,[.09 .14 .79 .20]);x=(0:23)+.5;lower=zeros(1,24);handles=gobjects(1,4);
for i=1:4
    upper=lower+d.groups(i,:);handles(i)=fill(b,[x fliplr(x)],[lower fliplr(upper)],p(i,:)*.8+.2,'EdgeColor','none');lower=upper;
end
plot(b,[0 24],[d.capacity d.capacity],'Color',p(3,:),'LineStyle','--','LineWidth',1.4);set(b,'XLim',[0 24]);xlabel(b,'Time / h','FontSize',14);ylabel(b,'Aggregate power / a.u.','FontSize',14);
lg=legend(b,handles,{'Group 1','Group 2','Group 3','Group 4'},'Box','off','NumColumns',4,'FontSize',11);lg.Units='normalized';lg.Position=[.25 .035 .45 .04];
end
