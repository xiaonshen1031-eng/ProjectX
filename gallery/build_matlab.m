function build_matlab(selected,language)
% Six independent chart demonstrations, exported natively as Windows EMF.
% Input: analytic / seeded illustrative data from build_python.py.
% No project document or client data is read by this generator.
root = fileparts(fileparts(mfilename('fullpath')));
out = fullfile(root,'docs','downloads','figures','matlab');
if nargin<2,language='en';end
if strcmp(language,'zh'),out=fullfile(out,'zh');end
if ~exist(out,'dir'), mkdir(out); end
data = jsondecode(fileread(fullfile(root,'gallery','demo-data.json')));
set(groot,'DefaultFigureVisible','off','DefaultTextInterpreter','none', ...
    'DefaultAxesTickLabelInterpreter','none','DefaultLegendInterpreter','none');
names = {'trajectory','ridges','chord','cluster','spatial','feasibility'};
builders = {@trajectory,@ridges,@chord,@cluster,@spatial,@feasibility};
for k = 1:numel(names)
    if nargin>0 && ~isempty(selected) && ~any(strcmp(cellstr(selected),names{k})),continue;end
    fig = builders{k}(data.(names{k}));
    drawnow;
    apply_figure_language(fig,language);
    print(fig,fullfile(out,[names{k} '.emf']),'-dmeta','-vector');
    close(fig);
    fprintf('MATLAB EMF: %s %s\n',language,names{k});
end
end

function f = canvas()
f=figure('Color','w','Units','inches','Position',[1 1 16 9.6], ...
    'PaperUnits','inches','PaperPosition',[0 0 16 9.6],'PaperSize',[16 9.6]);
end

function a = axis_at(f,position)
a=axes(f,'Position',position,'FontName','Times New Roman','FontSize',12, ...
    'XColor',rgb('#193b33'),'YColor',rgb('#193b33'),'LineWidth',.7,'Box','off');
hold(a,'on');
end

function c = rgb(s)
c=sscanf(s(2:end),'%2x%2x%2x',[1 3])/255;
end

function p = palette()
p=[rgb('#286b56');rgb('#54849c');rgb('#bc8856');rgb('#837799'); ...
    rgb('#7e9a67');rgb('#ae6f78');rgb('#5b9c9b');rgb('#b4a269')];
end

function c = sequential(value)
anchors=[rgb('#f1f3dc');rgb('#c3d8a4');rgb('#74a78f');rgb('#286b56');rgb('#163c36')];
c=interp1(linspace(0,1,5),anchors,min(1,max(0,value)),'linear');
end

function c = diverging(value)
anchors=[rgb('#8d647d');rgb('#cbb7c3');rgb('#fafaf4');rgb('#b0cbb5');rgb('#286b56')];
c=interp1(linspace(-1,1,5),anchors,min(1,max(-1,value)),'linear');
end

function t = label(a,x,y,s,varargin)
t=text(a,x,y,s,'FontName','Times New Roman','FontSize',12,'Color',rgb('#193b33'),varargin{:});
end

function vector_key(f,position,limits,kind,titleText)
a=axis_at(f,position);v=linspace(limits(1),limits(2),81);
for i=1:80
    if strcmp(kind,'diverging'),c=diverging((v(i)+v(i+1))/2);else,c=sequential((v(i)+v(i+1))/2);end
    patch(a,[0 1 1 0],[v(i) v(i) v(i+1) v(i+1)],c,'EdgeColor','none');
end
set(a,'XLim',[0 1],'YLim',limits,'XTick',[],'YAxisLocation','right');
ylabel(a,titleText,'FontSize',13,'FontName','Times New Roman');
end

