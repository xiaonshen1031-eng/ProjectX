"""Eight additional chart families from independently generated demonstration data."""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from scipy.stats import gaussian_kde
from scipy.signal import stft
from build_python import ROOT, INK, JADE, GRID, PALETTE, CMAP, COLORS, style, base, save

SLUGS=['sankey','raincloud','polar','parallel','calibration','spectrum','forest','gantt']


def generate():
    rng=np.random.default_rng(202610)
    f1=rng.integers(4,18,(4,4)).astype(float)
    proportions=rng.uniform(.5,2,(4,3));f2=f1.sum(axis=0)[:,None]*proportions/proportions.sum(axis=1)[:,None]
    stages=[f1.sum(axis=1),f1.sum(axis=0),f2.sum(axis=0)];scale=.76/stages[0].sum()
    nodes=[];ranges=[]
    for k,values in enumerate(stages):
        cursor=.1;rs=[]
        for i,value in enumerate(values):
            h=value*scale;rs.append([cursor,cursor+h]);nodes.append([k,i,cursor,h,float(value)]);cursor+=h+.025
        ranges.append(rs)
    links=[]
    for k,matrix in enumerate([f1,f2]):
        left=np.array([r[0] for r in ranges[k]]);right=np.array([r[0] for r in ranges[k+1]])
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                h=matrix[i,j]*scale;x0=.08+k*.43+.028;x1=.08+(k+1)*.43
                t=np.linspace(0,1,35);x=x0+(x1-x0)*(3*t*t-2*t*t*t)
                lo=left[i]+(right[j]-left[i])*(3*t*t-2*t*t*t)
                links.append({'x':np.r_[x,x[::-1]].tolist(),'y':np.r_[lo,(lo+h)[::-1]].tolist(),'color':int(i),'value':float(matrix[i,j])})
                left[i]+=h;right[j]+=h
    samples=np.array([rng.normal(mu,.5+.11*i,240)+rng.exponential(.25,240) for i,mu in enumerate([1.0,1.9,2.7,3.4])])
    rx=np.linspace(-1,6.5,180);rd=np.array([gaussian_kde(v)(rx) for v in samples]);rq=np.quantile(samples,[.1,.25,.5,.75,.9],axis=1).T
    hours=np.arange(24);circular=np.array([.45+.2*np.sin((hours-7+i)*np.pi/12)+.08*np.cos(hours*np.pi/6+i) for i in range(4)])
    profiles=[];groups=[]
    patterns=np.array([[.3,.7,.45,.8,.25,.55],[.7,.35,.75,.3,.65,.4],[.5,.55,.3,.55,.8,.7]])
    for k in range(3):
        for _ in range(16):profiles.append(np.clip(patterns[k]+rng.normal(0,.07,6),0,1));groups.append(k)
    probability=rng.beta(2,2,1600);truth=rng.binomial(1,probability**1.2)
    cuts=np.linspace(0,1,11);bins=[]
    for i in range(10):
        mask=(probability>=cuts[i])&(probability<cuts[i+1]);n=mask.sum();q=truth[mask].mean();z=1.96
        center=(q+z*z/(2*n))/(1+z*z/n);half=z*np.sqrt(q*(1-q)/n+z*z/(4*n*n))/(1+z*z/n)
        bins.append([float(probability[mask].mean()),float(q),float(max(0,min(q,center-half))),float(min(1,max(q,center+half))),int(n)])
    px=np.linspace(.001,.999,150);dens0=gaussian_kde(probability[truth==0])(px);dens1=gaussian_kde(probability[truth==1])(px)
    time=np.arange(512)/64;signal=np.sin(2*np.pi*(4*time+time*time))+.6*np.sin(2*np.pi*12*time)+.5*np.exp(-((time-4.5)/.7)**2)*np.sin(2*np.pi*23*time)
    frequency,window,z=stft(signal,fs=64,nperseg=64,noverlap=48,nfft=128,boundary='zeros')
    power=np.abs(z)**2;db=np.maximum(-45,10*np.log10(np.maximum(power,1e-12)/power.max()))
    differences=np.array([rng.normal(mu,.25+.045*i,36) for i,mu in enumerate(np.linspace(-.45,.75,14))])
    boot=np.array([rng.choice(v,(1200,len(v)),replace=True).mean(axis=1) for v in differences]);ci=np.quantile(boot,[.025,.975],axis=1).T
    dx=np.linspace(-2.5,3,160);dd=np.array([gaussian_kde(v)(dx) for v in differences])
    arrivals=rng.integers(0,10,16);departures=np.minimum(24,arrivals+rng.integers(7,15,16));p=np.zeros((16,24))
    for i in range(16):
        n=departures[i]-arrivals[i];p[i,arrivals[i]:departures[i]]=rng.uniform(4,10)*(1-.45*np.cos(np.linspace(0,2*np.pi,n)))
    group_power=np.array([p[i*4:(i+1)*4].sum(axis=0) for i in range(4)])
    return {
      'schema':'projectx.illustrative-extension.v1','seed':202610,
      'sankey':{'nodes':nodes,'links':links,'total':float(stages[0].sum())},
      'raincloud':{'samples':samples.tolist(),'x':rx.tolist(),'density':rd.tolist(),'quantiles':rq.tolist(),'jitter':rng.uniform(-.22,-.09,samples.shape).tolist()},
      'polar':{'values':circular.tolist()},
      'parallel':{'profiles':np.array(profiles).tolist(),'groups':groups},
      'calibration':{'bins':bins,'x':px.tolist(),'density0':dens0.tolist(),'density1':dens1.tolist(),'brier':float(np.mean((probability-truth)**2)),'n':len(truth)},
      'spectrum':{'time':time.tolist(),'signal':signal.tolist(),'frequency':frequency.tolist(),'window':window.tolist(),'db':db.tolist(),'energy':power.sum(axis=1).tolist()},
      'forest':{'mean':differences.mean(axis=1).tolist(),'ci':ci.tolist(),'x':dx.tolist(),'density':dd.tolist(),'n':36},
      'gantt':{'arrival':arrivals.tolist(),'departure':departures.tolist(),'power':p.tolist(),'groups':group_power.tolist(),'capacity':float(group_power.sum(axis=0).max()*1.12)},
    }


