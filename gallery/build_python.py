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
INK = '#193b33'
TEAL = '#286b56'
GRID = '#e1e7df'
PALETTE = ['#286b56', '#54849c', '#bc8856', '#837799', '#7e9a67', '#ae6f78', '#5b9c9b', '#b4a269']
CMAP = LinearSegmentedColormap.from_list('botanical', ['#f1f3dc', '#c3d8a4', '#74a78f', '#286b56', '#163c36'])
DIV = LinearSegmentedColormap.from_list('signed', ['#8d647d', '#cbb7c3', '#fafaf4', '#b0cbb5', '#286b56'])


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
    ax.tick_params(labelsize=12,colors=INK,length=4)
    for key in ['top','right']:ax.spines[key].set_visible(False)
    for key in ['left','bottom']:ax.spines[key].set_color('#abbdb1')
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
    ax.fill_between(x,a['low'],a['high'],color='#c7ddca',label='10–90% envelope')
    ax.plot(x,a['reference'],color=PALETTE[1],lw=1.8,ls='--',label='Reference')
    ax.plot(x,a['mean'],color=TEAL,lw=2.7,label='Central profile')
    ax.plot(x,a['capacity'],color=PALETTE[2],lw=1.8,ls='-.',label='Upper bound')
    ax.set(xlim=(0,24),ylim=(20,95),ylabel='Signal / a.u.')
    ax.grid(axis='y',color=GRID,lw=.6);ax.set_xticklabels([])
    ax.legend(ncol=4,frameon=False,loc='upper center',bbox_to_anchor=(.5,1.13),fontsize=12)
    ax2=f.add_axes([.09,.15,.85,.20]);style(ax2)
    margin=a['capacity']-a['mean']
    ax2.fill_between(x,0,margin,color='#d7e5bf');ax2.plot(x,margin,color=TEAL,lw=2)
    ax2.set(xlim=(0,24),ylim=(0,65),xlabel='Time / h',ylabel='Bound margin / a.u.',xticks=np.arange(0,25,3))
    ax2.grid(axis='y',color=GRID,lw=.6)
    return f


def ridges(d):
    f=base();ax=f.add_axes([.12,.14,.75,.76]);style(ax)
    x=np.array(d['x']);dens=np.array(d['density']);q=np.array(d['quantiles'])
    for i in range(8):
        y=(7-i)*1.06;z=dens[i]/dens.max()*1.65
        color=CMAP(.2+i*.09)
        ax.fill_between(x,y,y+z,color=color,edgecolor='white',lw=1.4,zorder=10-i)
        ax.plot(x,y+z,color=TEAL,lw=.7,zorder=10-i)
        center=y+.13
        ax.plot(q[i,[0,2]],[center,center],color='white',lw=4,zorder=30)
        ax.plot(q[i,1],center,'o',ms=5,color=INK,zorder=31)
        ax.text(-3.7,y+.2,f'C{i+1:02}',ha='right',va='center',fontsize=13,color=INK)
        ax.text(16.3,y+.2,f'{q[i,1]:.2f}',ha='left',va='center',fontsize=13,color=INK)
    ax.set(xlim=(-3.5,18),ylim=(-.15,9.15),xlabel='Illustrative response / a.u.',yticks=[])
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
                color=np.array(matplotlib.colors.to_rgb(PALETTE[i]))*.42+.58
                ax.add_patch(Polygon(ribbon_vertices(segments[i,j],segments[j,i]),closed=True,facecolor=color,edgecolor='white',lw=.5))
    for i,(start,end) in enumerate(arcs):
        t=np.linspace(start,end,70);poly=np.r_[np.c_[np.cos(t),np.sin(t)],np.c_[np.cos(t[::-1]),np.sin(t[::-1])]*.93]
        ax.add_patch(Polygon(poly,facecolor=PALETTE[i],edgecolor='white',lw=1.1))
        mid=(start+end)/2;ax.text(np.cos(mid)*1.13,np.sin(mid)*1.13,f'G{i+1}',ha='center',va='center',fontsize=15,color=INK)
    ax.set(xlim=(-1.3,1.3),ylim=(-1.3,1.3))
    m=f.add_axes([.68,.25,.255,.45]);style(m)
    m.imshow(a,cmap=CMAP,vmin=0,vmax=9,aspect='equal',interpolation='nearest')
    for i in range(n):
        for j in range(n):m.text(j,i,str(int(a[i,j])) if a[i,j] else '·',ha='center',va='center',color='white' if a[i,j]>=6 else INK,fontsize=12)
    m.set(xticks=range(n),yticks=range(n),xticklabels=[f'G{i+1}' for i in range(n)],yticklabels=[f'G{i+1}' for i in range(n)])
    m.tick_params(length=0,pad=8,labelsize=11)
    f.text(.68,.77,'Pairwise weights',fontsize=16,color=INK)
    f.text(.68,.16,'Ribbon width follows the same matrix.',fontsize=12,color='#5c7061')
    return f


def cluster(d):
    f=base();order=np.array(d['order']);a=np.array(d['matrix'])[np.ix_(order,order)]
    tree=f.add_axes([.12,.79,.69,.13]);tree.axis('off')
    for x,y in zip(d['treeX'],d['treeY']):tree.plot(x,y,color=TEAL,lw=1.2)
    tree.set_xlim(-.5,11.5)
    ax=f.add_axes([.12,.11,.69,.66]);style(ax)
    ax.imshow(a,cmap=DIV,vmin=-1,vmax=1,aspect='auto',interpolation='nearest')
    for i in range(12):
        for j in range(12):
            if i>=j:ax.text(j,i,f'{a[i,j]:.2f}',ha='center',va='center',fontsize=10.5,color='white' if abs(a[i,j])>.68 else INK)
    labels=[f'V{i+1:02}' for i in order]
    ax.set(xticks=range(12),yticks=range(12),xticklabels=labels,yticklabels=labels)
    ax.tick_params(length=0,pad=8,labelsize=11)
    cb=f.colorbar(ax.images[0],cax=f.add_axes([.86,.18,.022,.52]));cb.set_label('Pearson correlation',fontsize=13,color=INK);cb.ax.tick_params(labelsize=12)
    return f


