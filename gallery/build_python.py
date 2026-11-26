"""Generate independent illustrative data and six complex PNG chart examples.

These analytic and seeded synthetic examples demonstrate visual encodings.
They contain no project documents, client data, or research conclusions.
Run from any directory with the repository's scientific Python requirements.
"""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, PathPatch
from matplotlib.path import Path as MPath
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import pdist
from scipy.optimize import minimize
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/downloads/figures/python'
PREVIEW = ROOT / 'docs/assets/charts'
ROLE_COLORS = json.loads((ROOT/'gallery/figure-palette.json').read_text(encoding='utf-8'))
COLORS = ROLE_COLORS['colors']
INK, GRID = COLORS['ink'], COLORS['grid']
JADE = COLORS['state']
PALETTE = ROLE_COLORS['categorical']
CMAP = LinearSegmentedColormap.from_list('projectx-sequential', ROLE_COLORS['sequential'], N=4096)
DIV = LinearSegmentedColormap.from_list('projectx-signed', ROLE_COLORS['signed'], N=4097)


def cell_text_color(color):
    # Contrast based on the rendered fill, shared by sequential and signed maps.
    rgb = np.array(color[:3])
    linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055)**2.4)
    luminance = linear @ [.2126, .7152, .0722]
    return 'white' if luminance < .179 else INK