def sankey(d):
    f=base();a=f.add_axes([.04,.145,.91,.72]);a.axis('off')
    for link in d['links']:
        color=np.array(plt.matplotlib.colors.to_rgb(PALETTE[link['color']]))*.48+.52
        a.add_patch(Polygon(np.c_[link['x'],link['y']],color=color,ec='white',lw=.6))
    for k,i,y,h,value in d['nodes']:
        x=.08+k*.43;a.add_patch(Rectangle((x,y),.028,h,facecolor=PALETTE[int(i)],edgecolor='white'))
        name=f'{"ABC"[int(k)]}{int(i)+1}'
        align='right' if k==0 else 'left'
        if k==1:
            a.text(x+.014,y+h/2,name,ha='center',va='center',fontsize=12,color=INK,
                   bbox={'facecolor':'white','edgecolor':'none','pad':1.3})
        else:
            a.text(x-.012 if k==0 else x+.04,y+h/2,f'{name}  {value:.1f}',
                   ha=align,va='center',fontsize=13,color=INK)
    for x,s in zip([.094,.524,.954],['Inputs','Intermediate groups','Outputs']):
        a.text(x,1.025,s,ha='center',fontsize=15,color=INK)
    middle=[(int(i),value) for k,i,_,_,value in d['nodes'] if k==1]
    a.text(.524,.025,'   '.join(f'B{i+1} {value:.1f}' for i,value in middle),ha='center',fontsize=13,color=INK)
    a.set(xlim=(-.085,1.105),ylim=(-.025,1.07))
    f.text(.5,.091,f'Conserved total: {d["total"]:.1f} a.u.',ha='center',color=INK,fontsize=14)
    return f


