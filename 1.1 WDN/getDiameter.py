# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 15:36:24 2019

@author: sahmad20
"""
# from datetime import datetime
# start=datetime.now()
import networkx as nx
import pandas as pd
import geopy.distance
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import math
import shutil
import os


def flow(cityname):
    df_paths=pd.read_csv('paths.csv',header=None)
    G_orig=nx.read_graphml(os.path.join(os.getcwd(),'data','%s_drive.graphml'%(cityname)))
    df_wtp=pd.read_csv('%s_treatmentPlant.csv'%(cityname))

    #print (G_orig.node['1'])



    pos=[[i,(float(G_orig.node[i]['x']),float(G_orig.node[i]['y']))] for i in G_orig.nodes]
    nx.set_node_attributes(G_orig,dict(pos),'pos')


    paths=[]
    for j in range(len(df_paths.index)):
        df_1=df_paths.iloc[j,:]
        df_1=df_1.dropna()
        path_1=[]
        
        for i in df_1:
            
            path_1.append(str(i)[:-2])
        paths.append(path_1)
        
        



    waterMain=paths[0][1:]
    #print (waterMain,len(waterMain))

    '''
    head loss (psi)= 4.52*Q^1.852*L/C^1.852/d^4.8704
    Q in gallons per minute
    L in feet
    C= roughness coefficient (for PVC is 150)
    d (dia) in inches
    applied eqn= 4.52*L*3.28(1m=3.28ft)*5ft/s*3.14(pi)*d^2*7.48(1ft^3=7.48gallon)*60 (1m=60s)/
    150^1.852/d^4.87/4/12^2(1ft=12inch)
    '''
    d=60.0
    q=(5*3.14*d**2*7.48*60/4/12**2)
    hl_per_m=4.52*3.28*q**1.852/150**1.852/d**4.87
    #print (q,hl_per_m)

    for e1,e2 in G_orig.edges:
        
        
        G_orig[e1][e2]['hl_psi_init']=hl_per_m*float(G_orig[e1][e2]['length'])
        G_orig[e1][e2]['len_flt']=float(G_orig[e1][e2]['length'])


    def target_trunk(source,target):
        
        all_paths=[(source,tg,nx.dijkstra_path_length(G_orig,source,
                                                      tg,weight='len_flt')) for tg in target]
        
        all_paths_s=sorted(all_paths,key=lambda x:x[2])
        
        return all_paths_s[0]

    wtp={}

    for n in waterMain:
        
        
        
        wtp[n]=sorted([(i,nx.dijkstra_path_length(G_orig,str(i),
           n,weight='hl_psi_init')) for i in range(1,len(df_wtp.index)+1)],key=lambda x:x[1])[0][0]
        
         

    print (len(waterMain),len([v for v in wtp.values() if v==1]),len(waterMain)-\
           len([v for v in wtp.values() if v==1]))


    wTp=list(set(list(wtp.values())))

    print ('wTP',wTp)
    wm_edges=[]
    entry_points=[]

    sub_graph=[]

    for w in wTp:
        
        #print (target_trunk(str(w),waterMain))
        entry_pt=target_trunk(str(w),waterMain)[1]
        #print (w,entry_pt)
        sub_graph.append(nx.dijkstra_path(G_orig,str(w),str(entry_pt)))
        entry_points.append(entry_pt)
        w_nodes=[k for k in wtp.keys() if wtp[k]==w]
        #print (len(w_nodes))
        
        
        
        entry_pt_index=waterMain.index(entry_pt)
        
        w_nodes_index=[waterMain.index(n) for n in w_nodes]
        
        sp=min(w_nodes_index)
        fp=max(w_nodes_index)

        
        
        for i in range(entry_pt_index,sp,-1):
            
            wm_edges.append((waterMain[i],waterMain[i-1]))
            
        for i in range(entry_pt_index,fp):
            
            wm_edges.append((waterMain[i],waterMain[i+1]))
        
    print ('entry_points',entry_points)

    df_sub=pd.DataFrame(sub_graph)
    df_sub.to_csv('entry_points.csv',index=False)

    # fig_wtp=plt.figure(figsize=(9,13.5))
    # ax=fig_wtp.add_subplot(111)
    #ax.autoscale(enable=True)
    # nx.draw(G_orig,nx.get_node_attributes(G_orig,'pos'),alpha=0.0)
    # nx.draw_networkx_edges(G_orig,nx.get_node_attributes(G_orig,'pos'),
    #                        width=0.5,edge_color='gray')

    # for s in sub_graph:
        
    #     G_sub=nx.subgraph(G_orig,s)
    #     nx.draw_networkx_edges(G_sub,nx.get_node_attributes(G_sub,'pos'),
    #                        width=2.0,edge_color='red')
        
    #fig_wtp.savefig('wtp_connect.pdf')
        
    # create a balnk directed graph for simple flow analysis

    G=nx.DiGraph() 

    G.add_edges_from(wm_edges)


    c_points=[]

    # connect WTP zones

    for ix,n in enumerate(waterMain):
        
        if ix not in [0,len(waterMain)-1] and G.out_degree(str(n))==0:
            
            c_points.append((str(n),waterMain.index(n)))
    print ('c_points',c_points)

    for i in range(0,len(c_points),2):
        
        if float(G_orig.node[c_points[i][0]]['elevation'])>float(G_orig.node[c_points[i+1][0]]['elevation']):
            
            G.add_edge(c_points[i][0],c_points[i+1][0])
            
        else:
            
            G.add_edge(c_points[i+1][0],c_points[i][0])
            
            
    for ix,ep in enumerate(entry_points):
        
        G.add_node('wtp_%s'%(wTp[ix]),demand=0.0)
        
        G.add_edge('wtp_%s'%(wTp[ix]),ep)
        
        #print (G['wtp_%s'%(wTp[ix])])
        
        
    for n in waterMain:
        
        #print (wtp[n],G_orig.node[str(n)])
        
        G.node[n]['demand']=round(float(G_orig.node[n]['wDemand']))
        
        G.node['wtp_%s'%(wtp[n])]['demand']+=-1*G.node[n]['demand']
        
        #print (G.node[n],G.node['wtp_%s'%(wtp[n])])
        
        
        
        #print (flowDict)
        
    df_trunk=pd.read_csv('sPathToTrunk.csv')



    for p in range(1,len(paths)):   
        wm_edges_2=[]
        
        path_2=paths[p][1:]
     
        for ix,n in enumerate(path_2):
            try:
                wm_edges_2.append((path_2[ix+1],n))
            except:
                continue
        
        G.add_edges_from(wm_edges_2)
        

    #    
    #    




    for ix,n in enumerate(list(df_trunk.source)):
        
        #print (n, df_trunk.target.iloc[ix],wtp[str(df_trunk.target.iloc[ix])])
        
        
        G.node[str(n)]['demand']=round(float(G_orig.node[str(n)]['wDemand']))
        
        G.node['wtp_%s'%(wtp[str(df_trunk.target.iloc[ix])])]['demand']+=-1*G.node[str(n)]['demand']
        
       


           
            
    d_total=0

    for n in G.nodes:
        
        try:
            d_total+=G.node[n]['demand']
            #print (n,G.node[n]['demand'])
        except:
            continue
        

    print ('total',d_total)

    flowCost, flowDict=nx.network_simplex(G)



    # for w in wTp:
        
    #     print (flowDict['wtp_%s'%(w)]) 

    for i in wTp:
        
    #    print (list(flowDict['wtp_%s'%(i)].keys())[0],
    #           G_orig.node['%s'%(list(flowDict['wtp_%s'%(i)].keys())[0])])
        
        for k in flowDict['wtp_%s'%(i)].keys():
            
            G_orig.node['%s'%(k)]['demand (gallons per minute)']=float(flowDict['wtp_%s'%(i)][k])*\
            2.47/30/24/60
            
            
            #print (G_orig.node['%s'%(k)])
        
        

    G.remove_nodes_from(['wtp_%s'%(wp) for wp in wTp])

    for n in list(G.nodes):
        
        if flowDict[n]!={}:
        
            
            
            flow=flowDict[n]
            
            for k in flow.keys():
                
                try:
                    d=(float(flow[k])*0.0038*2*4/30/24/60/60/1.524/3.14)**(1/2)*39.37
                    G_orig[n][k]['dia(in)']=math.ceil(d)
                    
                    G_orig[n][k]['gpm']=float(flow[k])*2/30/24/60
                    
                except:
                    continue
                
                #print (n,k,flow[k],G_orig[n][k])

    min_dia=6.0
             
    for e1,e2 in G_orig.edges:
        
        
        try:
            
            G_orig[e1][e2]['dia(in)']+=0.0
            
        except:
            
            G_orig[e1][e2]['dia(in)']=min_dia
        
    for e1,e2 in G_orig.edges:
        
        if G_orig[e1][e2]['dia(in)']<min_dia:
            
            G_orig[e1][e2]['dia(in)']=min_dia
            
    min_flow=5*3.14*7.48*60*math.pow((min_dia/12.0),2)/4.0

    print (min_flow)

    for e1,e2 in G_orig.edges:
        
        
        try:
            
            G_orig[e1][e2]['gpm']+=0.0
            
        except:
            
            G_orig[e1][e2]['gpm']=min_flow         
       
    for e1,e2 in G_orig.edges:
        
        if G_orig[e1][e2]['gpm']<min_flow:
            
            G_orig[e1][e2]['gpm']=min_flow       
        

               
    dia=nx.get_edge_attributes(G_orig,'dia(in)')

    
    gpm=nx.get_edge_attributes(G_orig,'gpm')


    trt_plant=[str(w) for w in range(1,len(df_wtp.index)+1)]

    G_orig.remove_nodes_from(trt_plant)


        
            
        
    dia=[i[2]/20 for i in G_orig.edges(data='dia(in)')]

    for ix,(e1,e2) in enumerate(G_orig.edges):
        
        G_orig[e1][e2]['Weight']=dia[ix]
        

    df_dia=pd.DataFrame(dia)
    df_dia['pct']=df_dia.rank(pct=True)


    labels=np.linspace(0,1,num=7)
    print (len(labels))
    df_dia['group'] = pd.cut(df_dia.pct, np.linspace(0,1,num=8), right=False, labels=labels)

    #print (df_dia.head())

    cmap=matplotlib.cm.get_cmap('plasma_r')
    #norm = matplotlib.colors.Normalize(vmin=1, vmax=7)

    #print (matplotlib.cm.plasma(norm(4),bytes=True))

    color=[cmap(i) for i in df_dia['group'] ]

    


    for e1,e2 in G_orig.edges:
        
        G_orig[e1][e2]['flow rate (gallons per minute)']=G_orig[e1][e2]['gpm']
        G_orig[e1][e2]['from_id']=e1
        G_orig[e1][e2]['to_id']=e2
        G_orig[e1][e2]['velocity (ft/s)']=5.0
        G_orig[e1][e2]['roughness']=150

    for n in G_orig.nodes:
        
        try:
            
            G_orig.node[n]['longitude']=float(G_orig.node[n]['x'])
            G_orig.node[n]['latitude']=float(G_orig.node[n]['y'])
        except:
            G_orig.node[n]['longitude']=float(G_orig.node[n]['pos'][0])
            G_orig.node[n]['latitude']=float(G_orig.node[n]['pos'][1])
            
            
    G.remove_nodes_from(['wtp_%s'%(wp) for wp in range(1,3)]) 
    print (len(G.nodes),len(G_orig.nodes))
    for n in G.nodes:
        
        G.node[n]['pos']=G_orig.node[n]['pos']
        G.node[n]['x']=G_orig.node[n]['x']
        G.node[n]['y']=G_orig.node[n]['y']
             
            

        
    keys_del=['y', 'x', 'D_1', 'D_2', 'wtp', 'net_2', 'net_1', 'pos']

    for n in G_orig.nodes:
        
        for att in keys_del:
            
            try:
        
                G_orig.node[n].pop(att)
            except:
                continue
            

    for n in list(G_orig.nodes):
        
        
        try:
            
            G_orig.node[n]['demand (gallons per minute)']+=sum([G_orig[e1][e2]['gpm'] for (e1,e2) in G.in_edges(n)])
            
        except:
            
            G_orig.node[n]['demand (gallons per minute)']=sum([G_orig[e1][e2]['gpm'] for (e1,e2) in G.in_edges(n)])
        
       
        


    #print (G_orig.node[2])   

    nx.write_graphml(G_orig,'%s_dia.graphml'%(cityname))


    
    #print ('Total time taken : %s'%(datetime.now()-start))