def spatial(d):
    f=base();ax=f.add_axes([.08,.13,.78,.77]);style(ax);ax.set_aspect('equal')
    centers=np.array(d['centers']);values=np.array(d['values']);nodes=np.array(d['nodes']);nv=np.array(d['nodeValues'])
    angle=np.arange(6)*np.pi/3+np.pi/6
    for (x,y),value in zip(centers,values):
        points=np.c_[x+3.50*np.cos(angle),y+3.50*np.sin(angle)]
        ax.add_patch(Polygon(points,facecolor=CMAP(value),edgecolor='white',lw=.65))
    boundary=np.r_[np.array(d['polygon']),[d['polygon'][0]]]
    ax.plot(boundary[:,0],boundary[:,1],color='#9bad99',lw=1)
    for i,j in d['edges']:ax.plot(nodes[[i,j],0],nodes[[i,j],1],color='#d5ba8e',lw=1.8,zorder=3)
    for i,((x,y),value) in enumerate(zip(nodes,nv)):
        ax.add_patch(plt.Circle((x,y),.95+value*.75,color='white',zorder=4))
        ax.add_patch(plt.Circle((x,y),.55+value*.5,color=INK,zorder=5))
        ax.text(x+2.0,y+1.1,f'N{i+1:02}',fontsize=10.5,color=INK,zorder=6)
    ax.set(xlim=(0,102),ylim=(0,78),xlabel='Spatial coordinate X',ylabel='Spatial coordinate Y')
    sm=matplotlib.cm.ScalarMappable(cmap=CMAP,norm=plt.Normalize(0,1))
    cb=f.colorbar(sm,cax=f.add_axes([.89,.21,.022,.50]));cb.set_label('Normalized field',fontsize=13,color=INK);cb.ax.tick_params(labelsize=12)
    return f


def feasibility(d):
    f=base();ax=f.add_axes([.075,.14,.65,.77]);style(ax)
    x=np.linspace(0,105,160);y=np.linspace(0,96,145);xx,yy=np.meshgrid(x,y)
    cost=.005*(xx-28)**2+.009*(yy-28)**2+.002*xx*yy
    ax.contour(xx,yy,cost,levels=[5,10,20,35,50,65],colors='#c8d5c4',linewidths=.9)
    ellipse=((xx-54)/34)**2+((yy-49)/27)**2
    feasible=(ellipse<=1)&(xx+.65*yy<=95)&(yy>=19)
    ax.contourf(xx,yy,feasible.astype(float),levels=[.5,1.5],colors=['#e1ecd7'])
    theta=np.linspace(0,2*np.pi,500)
    ax.plot(54+34*np.cos(theta),49+27*np.sin(theta),color=TEAL,lw=2.1,label='Elliptic boundary')
    ax.plot(x,(95-x)/.65,color=PALETTE[2],lw=1.6,ls='--',label='Linear boundary')
    ax.axhline(19,color=PALETTE[1],lw=1.5,ls=':',label='Lower bound')
    origin=np.array(d['origin']);projected=np.array(d['projected']);distance=np.linalg.norm(projected-origin,axis=1)
    for i,(p,q) in enumerate(zip(origin,projected)):
        color=PALETTE[i];ax.plot(*p,marker='x',color=color,ms=8,mew=1.8)
        ax.annotate('',xy=q,xytext=p,arrowprops={'arrowstyle':'-|>','color':color,'lw':1.8,'mutation_scale':13})
        ax.plot(*q,marker='o',color=color,ms=5)
        ax.text(p[0]+2,p[1]+2,f'S{i+1}',fontsize=11,color=INK)
    ax.text(47,44,'Feasible domain',ha='center',fontsize=14,color=TEAL)
    ax.set(xlim=(0,105),ylim=(0,96),xlabel='State variable u1',ylabel='State variable u2')
    ax.legend(loc='upper left',ncol=3,bbox_to_anchor=(-.01,1.12),frameon=False,fontsize=11)
    dist=f.add_axes([.80,.21,.14,.61]);style(dist)
    for i,value in enumerate(distance):
        dist.plot([0,value],[7-i,7-i],color=PALETTE[i],lw=2)
        dist.plot(value,7-i,'o',ms=6,color=PALETTE[i]);dist.text(value+.6,7-i,f'{value:.1f}',fontsize=11,va='center',color=INK)
    dist.set(yticks=range(8),yticklabels=[f'S{i}' for i in range(8,0,-1)],ylim=(-.6,7.6),xlim=(0,max(distance)+8),xlabel='Displacement')
    return f


def main():
    plt.rcParams.update({'font.family':'Times New Roman','font.size':12,'axes.unicode_minus':False,'savefig.facecolor':'white'})
    d=illustrative_data()
    (ROOT/'gallery/demo-data.json').write_text(json.dumps(d,separators=(',',':')),encoding='utf-8')
    builders={'trajectory':trajectory,'ridges':ridges,'chord':chord,'cluster':cluster,'spatial':spatial,'feasibility':feasibility}
    for slug,fn in builders.items():save(fn(d[slug]),slug);print('Python PNG:',slug,flush=True)


if __name__=='__main__':main()