def raincloud(d):
    f=base();a=f.add_axes([.12,.14,.81,.76]);style(a);x=np.array(d['x']);den=np.array(d['density'])
    for i in range(4):
        y=6-i*1.65;v=np.array(d['samples'][i]);q=d['quantiles'][i];color=PALETTE[i]
        a.fill_between(x,y,y+den[i]/den.max()*.95,color=color,alpha=.66,lw=0)
        a.plot(x,y+den[i]/den.max()*.95,color=INK,lw=.8)
        a.plot(v,y+np.array(d['jitter'][i]),'.',ms=3,color=color,alpha=.65)
        a.plot([q[0],q[4]],[y-.4,y-.4],lw=1.4,color=INK)
        a.add_patch(Rectangle((q[1],y-.50),q[3]-q[1],.20,facecolor='white',ec=INK,lw=1.1))
        a.plot([q[2],q[2]],[y-.5,y-.3],color=INK,lw=2)
    ranges=np.asarray(d['samples'])
    a.set(xlim=(min(-1,ranges.min()-.1),max(6.5,ranges.max()+.1)),ylim=(.3,7.2),
          yticks=[6-i*1.65 for i in range(4)],yticklabels=['C01','C02','C03','C04'],
          xlabel='Illustrative response / a.u.')
    a.spines['left'].set_visible(False)
    f.text(.12,.925,'Dots: observations    Box: quartiles    Whiskers: P10-P90',fontsize=14,color=INK)
    return f


def polar(d):
    f=base();a=f.add_axes([.04,.10,.49,.79]);a.set_aspect('equal');a.axis('off');v=np.array(d['values'])
    for i in range(4):
        for h in range(24):
            t=np.linspace(np.pi/2-(h+.5)*2*np.pi/24,np.pi/2-(h-.5)*2*np.pi/24,13)
            r0=.25+i*.16;r1=r0+.15
            xy=np.r_[np.c_[r1*np.cos(t),r1*np.sin(t)],np.c_[r0*np.cos(t[::-1]),r0*np.sin(t[::-1])]]
            a.add_patch(Polygon(xy,facecolor=CMAP(v[i,h]),ec='white',lw=.7))
    for h in range(0,24,3):
        t=np.pi/2-h*2*np.pi/24;a.text(1.03*np.cos(t),1.03*np.sin(t),f'{h:02}:00',ha='center',va='center',fontsize=13,color=INK)
    a.text(0,.035,'C01-C04',ha='center',fontsize=14,color=INK)
    a.text(0,-.085,'Inner to outer',ha='center',fontsize=12,color=INK)
    a.set(xlim=(-1.18,1.18),ylim=(-1.18,1.18))
    cax=f.add_axes([.51,.29,.017,.40])
    cb=f.colorbar(plt.matplotlib.cm.ScalarMappable(cmap=CMAP,norm=plt.Normalize(0,1)),cax=cax)
    cb.set_label('Normalized response',fontsize=13)
    b=f.add_axes([.67,.30,.27,.39]);style(b);hours=np.arange(24)
    spread=np.ptp(v,axis=0);peak=int(np.argmax(spread))
    b.fill_between(hours,0,spread,step='mid',color=COLORS['alternative_wash'])
    b.step(hours,spread,where='mid',color=COLORS['alternative'],lw=2)
    b.plot(peak,spread[peak],'D',mfc=COLORS['attention'],mec=INK,ms=7)
    b.annotate(f'{peak:02}:00 / {spread[peak]:.2f}',(peak,spread[peak]),xytext=(3,10),
               textcoords='offset points',ha='right' if peak>12 else 'left',fontsize=13)
    b.set(xlim=(0,23),ylim=(0,spread.max()*1.30),xticks=np.arange(0,24,6),
          xlabel='Hour of day',ylabel='Between-condition range')
    return f


def parallel(d):
    f=base();a=f.add_axes([.10,.16,.82,.71]);style(a);p=np.array(d['profiles']);groups=np.array(d['groups']);x=np.arange(6)
    for i in range(6):a.plot([i,i],[0,1],color='#DADAE2',lw=1)
    for k in range(3):
        rows=p[groups==k];color=PALETTE[k];lo,hi=np.quantile(rows,[.1,.9],axis=0)
        a.fill_between(x,lo,hi,color=color,alpha=.12)
        for row in rows:a.plot(x,row,color=color,alpha=.20,lw=.7)
        a.plot(x,rows.mean(axis=0),color=color,lw=2.45,ls=['-',':','--'][k],
               marker=['o','s','D'][k],ms=4,mec=INK,label=f'Group {k+1} / n=16')
    a.set(xlim=(-.05,5.05),ylim=(0,1),xticks=x,xticklabels=[f'Metric {i+1}' for i in x],ylabel='Normalized value');a.legend(ncol=3,frameon=False,bbox_to_anchor=(.5,1.14),loc='upper center',fontsize=12);return f