function f = trajectory(d)
f=canvas();p=palette();x=d.time(:);
a=axis_at(f,[.09 .42 .85 .50]);
h1=fill(a,[x;flipud(x)],[d.low(:);flipud(d.high(:))],rgb('#c7ddca'),'EdgeColor','none');
h2=plot(a,x,d.reference,'Color',p(2,:),'LineWidth',1.8,'LineStyle','--');
h3=plot(a,x,d.mean,'Color',p(1,:),'LineWidth',2.7);
h4=plot(a,x,d.capacity,'Color',p(3,:),'LineWidth',1.8,'LineStyle','-.');
set(a,'XLim',[0 24],'YLim',[20 95],'XTickLabel',[],'YGrid','on','GridColor',rgb('#e1e7df'));
ylabel(a,'Signal / a.u.','FontSize',14);
lg=legend(a,[h1 h2 h3 h4],{'10-90% envelope','Reference','Central profile','Upper bound'},'NumColumns',4,'Box','off','FontSize',12);
lg.Units='normalized';lg.Position=[.18 .93 .66 .035];
b=axis_at(f,[.09 .15 .85 .20]);margin=d.capacity(:)-d.mean(:);
fill(b,[x;flipud(x)],[zeros(size(x));flipud(margin)],rgb('#d7e5bf'),'EdgeColor','none');
plot(b,x,margin,'Color',p(1,:),'LineWidth',2);
set(b,'XLim',[0 24],'YLim',[0 65],'XTick',0:3:24,'YGrid','on','GridColor',rgb('#e1e7df'));
xlabel(b,'Time / h','FontSize',14);ylabel(b,'Bound margin / a.u.','FontSize',14);
end

function f = ridges(d)
f=canvas();a=axis_at(f,[.12 .14 .75 .76]);x=d.x(:);density=d.density;
for i=8:-1:1
    y=(8-i)*1.06;z=density(i,:)'/max(density(:))*1.65;
    fill(a,[x;flipud(x)],[repmat(y,size(x));flipud(y+z)],sequential(.2+(i-1)*.09),'EdgeColor','w','LineWidth',1.4);
    plot(a,x,y+z,'Color',rgb('#286b56'),'LineWidth',.7);
end
for i=1:8
    y=(8-i)*1.06;center=y+.13;q=d.quantiles(i,:);
    plot(a,q([1 3]),[center center],'Color','w','LineWidth',4);
    plot(a,q(2),center,'o','Color',rgb('#193b33'),'MarkerFaceColor',rgb('#193b33'),'MarkerSize',5);
    label(a,-3.7,y+.2,sprintf('C%02d',i),'HorizontalAlignment','right','FontSize',13);
    label(a,16.3,y+.2,sprintf('%.2f',q(2)),'FontSize',13);
end
set(a,'XLim',[-3.5 18],'YLim',[-.15 9.15],'YTick',[],'YColor','none');
xlabel(a,'Illustrative response / a.u.','FontSize',14);
label(a,16.3,8.9,'Median','FontSize',13);
label(a,-3.7,8.9,'Condition','HorizontalAlignment','right','FontSize',13);
end

function xy = arc(startAngle,endAngle,r,n)
t=linspace(startAngle,endAngle,n)';xy=r*[cos(t) sin(t)];
end

function xy = curve(p,q)
t=linspace(0,1,35)';xy=(1-t).^3.*p+3*(1-t).^2.*t.*(p*.15)+3*(1-t).*t.^2.*(q*.15)+t.^3.*q;
end

function f = chord(d)
f=canvas();p=palette();matrix=d.matrix;n=size(matrix,1);
a=axis_at(f,[.035 .10 .59 .82]);axis(a,'equal');axis(a,'off');
gap=.055;scale=(2*pi-n*gap)/sum(matrix(:));theta=.15;arcs=zeros(n,2);segments=zeros(n,n,2);
for i=1:n
    start=theta;theta=theta+sum(matrix(i,:))*scale;arcs(i,:)=[start theta];cursor=start;
    for j=1:n
        segments(i,j,:)=[cursor cursor+matrix(i,j)*scale];cursor=cursor+matrix(i,j)*scale;
    end
    theta=theta+gap;
end
for i=1:n
    for j=i+1:n
        if matrix(i,j)<=0,continue;end
        ai=squeeze(segments(i,j,:));aj=squeeze(segments(j,i,:));
        left=arc(ai(1),ai(2),.91,24);right=arc(aj(1),aj(2),.91,24);
        points=[left;curve(left(end,:),right(1,:));right;curve(right(end,:),left(1,:))];
        patch(a,points(:,1),points(:,2),p(i,:)*.42+.58,'EdgeColor','w','LineWidth',.5);
    end
