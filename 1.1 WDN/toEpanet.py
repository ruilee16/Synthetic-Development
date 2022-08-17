# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 11:56:49 2019

@author: sahmad20
"""

from datetime import datetime
start=datetime.now()
import networkx as nx
import wntr
import matplotlib.pyplot as plt
import pandas as pd
import geopy.distance
import math
import shutil
import os




def epa_1(cityname):
    dia=nx.read_graphml('%s_dia.graphml'%(cityname))
    #G=nx.read_graphml('diameter.graphml')


    span=nx.read_graphml(os.path.join(os.getcwd(),'data','%s_span.graphml'%(cityname)))

    
    wn = wntr.network.WaterNetworkModel()

    wdemand=nx.get_node_attributes(dia,'wDemand')

    wdemand_value=[float(v) for v in wdemand.values() if float(v)>0.0]

        
    for n in dia.nodes():
        
        
        if float(dia.node[n]['wDemand'])>0.0:


            wn.add_junction('%s'%(dia.node[n]['osmid']),
        base_demand=float(dia.node[n]['wDemand'])*3/30/24/60/15850.323141,
        elevation=float(dia.node[n]['elevation']),
        coordinates=(float(dia.node[n]['longitude']),
                     float(dia.node[n]['latitude'])))

        else:

            wn.add_junction('%s'%(dia.node[n]['osmid']),
        base_demand=min(wdemand_value)*3/30/24/60/15850.323141,
        elevation=float(dia.node[n]['elevation']),
        coordinates=(float(dia.node[n]['longitude']),
                     float(dia.node[n]['latitude'])))


        
            
        
        
    epa_edges=[]

    for ix,(e1,e2) in enumerate(list(dia.edges())):
        
        #print (ix+1,e1,e2,dia[e1][e2])
        
        wn.add_pipe('pipe_%s'%(ix+1), 
                    '%s'%(dia[e1][e2]['from_id']), 
                    '%s'%(dia[e1][e2]['to_id']), 
                    length=float(dia[e1][e2]['length']), 
                    diameter=float(dia[e1][e2]['dia(in)'])/39.37, 
                    roughness=int(dia[e1][e2]['roughness']),
                status='OPEN')
        
        epa_edges.append(['pipe_%s'%(ix+1),
                          '%s'%(dia[e1][e2]['from_id']), 
                    '%s'%(dia[e1][e2]['to_id']),
                    float(dia[e1][e2]['length']), 
                    float(dia[e1][e2]['dia(in)'])/39.37, 
                    int(dia[e1][e2]['roughness'])])
        
    df_edge=pd.DataFrame(epa_edges) 
    df_edge.columns=['n_ID','Node1','Node2','Length','Diameter','Roughness']
    #df_edge.to_csv('edges.csv',index=False)   



        
    max_dia=nx.get_edge_attributes(dia,'dia(in)')

    res_link_dia=max(max_dia.values())

    df_wtp=pd.read_csv('%s_treatmentPlant.csv'%(cityname))

    

    s_to_edge=[]

    for i in range(1,len(df_wtp.index)+1):
        
        wtp=(span.node['%s'%(i)]['y'],span.node['%s'%(i)]['x'])
        distance=[[j,geopy.distance.distance(wtp, 
                        (dia.node[j]['latitude'],
                         dia.node[j]['longitude'])).meters] for j in dia.nodes ]
        
        
        
        e_node=str(sorted(distance,key=lambda x:x[1])[0][0])
        dis=float(sorted(distance,key=lambda x:x[1])[0][1])
        #print ((str(i),e_node),dis)
        
        s_to_edge.append([str(i),e_node,dis])
        
    

    for edg in s_to_edge:
        
        print (edg[0],edg[1],edg[2])
        
        dia.add_edge(edg[0],edg[1],
                         len_flt=float(edg[2]))
        
    print (len(dia.edges),'pipes-%s'%(wn.num_pipes))    
     
    def source_trunk(source,target):
        
        all_paths=[(source,tg,nx.dijkstra_path_length(dia,source,tg,weight='len_flt')) for tg in target]
        
        all_paths_s=sorted(all_paths,key=lambda x:x[2])
        
        return all_paths_s[0] 
            
    df_bnodes=pd.read_csv('sPathToTrunk.csv')

    main_nodes=list(df_bnodes.target.unique())

    main_nodes=[str(n) for n in main_nodes]

    #print (dia['1']['609759617'])

    # for e1,e2 in list(dia.edges)[:2]:
        
    #     print (dia[e1][e2])
        
    max_dia=nx.get_edge_attributes(dia,'dia(in)')

    res_link_dia=max(max_dia.values())
        
    for i in range(1,len(df_wtp.index)+1):
        
        res=source_trunk('%s'%(i),main_nodes)
        
        print (res[0],res[1])
        
        wn.add_reservoir('%s'%(res[0]),
                base_head=float(span.node[res[0]]['elevation'])+50,
                coordinates=(round(dia.node[res[1]]['longitude'],3),
                     round(dia.node[res[1]]['latitude'],3)))
        
        
        dis=geopy.distance.geodesic((round(dia.node[res[1]]['latitude'],3),
                                        round(dia.node[res[1]]['longitude'],3)),
        (float(dia.node[res[1]]['latitude']),
         float(dia.node[res[1]]['longitude']))).meters
        
        wn.add_pipe('pipe_res_%s'%(res[0]), 
                    '%s'%(res[0]), 
                    '%s'%(res[1]),
                     length=dis,
                     roughness=150,
                     diameter=float(res_link_dia)/39.37,
                     status='CV')
        
    

    wn.write_inpfile('%s.inp'%(cityname))

    print ('nodes-%s'%(wn.num_junctions),'pipes-%s'%(wn.num_pipes),
           'pumps-%s'%(wn.num_pumps),'reservoir-%s'%(wn.num_reservoirs))

#print (res_link_dia)

#epa_1('mesa')
