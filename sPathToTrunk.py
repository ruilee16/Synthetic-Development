# -*- coding: utf-8 -*-
"""
Created on Tue Oct 30 15:34:52 2018

@author: sahmad20
"""

# from datetime import datetime
# start=datetime.now()
#from keys import google_elevation_api_key
import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn
import os
import pandas as pd
import geopy.distance
from operator import itemgetter as ig
import itertools as it





def pathToTrunk(c_name):
    
    cityname=c_name
    
    df_wtp=pd.read_csv('%s_treatmentPlant.csv'%(cityname))

    T=nx.read_graphml(os.path.join(os.getcwd(),'data','%s_drive.graphml'%(cityname)))
    trt_plant=[str(w) for w in range(1,len(df_wtp.index)+1)]
    
    T_wtp=nx.subgraph(T,trt_plant)


    T.remove_nodes_from(trt_plant)
    
    pos=[[i,(float(T.node[i]['x']),float(T.node[i]['y']))] for i in T.nodes]
    nx.set_node_attributes(T,dict(pos),'pos')

    
    
    
    for e1,e2,data in T.edges(data='length'):
        T[e1][e2]['len_flt']=float(data)

    
        
    from perinode import perinode
    peri_nodes=perinode(cityname)
    
    df_peri_nodes=pd.DataFrame(peri_nodes)
    df_peri_nodes.to_csv('peri_nodes.csv',index=False)
    
    
    
    paths=[]
    path_11=nx.dijkstra_path(T,peri_nodes[0],peri_nodes[1],weight='len_flt')
    path_11[0:0]=[0]
    paths.append(path_11)
    
    
    pos=[[i,(float(T.node[i]['x']),float(T.node[i]['y']))] for i in T.nodes]
    nx.set_node_attributes(T,dict(pos),'pos')
    
    T_sub=nx.subgraph(T,path_11)
    
    
    
    
    all_nodes=list(T_sub.nodes())
    
    
    
    rem_nodes=list(set(T.nodes)-set(paths[0][1:]))
    
        
    #len_path = nx.all_pairs_dijkstra_path_length(T,weight='len_flt')
    len_path = nx.all_pairs_dijkstra_path_length(T)
    
    #print (len_path,type(next(len_path)[1]))
    target=paths[0][1:]
    print (len(T.nodes),len(target),len(T.nodes)-len(target))
    
    sPathToTrunk=[]
    for i in range(len(T.nodes)):
        if i%500==0:
            print ('%s---%s'%(i+1,len(T.nodes)))
        init_list=next(len_path)
        mydict=init_list[1]
        mylist=sorted([(k,mydict[k]) for k in target],key=lambda x:x[1])
        
        
        sPathToTrunk.append([init_list[0],mylist[0][0],mylist[0][1]])
        
    
    #
    df=pd.DataFrame(sPathToTrunk)
    df.columns=['source','target','length']
    df=df[df['source'].isin(rem_nodes)]
    df=df.sort_values(by='length',ascending=False)
    
    print (len(df.source),len(rem_nodes))
    
    #
    df.to_csv('sPathToTrunk.csv',index=False)
    #
    #
    #



# pathToTrunk('tempe')
# print ('Total time taken : %s'%(datetime.now()-start))