end
for i=1:n
    outer=arc(arcs(i,1),arcs(i,2),1,70);inner=flipud(arc(arcs(i,1),arcs(i,2),.93,70));
    points=[outer;inner];patch(a,points(:,1),points(:,2),p(i,:),'EdgeColor','w','LineWidth',1.1);
    mid=mean(arcs(i,:));label(a,cos(mid)*1.13,sin(mid)*1.13,sprintf('G%d',i),'HorizontalAlignment','center','FontSize',15);
end
set(a,'XLim',[-1.3 1.3],'YLim',[-1.3 1.3]);
m=axis_at(f,[.68 .25 .255 .45]);
for i=1:n
    for j=1:n
        v=matrix(i,j);patch(m,j+[-.5 .5 .5 -.5],i+[-.5 -.5 .5 .5],sequential(v/9),'EdgeColor','none');
        if v>=6,c='w';else,c=rgb('#193b33');end
        if v==0,s='-';else,s=sprintf('%d',v);end
        label(m,j,i,s,'HorizontalAlignment','center','Color',c,'FontSize',12);
    end
end
axis(m,'equal');set(m,'XLim',[.5 n+.5],'YLim',[.5 n+.5],'YDir','reverse','XTick',1:n,'YTick',1:n, ...
    'XTickLabel',compose('G%d',1:n),'YTickLabel',compose('G%d',1:n),'TickLength',[0 0],'FontSize',11);
annotation(f,'textbox',[.68 .76 .26 .05],'String','Pairwise weights','FontName','Times New Roman','FontSize',16,'EdgeColor','none','Color',rgb('#193b33'));
annotation(f,'textbox',[.68 .14 .28 .05],'String','Ribbon width follows the same matrix.','FontName','Times New Roman','FontSize',12,'EdgeColor','none','Color',rgb('#5c7061'));
end

function f = cluster(d)
f=canvas();order=d.order(:)+1;matrix=d.matrix(order,order);
tree=axis_at(f,[.12 .79 .69 .13]);axis(tree,'off');
for i=1:size(d.treeX,1),plot(tree,d.treeX(i,:)+1,d.treeY(i,:),'Color',rgb('#286b56'),'LineWidth',1.2);end
set(tree,'XLim',[.5 12.5]);
a=axis_at(f,[.12 .11 .69 .66]);
for i=1:12
    for j=1:12
        v=matrix(i,j);patch(a,j+[-.5 .5 .5 -.5],i+[-.5 -.5 .5 .5],diverging(v),'EdgeColor','none');
        if i>=j
            if abs(v)>.68,c='w';else,c=rgb('#193b33');end
            label(a,j,i,sprintf('%.2f',v),'HorizontalAlignment','center','FontSize',10.5,'Color',c);
        end
    end
end
set(a,'XLim',[.5 12.5],'YLim',[.5 12.5],'YDir','reverse','XTick',1:12,'YTick',1:12, ...
    'XTickLabel',compose('V%02d',order),'YTickLabel',compose('V%02d',order),'TickLength',[0 0],'FontSize',11);
vector_key(f,[.86 .18 .022 .52],[-1 1],'diverging','Pearson correlation');
end

function f = spatial(d)
f=canvas();a=axis_at(f,[.08 .13 .78 .77]);axis(a,'equal');
angle=(0:5)'*pi/3+pi/6;
for i=1:size(d.centers,1)
    x=d.centers(i,1);y=d.centers(i,2);v=d.values(i);
    patch(a,x+3.5*cos(angle),y+3.5*sin(angle),sequential(v),'EdgeColor','w','LineWidth',.65);
end
boundary=[d.polygon;d.polygon(1,:)];plot(a,boundary(:,1),boundary(:,2),'Color',rgb('#9bad99'),'LineWidth',1);
for k=1:size(d.edges,1)
    ids=d.edges(k,:)+1;plot(a,d.nodes(ids,1),d.nodes(ids,2),'Color',rgb('#d5ba8e'),'LineWidth',1.8);
