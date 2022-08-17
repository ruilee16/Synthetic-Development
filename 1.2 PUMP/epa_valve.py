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
import pickle
import numpy as np



def epa_2(cityname):

    G=nx.read_graphml('%s_dia.graphml'%(cityname))
    #wgs84=pyproj.Proj("+init=EPSG:4326")
    #merc=pyproj.Proj("+init=EPSG:3857")
    #
    #
    #for n in G.nodes():
    #    
    #    x,y =pyproj.transform(wgs84, merc, G.node[n]['x'], G.node[n]['y'])
    #    G.node[n]['merc_x']=x
    #    G.node[n]['merc_y']=y

    print (G.nodes[list(G.nodes())[4]])
        
    def set_pos(G):
        pos=[[i,(float(G.nodes[i]['longitude']),float(G.nodes[i]['latitude']))] for i in G.nodes]
        nx.set_node_attributes(G,dict(pos),'pos')
        
    set_pos(G)
    wn = wntr.network.WaterNetworkModel('%s.inp'%(cityname))

    print ('nodes-%s'%(wn.num_junctions),'pipes-%s'%(wn.num_pipes),
           'pumps-%s'%(wn.num_pumps),'reservoir-%s'%(wn.num_reservoirs))

    #print (res_link_dia)

    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()

    pressure = results.node['pressure']
    demand=results.node['demand']
    flow=results.link['flowrate']


    print (max(pressure.iloc[0,:]),
           min(pressure.iloc[0,:]),
           sorted(pressure.iloc[0,:])[:20])



    G_e=wn.get_graph()

    flow_direction={}

    for e1,e2 in list(G_e.edges()):
        
        pipe=list(G_e[e1][e2])[0]
        
        if float(flow.loc[:,'%s'%(pipe)])>0:
            
            flow_direction[(e1,e2)]=[abs(float(flow.loc[:,'%s'%(pipe)])),pipe]
        else:
            flow_direction[(e2,e1)]=[abs(float(flow.loc[:,'%s'%(pipe)])),pipe]
            
    G_flow=nx.DiGraph()

    G_flow.add_edges_from(list(flow_direction.keys()))

    print (nx.number_of_nodes(G_e),nx.number_of_nodes(G_flow),
           nx.number_of_edges(G_e),nx.number_of_edges(G_flow))


    for e1,e2 in G_flow.edges():
        
        G_flow[e1][e2]['flow']=flow_direction[(e1,e2)][0]
        G_flow[e1][e2]['pipe_name']=flow_direction[(e1,e2)][1]


    for (e1,e2) in list(G_flow.edges())[:3]:

        print (G_flow[e1][e2])

    nx.write_graphml(G_flow,'flow_%s.graphml'%(cityname))
        
    for n in G_flow.nodes():
        
       
        G_flow.nodes[n]['h_loss_psi']=float(pressure.loc[:,'%s'%(n)])
        G_flow.nodes[n]['demand']=float(demand.loc[:,'%s'%(n)])


    
        
        try:
        
            G_flow.nodes[n]['pos']=G.node[n]['pos']
        except:
            continue



    print (min(nx.get_edge_attributes(G_flow,'flow').values()))

    

    for (e1,e2) in list(G_flow.edges())[:2]:

        print (G_flow[e1][e2])



    reservoirs=[str(r+1) for r in range(wn.num_reservoirs)]

    lp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])<30 and\
               n not in reservoirs]
    hp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])>70]
    track_lp_nodes=[len(lp_nodes)]
    pumps=[]
    wn_pumps=[]
    print (len(lp_nodes),len(hp_nodes))

    it=1

    valve_node=[]
    valve_number=[]

    for r in reservoirs:
        valve_node.append(r)

    while len(hp_nodes)>10:

        root_node={}

        for hp in hp_nodes:

            r_tree=list(nx.bfs_tree(G_flow,hp,reverse=True))

            for ix,n in enumerate(r_tree):

                if float(pressure.loc[:,'%s'%(n)])<70:
                    try:
                        root_node[n].append(hp)
                        break
                    except:
                        root_node[n]=[hp]
                        break

                
        print ('root_node_hp',len(root_node.keys()))

        root_node_l=[]

        for rn in root_node.keys():

            fn_tree=list(nx.bfs_tree(G_flow,rn))

            #print (rn,fn_tree[:5])

            root_node_l.append([rn,len(root_node[rn]),
                len(set.intersection(set(fn_tree[1:]),set(root_node.keys())))])

            
        #print (root_node_l)

        df_root=pd.DataFrame(root_node_l)
        df_root.columns=['rn','f_nodes','u_node']
        #df_root=df_root[df_root.f_nodes>10]

        df_root=df_root.sort_values(by=['u_node','f_nodes'],ascending=[False, False])
        #df_root=df_root.sort_values(by=['f_nodes'],ascending=[False])

        #print (df_root.head(),df_root.tail())
        #print (df_root.head())
        #print (df_root.a_nodes)


        for i in df_root.index:

            #print (df_root['rn'][i],list(G_flow.out_edges(df_root['rn'][i])))

            out_edges=[]

            for (e1,e2) in list(G_flow.out_edges(df_root['rn'][i])):

                if float(pressure.loc[:,'%s'%(e2)])>70:

                    out_edges.append([e1,e2,
                len(set.intersection(set(list(nx.bfs_tree(G_flow,e2))[1:]),
                    set(root_node[df_root['rn'][i]])))])

            out_edges=sorted(out_edges,key=lambda x:x[2],reverse=True)

            #print (out_edges)

            for [e3,e4,l] in out_edges:

                #print (e3,e4)

                if set.intersection(set([e3,e4]),set(valve_node))==set():
                    wn.remove_link('%s'%(G_flow[e3][e4]['pipe_name']))

                    wn.add_valve('valve_%s'%(e4),'%s'%(e3),
                        '%s'%(e4),diameter=0.3048, valve_type='PRV',setting=65)

                    valve_node.extend([e3,e4])

                    wn.write_inpfile('%s_valve.inp'%(cityname))

                    sim = wntr.sim.EpanetSimulator(wn)
                    results = sim.run_sim()
                    pressure = results.node['pressure']
                    hp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])>70]
                    print (len(hp_nodes))

        
        hp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])>70]
        valve_number.append(wn.num_valves)
        try:
            if valve_number[-1]==valve_number[-2]:
                print (it,'valves-%s'%(wn.num_valves),len(hp_nodes)) 
                break
        except:
            it+=1
            continue
        print ('valves-%s'%(wn.num_valves),len(hp_nodes))
    wn.write_inpfile('%s_valve.inp'%(cityname))





# epa_2('phx')

# print ('Total time taken : %s'%(datetime.now()-start))




    







    
        