def calibration(d):
    f=base();b=np.array(d['bins']);a=f.add_axes([.09,.36,.49,.54]);style(a)
    a.plot([0,1],[0,1],ls='--',color='#131419',lw=1.3,label='Ideal calibration')
    a.errorbar(b[:,0],b[:,1],yerr=np.array([b[:,1]-b[:,2],b[:,3]-b[:,1]]),fmt='o-',ms=5,color=JADE,lw=1.7,capsize=3,label='Binned fraction / 95% Wilson interval')
    a.set(xlim=(0,1),ylim=(0,1),ylabel='Observed fraction');a.legend(frameon=False,loc='upper left',fontsize=11)
    count=f.add_axes([.09,.14,.49,.15]);style(count)
    count.bar(np.arange(len(b))/len(b),b[:,4],align='edge',width=1/len(b),color=COLORS['observation_wash'],edgecolor=INK,lw=.7)
    count.set(xlim=(0,1),xlabel='Predicted probability',ylabel='Count')
    den=f.add_axes([.68,.23,.25,.58]);style(den);x=np.array(d['x'])
    den.fill_between(x,0,d['density0'],color=PALETTE[1],alpha=.3);den.plot(x,d['density0'],color=PALETTE[1],lw=2,label='Label 0')
    den.fill_between(x,0,d['density1'],color=JADE,alpha=.25);den.plot(x,d['density1'],color=JADE,lw=2,label='Label 1')
    den.set(xlim=(0,1),xlabel='Predicted probability',ylabel='Density')
    den.legend(frameon=False,fontsize=11,ncol=2,loc='lower center',bbox_to_anchor=(.5,1.02))
    f.text(.68,.90,f'N = {d["n"]}   Brier = {d["brier"]:.3f}',color=INK,fontsize=14)
    return f


def spectrum(d):
    f=base();a=f.add_axes([.08,.76,.70,.17]);style(a);a.plot(d['time'],d['signal'],color=JADE,lw=.8);a.set(xlim=(0,8),ylabel='Signal',xticklabels=[])
    ax=f.add_axes([.08,.15,.70,.54]);style(ax);x=np.array(d['window']);y=np.array(d['frequency']);z=np.array(d['db'])
    im=ax.pcolormesh(x,y,z,cmap=CMAP,vmin=-45,vmax=0,shading='nearest');ax.set(xlim=(0,8),ylim=(0,32),xlabel='Time / s',ylabel='Frequency / Hz')
    side=f.add_axes([.83,.15,.12,.54]);style(side)
    side.fill_betweenx(y,0,d['energy'],color=COLORS['alternative_wash'])
    side.plot(d['energy'],y,color=COLORS['alternative'],lw=1.7)
    side.set(ylim=(0,32),xlabel='Summed STFT power',yticklabels=[])
    cb=f.colorbar(im,cax=f.add_axes([.83,.79,.12,.025]),orientation='horizontal');cb.set_label('Relative power / dB',fontsize=11);return f