def illustrative_data():
    rng = np.random.default_rng(1031)
    time = np.linspace(0, 24, 97)
    reference = 48 + 15*np.sin((time-5)*np.pi/12) + 5*np.cos(time*np.pi/6)
    paths = np.array([reference + 4*np.sin(time*.55+rng.uniform(-1, 1)) + rng.normal(0, 2, time.size) for _ in range(60)])
    mean = paths.mean(axis=0)
    q10, q90 = np.quantile(paths, [.1, .9], axis=0)
    capacity = 78 + 6*np.cos((time-3)*np.pi/12)
    ridge_x = np.linspace(-4, 16, 160)
    ridge_samples = [np.r_[rng.normal(i*1.15, .8+.07*i, 350), rng.normal(i*1.15+2.2, .7+.04*i, 150)] for i in range(8)]
    density = [gaussian_kde(v)(ridge_x) for v in ridge_samples]
    quantiles = [np.quantile(v, [.25,.5,.75]) for v in ridge_samples]
    flow = rng.integers(1, 10, (8,8)).astype(float)
    flow = np.triu(flow*(rng.uniform(size=(8,8))>.44), 1)
    flow = flow + flow.T
    for i in range(8):
        if flow[i].sum()==0:flow[i, (i+1)%8]=flow[(i+1)%8, i]=3
    t = np.linspace(0, 6*np.pi, 192)
    latent = np.array([np.sin(t), np.cos(.65*t+.7), np.sin(.4*t+.3)])
    signals = np.array([latent[i//4] + .22*rng.normal(size=t.size) + .12*latent[(i//4+1)%3] for i in range(12)])
    correlation = np.corrcoef(signals)
    dd = dendrogram(linkage(pdist(signals, metric='correlation'), method='average'), no_plot=True)
    polygon = np.array([[6,14],[18,6],[46,10],[68,4],[91,20],[96,46],[82,66],[52,73],[32,66],[11,45]])
    centers = np.array([[x+(row%2)*3.1,y] for row,y in enumerate(np.arange(6,73,5.35)) for x in np.arange(5,98,6.2)])
    centers = centers[MPath(polygon).contains_points(centers)]
    def field(x,y):return .2+.65*np.exp(-((x-31)**2+(y-43)**2)/450)+.43*np.exp(-((x-76)**2+(y-30)**2)/300)
    field_values = field(centers[:,0], centers[:,1])
    nodes = np.array([[19,20],[25,40],[31,56],[40,31],[45,48],[51,19],[58,37],[63,58],[72,25],[77,43],[83,53],[31,21]])
    node_values = field(nodes[:,0],nodes[:,1])
    distances = np.linalg.norm(nodes[:,None,:]-nodes[None,:,:], axis=2)
    edges = sorted({tuple(sorted((i,j))) for i in range(len(nodes)) for j in np.argsort(distances[i])[1:3]})
    origin = np.array([[15,75],[29,82],[45,86],[83,78],[98,55],[96,30],[62,10],[10,32]],float)
    def ellipse(z):return 1-((z[0]-54)/34)**2-((z[1]-49)/27)**2
    projected=[]
    for point in origin:
        res=minimize(lambda z:np.sum((z-point)**2), [54,49], jac=lambda z:2*(z-point), constraints=[{'type':'ineq','fun':ellipse,'jac':lambda z:np.array([-2*(z[0]-54)/34**2,-2*(z[1]-49)/27**2])},{'type':'ineq','fun':lambda z:95-z[0]-.65*z[1],'jac':lambda z:np.array([-1.,-.65])},{'type':'ineq','fun':lambda z:z[1]-19,'jac':lambda z:np.array([0.,1.])}], method='SLSQP', options={'ftol':1e-8,'maxiter':300})
        if not res.success:raise ValueError('Illustrative projection did not converge')
        projected.append(res.x)
    return {
        'schema':'projectx.illustrative-charts.v1', 'seed':1031,
        'trajectory':{'time':time.tolist(),'reference':reference.tolist(),'mean':mean.tolist(),'low':q10.tolist(),'high':q90.tolist(),'capacity':capacity.tolist()},
        'ridges':{'x':ridge_x.tolist(),'density':np.array(density).tolist(),'quantiles':np.array(quantiles).tolist(),'sampleCount':500},
        'chord':{'matrix':flow.tolist()},
        'cluster':{'matrix':correlation.tolist(),'order':[int(i) for i in dd['leaves']],'treeX':(np.array(dd['icoord'])/10-.5).tolist(),'treeY':dd['dcoord']},
        'spatial':{'polygon':polygon.tolist(),'centers':centers.tolist(),'values':field_values.tolist(),'nodes':nodes.tolist(),'nodeValues':node_values.tolist(),'edges':[[int(i),int(j)] for i,j in edges]},
        'feasibility':{'origin':origin.tolist(),'projected':np.array(projected).tolist()},
    }


def style(ax):
    ax.set_facecolor('white')
    ax.tick_params(labelsize=13,colors=INK,length=4)
    for key in ['top','right']:ax.spines[key].set_visible(False)
    for key in ['left','bottom']:ax.spines[key].set_color('#DADAE2')
    ax.xaxis.label.set_color(INK);ax.yaxis.label.set_color(INK)
    ax.xaxis.label.set_size(14);ax.yaxis.label.set_size(14)


def base():return plt.figure(figsize=(16,9.6),facecolor='white')


def save(fig,slug):
    OUT.mkdir(parents=True,exist_ok=True);PREVIEW.mkdir(parents=True,exist_ok=True)
    p=OUT/(slug+'.png');fig.savefig(p,dpi=150,facecolor='white');plt.close(fig)
    with Image.open(p) as im:
        im.resize((1440,864),Image.Resampling.LANCZOS).save(PREVIEW/('python-'+slug+'.webp'),'WEBP',quality=92,method=6)


def trajectory(d):
    a={k:np.array(v) for k,v in d.items()};x=a['time'];f=base()
    ax=f.add_axes([.09,.42,.85,.50]);style(ax)
    ax.fill_between(x,a['low'],a['high'],color=COLORS['observation_wash'],label='10–90% envelope')
    ax.plot(x,a['reference'],color=COLORS['observation'],lw=1.65,ls=':',label='Reference')
    ax.plot(x,a['mean'],color=COLORS['state'],lw=2.65,label='Central profile')
    ax.plot(x,a['capacity'],color=INK,lw=1.8,ls='--',label='Upper bound')
    ax.set(xlim=(0,24),ylim=(20,95),ylabel='Signal / a.u.')
    ax.grid(axis='y',color=GRID,lw=.6);ax.set_xticklabels([])
    ax.legend(ncol=4,frameon=False,loc='upper center',bbox_to_anchor=(.5,1.13),fontsize=12)
    ax2=f.add_axes([.09,.15,.85,.20]);style(ax2)
    margin=a['capacity']-a['mean'];envelope_margin=a['capacity']-a['high']
    minimum=int(np.argmin(envelope_margin))
    ax2.fill_between(x,envelope_margin,margin,color=COLORS['observation_wash'])
    ax2.plot(x,margin,color=JADE,lw=2,label='Mean margin')
    ax2.plot(x,envelope_margin,color=COLORS['observation'],lw=1.65,ls='--',label='P90 margin')
    ax2.axhline(0,color=INK,lw=.7)
    ax2.plot(x[minimum],envelope_margin[minimum],'D',ms=6,mfc=COLORS['attention'],mec=INK,zorder=4)
    ax2.annotate(f'{envelope_margin[minimum]:.1f}',(x[minimum],envelope_margin[minimum]),
                 xytext=(6,9),textcoords='offset points',fontsize=12,color=INK)
    ax2.set(xlim=(0,24),ylim=(min(-4,float(envelope_margin.min())-4),float(margin.max())+7),xlabel='Time / h',ylabel='Bound margin / a.u.',xticks=np.arange(0,25,3))
    ax2.legend(ncol=2,frameon=False,loc='lower center',bbox_to_anchor=(.5,1.0),fontsize=11)
    ax2.grid(axis='y',color=GRID,lw=.6)
    return f


def ridges(d):
    f=base();ax=f.add_axes([.12,.14,.75,.76]);style(ax)
    x=np.array(d['x']);dens=np.array(d['density']);q=np.array(d['quantiles'])
    for i in range(8):
        y=(7-i)*1.06;z=dens[i]/dens.max()*1.65
        color=CMAP(.32+i*.07)
        ax.fill_between(x,y,y+z,color=color,edgecolor='white',lw=1.4,zorder=10-i)
        ax.plot(x,y+z,color=INK,lw=.75,zorder=10-i)
        center=y+.13
        ax.plot(q[i,[0,2]],[center,center],color='white',lw=4,zorder=30)
        ax.plot(q[i,1],center,'o',ms=5,color=INK,zorder=31)
        ax.text(-3.7,y+.2,f'C{i+1:02}',ha='right',va='center',fontsize=13,color=INK)
        ax.text(16.3,y+.2,f'{q[i,1]:.2f}',ha='left',va='center',fontsize=13,color=INK)
    ax.set(xlim=(-4,18),ylim=(-.15,9.15),xlabel='Illustrative response / a.u.',yticks=[],xticks=np.arange(-4,17,4))
    ax.spines['left'].set_visible(False)
    ax.text(16.3,8.9,'Median',ha='left',fontsize=13,color=INK)
    ax.text(-3.7,8.9,'Condition',ha='right',fontsize=13,color=INK)
    return f


def ribbon_vertices(ai,aj,r=.91):
    def arc(a):return np.c_[np.cos(a),np.sin(a)]*r
    left,right=arc(np.linspace(*ai,24)),arc(np.linspace(*aj,24))
    def curve(p,q):
        t=np.linspace(0,1,35)[:,None]
        return (1-t)**3*p+3*(1-t)**2*t*(p*.15)+3*(1-t)*t**2*(q*.15)+t**3*q
    return np.vstack([left,curve(left[-1],right[0]),right,curve(right[-1],left[0])])


def chord(d):
    a=np.array(d['matrix']);n=len(a);f=base()
    ax=f.add_axes([.035,.10,.59,.82]);ax.set_aspect('equal');ax.axis('off')
    gap=.055;scale=(2*np.pi-n*gap)/a.sum();theta=.15;arcs=[];segments={}
    for i in range(n):
        begin=theta;theta+=a[i].sum()*scale;arcs.append((begin,theta));cursor=begin
        for j in range(n):segments[i,j]=(cursor,cursor+a[i,j]*scale);cursor+=a[i,j]*scale
        theta+=gap
    for i in range(n):
        for j in range(i+1,n):
            if a[i,j]>0:
                alpha=.78 if a[i,j]==a.max() else .28
                color=np.array(matplotlib.colors.to_rgb(PALETTE[i]))*alpha+1-alpha
                ax.add_patch(Polygon(ribbon_vertices(segments[i,j],segments[j,i]),closed=True,facecolor=color,edgecolor='white',lw=.5))
    for i,(start,end) in enumerate(arcs):
        t=np.linspace(start,end,70);poly=np.r_[np.c_[np.cos(t),np.sin(t)],np.c_[np.cos(t[::-1]),np.sin(t[::-1])]*.93]
        ax.add_patch(Polygon(poly,facecolor=PALETTE[i],edgecolor='white',lw=1.1))
        mid=(start+end)/2;ax.text(np.cos(mid)*1.13,np.sin(mid)*1.13,f'G{i+1}',ha='center',va='center',fontsize=15,color=INK)
    ax.set(xlim=(-1.3,1.3),ylim=(-1.3,1.3))
    m=f.add_axes([.68,.25,.255,.45]);style(m)
    m.imshow(a,cmap=CMAP,vmin=0,vmax=9,aspect='equal',interpolation='nearest')
    for i in range(n):
        for j in range(n):
            value=a[i,j]
            m.text(j,i,str(int(value)) if value else '·',ha='center',va='center',
                   color=cell_text_color(CMAP(value/9)),fontsize=13)
            if value==a.max():
                m.add_patch(plt.Rectangle((j-.47,i-.47),.94,.94,fill=False,ec='white',lw=1.5))
    m.set(xticks=range(n),yticks=range(n),xticklabels=[f'G{i+1}' for i in range(n)],yticklabels=[f'G{i+1}' for i in range(n)])
    m.tick_params(length=0,pad=8,labelsize=11)
    f.text(.68,.77,'Pairwise weights',fontsize=16,color=INK)
    f.text(.68,.16,'Outlined cells: largest pairs',fontsize=13,color=INK)
    return f


def cluster(d):
    f=base();order=np.array(d['order']);a=np.array(d['matrix'])[np.ix_(order,order)]
    tree=f.add_axes([.12,.79,.69,.13]);tree.axis('off')
    for x,y in zip(d['treeX'],d['treeY']):tree.plot(x,y,color=INK,lw=1.35)
    tree.set_xlim(-.5,11.5)
    ax=f.add_axes([.12,.11,.69,.66]);style(ax)
    ax.imshow(a,cmap=DIV,vmin=-1,vmax=1,aspect='auto',interpolation='nearest')
    for i in range(12):
        for j in range(12):
            if i>=j:ax.text(j,i,f'{a[i,j]:.2f}',ha='center',va='center',fontsize=11.5,
                            color=cell_text_color(DIV((a[i,j]+1)/2)))
    labels=[f'V{i+1:02}' for i in order]
    ax.set(xticks=range(12),yticks=range(12),xticklabels=labels,yticklabels=labels)
    ax.tick_params(length=0,pad=8,labelsize=11)
    cb=f.colorbar(ax.images[0],cax=f.add_axes([.86,.18,.022,.52]));cb.set_label('Pearson correlation',fontsize=13,color=INK);cb.ax.tick_params(labelsize=12)
    return f


def spatial(d):
    f=base();ax=f.add_axes([.075,.13,.57,.77]);style(ax);ax.set_aspect('equal')
    centers=np.array(d['centers']);values=np.array(d['values']);nodes=np.array(d['nodes']);nv=np.array(d['nodeValues'])
    boundary=np.r_[np.array(d['polygon']),[d['polygon'][0]]]
    clip=PathPatch(MPath(boundary,closed=True),transform=ax.transData)
    angle=np.arange(6)*np.pi/3+np.pi/6
    for (x,y),value in zip(centers,values):
        points=np.c_[x+3.50*np.cos(angle),y+3.50*np.sin(angle)]
        tile=Polygon(points,facecolor=CMAP(value),edgecolor='white',lw=.65)
        tile.set_clip_path(clip)
        ax.add_patch(tile)
    ax.plot(boundary[:,0],boundary[:,1],color='#131419',lw=1)
    for i,j in d['edges']:ax.plot(nodes[[i,j],0],nodes[[i,j],1],color='#2452DC',lw=1.8,zorder=3)
    for i,((x,y),value) in enumerate(zip(nodes,nv)):
        ax.add_patch(plt.Circle((x,y),.95+value*.75,color='white',zorder=4))
        ax.add_patch(plt.Circle((x,y),.55+value*.5,color=INK,zorder=5))
        ax.text(x+2.0,y+1.1,f'N{i+1:02}',fontsize=10.5,color=INK,zorder=6)
    ax.set(xlim=(0,102),ylim=(0,78),xlabel='Spatial coordinate X',ylabel='Spatial coordinate Y')
    sm=matplotlib.cm.ScalarMappable(cmap=CMAP,norm=plt.Normalize(0,1))
    cb=f.colorbar(sm,cax=f.add_axes([.65,.26,.018,.39]));cb.set_label('Normalized field',fontsize=13,color=INK);cb.ax.tick_params(labelsize=12)
    right=f.add_axes([.795,.20,.15,.62]);style(right)
    order=np.argsort(nv,kind='stable');levels=np.arange(len(order))
    right.hlines(levels,0,nv[order],color=GRID,lw=1.1)
    right.scatter(nv[order],levels,c=CMAP(nv[order]),s=35,edgecolor=INK,zorder=3)
    right.set(xlim=(0,1),ylim=(-.5,len(order)-.5),xlabel='Sampled node field',
              yticks=levels,yticklabels=[f'N{i+1:02}' for i in order],xticks=[0,.5,1])
    return f


def feasibility(d):
    f=base();ax=f.add_axes([.075,.14,.61,.77]);style(ax);ax.set_aspect('equal',adjustable='box')
    x=np.linspace(0,105,160);y=np.linspace(0,96,145);xx,yy=np.meshgrid(x,y)
    ellipse=((xx-54)/34)**2+((yy-49)/27)**2
    feasible=(ellipse<=1)&(xx+.65*yy<=95)&(yy>=19)
    ax.contourf(xx,yy,feasible.astype(float),levels=[.5,1.5],colors=['#E6F8F2'])
    theta=np.linspace(0,2*np.pi,500)
    ax.plot(54+34*np.cos(theta),49+27*np.sin(theta),color=COLORS['alternative'],lw=2.1,label='E: Elliptic boundary')
    ax.plot(x,(95-x)/.65,color=COLORS['exceedance'],lw=1.6,ls='--',label='L: Linear boundary')
    ax.axhline(19,color=COLORS['observation'],lw=1.5,ls=':',label='F: Lower bound')
    origin=np.array(d['origin']);projected=np.array(d['projected']);distance=np.linalg.norm(projected-origin,axis=1)
    for i,(p,q) in enumerate(zip(origin,projected)):
        ax.plot(*p,marker='x',color=INK,ms=8,mew=1.8)
        ax.annotate('',xy=q,xytext=p,arrowprops={'arrowstyle':'-|>','color':INK,'lw':1.45,'mutation_scale':13})
        ax.plot(*q,marker='o',color=INK,mfc=COLORS['state'],ms=5)
        ax.text(p[0]+2,p[1]+2,f'S{i+1}',fontsize=11,color=INK)
    ax.text(47,44,'Feasible domain',ha='center',fontsize=14,color=JADE)
    ax.set(xlim=(0,105),ylim=(0,96),xlabel='State variable u1',ylabel='State variable u2')
    ax.legend(loc='upper left',ncol=3,bbox_to_anchor=(-.01,1.12),frameon=False,fontsize=11)
    dist=f.add_axes([.76,.21,.18,.61]);style(dist)
    px,py=projected.T
    active=np.abs(np.c_[((px-54)/34)**2+((py-49)/27)**2-1, px+.65*py-95, py-19])<1e-5
    dist.text(.0,1.07,'Binding at projection',transform=dist.transAxes,fontsize=13,color=INK)
    for i,value in enumerate(distance):
        dist.plot([0,value],[7-i,7-i],color=GRID,lw=1.4)
        dist.plot(value,7-i,'o',ms=6,mfc=COLORS['state'],mec=INK)
        tags=' + '.join(np.array(['E','L','F'])[active[i]])
        dist.text(value+1.0,7-i,f'{value:.1f}  {tags}',fontsize=12,va='center',color=INK)
    dist.set(yticks=range(8),yticklabels=[f'S{i}' for i in range(8,0,-1)],ylim=(-.6,7.6),xlim=(0,max(distance)+14),xlabel='Euclidean displacement')
    return f


def main():
    plt.rcParams.update({'font.family':'Times New Roman','font.size':12,'axes.unicode_minus':False,'savefig.facecolor':'white'})
    d=illustrative_data()
    (ROOT/'gallery/demo-data.json').write_text(json.dumps(d,separators=(',',':')),encoding='utf-8')
    builders={'trajectory':trajectory,'ridges':ridges,'chord':chord,'cluster':cluster,'spatial':spatial,'feasibility':feasibility}
    for slug,fn in builders.items():save(fn(d[slug]),slug);print('Python PNG:',slug,flush=True)


if __name__=='__main__':main()