end
angles=linspace(0,2*pi,40)';
for i=1:size(d.nodes,1)
    x=d.nodes(i,1);y=d.nodes(i,2);v=d.nodeValues(i);
    patch(a,x+(.95+v*.75)*cos(angles),y+(.95+v*.75)*sin(angles),'w','EdgeColor','none');
    patch(a,x+(.55+v*.5)*cos(angles),y+(.55+v*.5)*sin(angles),rgb('#193b33'),'EdgeColor','none');
    label(a,x+2,y+1.1,sprintf('N%02d',i),'FontSize',10.5);
end
set(a,'XLim',[0 102],'YLim',[0 78]);xlabel(a,'Spatial coordinate X','FontSize',14);ylabel(a,'Spatial coordinate Y','FontSize',14);
vector_key(f,[.89 .21 .022 .50],[0 1],'sequential','Normalized field');
end

function f = feasibility(d)
f=canvas();p=palette();a=axis_at(f,[.075 .14 .65 .77]);
[x,y]=meshgrid(linspace(0,105,160),linspace(0,96,145));cost=.005*(x-28).^2+.009*(y-28).^2+.002*x.*y;
contour(a,x,y,cost,[5 10 20 35 50 65],'LineColor',rgb('#c8d5c4'),'LineWidth',.9);
theta=linspace(0,2*pi,600)';theta(end)=[];polygon=polyshape(54+34*cos(theta),49+27*sin(theta));
linear=polyshape([0 95-19*.65 95-96*.65 0],[19 19 96 96]);region=intersect(polygon,linear);
plot(a,region,'FaceColor',rgb('#e1ecd7'),'FaceAlpha',1,'EdgeColor','none');
h1=plot(a,54+34*cos(theta),49+27*sin(theta),'Color',p(1,:),'LineWidth',2.1);
xx=linspace(0,105,200);h2=plot(a,xx,(95-xx)/.65,'Color',p(3,:),'LineWidth',1.6,'LineStyle','--');
h3=plot(a,[0 105],[19 19],'Color',p(2,:),'LineWidth',1.5,'LineStyle',':');
origin=d.origin;projected=d.projected;distance=sqrt(sum((origin-projected).^2,2));
for i=1:size(origin,1)
    pp=origin(i,:);qq=projected(i,:);v=qq-pp;
    plot(a,pp(1),pp(2),'x','Color',p(i,:),'MarkerSize',8,'LineWidth',1.8);
    quiver(a,pp(1),pp(2),v(1),v(2),0,'Color',p(i,:),'LineWidth',1.8,'MaxHeadSize',.35);
    plot(a,qq(1),qq(2),'o','Color',p(i,:),'MarkerFaceColor',p(i,:),'MarkerSize',5);
    label(a,pp(1)+2,pp(2)+2,sprintf('S%d',i),'FontSize',11);
end
label(a,47,44,'Feasible domain','HorizontalAlignment','center','FontSize',14,'Color',p(1,:));
set(a,'XLim',[0 105],'YLim',[0 96]);xlabel(a,'State variable u1','FontSize',14);ylabel(a,'State variable u2','FontSize',14);
lg=legend(a,[h1 h2 h3],{'Elliptic boundary','Linear boundary','Lower bound'},'NumColumns',3,'Box','off','FontSize',11);
lg.Units='normalized';lg.Position=[.085 .93 .63 .035];
b=axis_at(f,[.80 .21 .14 .61]);
for i=1:numel(distance)
    yy=8-i;plot(b,[0 distance(i)],[yy yy],'Color',p(i,:),'LineWidth',2);
    plot(b,distance(i),yy,'o','Color',p(i,:),'MarkerFaceColor',p(i,:),'MarkerSize',6);
    label(b,distance(i)+.6,yy,sprintf('%.1f',distance(i)),'FontSize',11);
end
set(b,'XLim',[0 max(distance)+8],'YLim',[-.6 7.6],'YTick',0:7,'YTickLabel',compose('S%d',8:-1:1));
xlabel(b,'Displacement','FontSize',14);
end