def forest(d):
    f=base();a=f.add_axes([.10,.13,.47,.76]);style(a);x=np.array(d['x']);den=np.array(d['density']);means=np.array(d['mean']);ci=np.array(d['ci'])
    for i in range(14):
        y=13-i;a.fill_between(x,y,y+den[i]/den.max()*.72,color=CMAP(.34+i*.012),lw=.7,edgecolor='white')
    a.axvline(0,color='#131419',ls='--',lw=1);a.set(xlim=(-2.5,3),ylim=(-.3,14),yticks=np.arange(14),yticklabels=[f'C{i:02}' for i in range(14,0,-1)],xlabel='Paired difference distribution')
    b=f.add_axes([.65,.13,.28,.76]);style(b);b.axvline(0,color='#131419',ls='--',lw=1)
    for i in range(14):
        color,mark=(COLORS['exceedance'],'<') if ci[i,1]<0 else ((JADE,'>') if ci[i,0]>0 else (INK,'s'))
        b.plot(ci[i],[13-i,13-i],color=color,lw=1.7)
        b.plot(ci[i],[13-i,13-i],'|',ms=6,color=color)
        b.plot(means[i],13-i,mark,ms=6,mfc=color,mec=INK)
    limits=float(ci.min()),float(ci.max());pad=(limits[1]-limits[0])*.08
    b.set(ylim=(-.3,14),xlim=(limits[0]-pad,limits[1]+pad),yticks=np.arange(14),yticklabels=[],
          xlabel='Mean difference / 95% bootstrap CI')
    f.text(.10,.925,f'n = {d["n"]} / condition',fontsize=14,color=INK)
    return f


def gantt(d):
    f=base();a=f.add_axes([.09,.47,.73,.43]);style(a);p=np.array(d['power']);arrival=d['arrival'];departure=d['departure']
    for i in range(16):
        y=15-i;a.add_patch(Rectangle((arrival[i],y-.40),departure[i]-arrival[i],.80,
                                     color=COLORS['alternative_wash'],lw=0))
        c=np.array(plt.matplotlib.colors.to_rgb(PALETTE[i//4]))
        for h in range(24):
            if p[i,h]>0:a.add_patch(Rectangle((h+.025,y-.28),.95,.56,facecolor=c*(.3+.7*p[i,h]/p.max())+1-(.3+.7*p[i,h]/p.max()),lw=0))
        a.text(24.5,y,f'{p[i].sum():.1f}',va='center',fontsize=11,color=INK)
    a.set(xlim=(0,24),ylim=(-.6,15.7),yticks=np.arange(16),
          yticklabels=[f'R{i:02}' for i in range(16,0,-1)],xticklabels=[])
    a.text(24.5,16.15,'Energy / kWh',fontsize=13,color=INK)
    b=f.add_axes([.09,.27,.73,.155]);style(b);groups=np.array(d['groups'])
    hours=np.arange(25)
    b.stackplot(hours,np.c_[groups,groups[:,-1]],step='post',colors=PALETTE[:4],
                labels=['Group 1','Group 2','Group 3','Group 4'],alpha=.78)
    b.axhline(d['capacity'],color=INK,ls='--',lw=1.35,label='Study cap')
    b.set(xlim=(0,24),ylabel='Power / kW',xticklabels=[])
    b.legend(ncol=5,frameon=False,bbox_to_anchor=(.5,1.04),loc='lower center',fontsize=11)
    headroom=d['capacity']-groups.sum(axis=0);h=f.add_axes([.09,.115,.73,.10]);style(h)
    h.fill_between(hours,0,np.r_[headroom,headroom[-1]],step='post',color=COLORS['observation_wash'])
    h.step(hours,np.r_[headroom,headroom[-1]],where='post',color=COLORS['observation'],lw=1.45)
    peak=int(np.argmin(headroom));h.plot(peak+.5,headroom[peak],'D',mfc=COLORS['attention'],mec=INK,ms=6)
    h.annotate(f'{headroom[peak]:.1f}',(peak+.5,headroom[peak]),
               xytext=(6,6),textcoords='offset points',fontsize=12,color=INK)
    h.set(xlim=(0,24),ylim=(0,headroom.max()*1.05),xticks=np.arange(0,25,3),
          xlabel='Time / h',ylabel='Headroom / kW')
    return f


def main():
    import sys
    plt.rcParams.update({'font.family':'Times New Roman','font.size':12,'axes.unicode_minus':False})
    d=generate();(ROOT/'gallery/extra-data.json').write_text(json.dumps(d,separators=(',',':')),encoding='utf-8')
    selected=sys.argv[1:] or SLUGS
    if any(s not in SLUGS for s in selected):raise ValueError('Unknown chart family')
    for slug in selected:save(globals()[slug](d[slug]),slug);print('Python PNG:',slug,flush=True)


if __name__=='__main__':main()
