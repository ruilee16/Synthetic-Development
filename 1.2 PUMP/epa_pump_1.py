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

    wn = wntr.network.WaterNetworkModel('%s_valve.inp'%(cityname))

    print ('nodes-%s'%(wn.num_junctions),'pipes-%s'%(wn.num_pipes),
           'pumps-%s'%(wn.num_pumps),'reservoir-%s'%(wn.num_reservoirs),
           'valves-%s'%(wn.num_valves))

    #print (res_link_dia)

    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()

    pressure = results.node['pressure']
    demand=results.node['demand']
    flow=results.link['flowrate']


    print (max(pressure.iloc[0,:]),
           min(pressure.iloc[0,:]),
           sorted(pressure.iloc[0,:])[:20])


    G_flow=nx.read_graphml('flow_%s.graphml'%(cityname))


        
    for n in G_flow.nodes():
        
       
        G_flow.nodes[n]['h_loss_psi']=float(pressure.loc[:,'%s'%(n)])
        G_flow.nodes[n]['demand']=float(demand.loc[:,'%s'%(n)])        
        try:
        
            G_flow.nodes[n]['pos']=G_flow.nodes[n]['pos']
        except:
            continue



    print (min(nx.get_edge_attributes(G_flow,'flow').values()))

    

    for (e1,e2) in list(G_flow.edges())[:2]:

        print (G_flow[e1][e2])



    reservoirs=[str(r+1) for r in range(wn.num_reservoirs)]

    lp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])<30 and\
               n not in reservoirs]
    hp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])>70]
    # track_lp_nodes=[len(lp_nodes)]
    # pumps=[]
    # wn_pumps=[]
    print (len(lp_nodes),len(hp_nodes))

    valve_node=[]
    for r in reservoirs:
        valve_node.append(r)

    for v_name, valve in wn.valves():

        valve_node.append(str(valve.start_node))
        valve_node.append(str(valve.end_node))

    print (valve_node,len(valve_node))

    it=1

    pump_details=[]

    pump_number=[]

    while len(lp_nodes)>100:

        root_node={}

        for lp in lp_nodes:

            r_tree=list(nx.bfs_tree(G_flow,lp,reverse=True))

            for ix,n in enumerate(r_tree):

                if float(pressure.loc[:,'%s'%(n)])>30:
                    try:
                        root_node[n].append(lp)
                        break
                    except:
                        root_node[n]=[lp]
                        break

                
        print ('root_node_lp',len(root_node.keys()))

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
        print (df_root.head())
        #print (df_root.a_nodes)


        for i in df_root.index:

            #print (df_root['rn'][i],list(G_flow.out_edges(df_root['rn'][i])))

            out_edges=[]

            for (e1,e2) in list(G_flow.out_edges(df_root['rn'][i])):

                if float(pressure.loc[:,'%s'%(e2)])<30:

                    out_edges.append([e1,e2,
                len(set.intersection(set(list(nx.bfs_tree(G_flow,e2))[1:]),
                    set(root_node[df_root['rn'][i]])))])

            out_edges=sorted(out_edges,key=lambda x:x[2],reverse=True)

            #print (out_edges)

            # min_head=min([float(pressure.loc[:,'%s'%(n1)]) for n1 in root_node[df_root['rn'][i]]])
            # print (df_root['rn'][i],out_edges,float(pressure.loc[:,'%s'%(n1)]))

            lp_node_p=len(lp_nodes)

            for [e3,e4,l] in out_edges:

                min_head=float(pressure.loc[:,'%s'%(e4)])

                print (min_head)

                if set.intersection(set([e3,e4]),set(valve_node))==set() and min_head<35:
                    p_name=G_flow[e3][e4]['pipe_name']
                    length=wn.get_link(p_name).length
                    dia=wn.get_link(p_name).diameter


                    wn.remove_link('%s'%(G_flow[e3][e4]['pipe_name']))
                    wn.add_curve('curve_%s'%(e4),'HEAD',[(G_flow[e3][e4]['flow']*3,
                                 35-min_head)])

                    wn.add_pump('pump_%s'%(e4),
                                                '%s'%(e3),
                                                '%s'%(e4),
                                                pump_type='HEAD',
                                                pump_parameter='curve_%s'%(e4))

                    valve_node.extend([e3,e4])

                    wn.write_inpfile('%s_pump_1.inp'%(cityname))

                    sim = wntr.sim.EpanetSimulator(wn)
                    results = sim.run_sim()
                    pressure = results.node['pressure']


                    lp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])<30 and\
                            n not in reservoirs]
                    if (lp_node_p-len(lp_nodes))>9:
                        print (it,lp_node_p,len(lp_nodes),min_head,float(pressure.loc[:,'%s'%(e4)]),
                            'pipes-%s'%(wn.num_pipes),'pumps-%s'%(wn.num_pumps))

                        f=1

                        while float(pressure.loc[:,'%s'%(e4)])<60:

                            #print (wn.get_curve('curve_%s'%(e4)).points)

                            c_flow=wn.get_curve('curve_%s'%(e4)).points[0][0]
                            c_head=wn.get_curve('curve_%s'%(e4)).points[0][1]
                            wn.get_curve('curve_%s'%(e4)).points=[(c_flow+0.006,c_head+1)]

                            wn.write_inpfile('%s_pump_1.inp'%(cityname))

                            lp_node_p=len(lp_nodes)

                            sim = wntr.sim.EpanetSimulator(wn)
                            results = sim.run_sim()
                            pressure = results.node['pressure']
                            lp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])<30 and\
                            n not in reservoirs]

                            if len(lp_nodes)<lp_node_p:

                                print (f,len(lp_nodes),float(pressure.loc[:,'%s'%(e4)]))
                                f+=1
                            else:
                                wn.get_curve('curve_%s'%(e4)).points=[(c_flow,c_head)]
                                break




                        pump_details.append([it,e3,e4,wn.get_curve('curve_%s'%(e4)).points[0][0],
                            wn.get_curve('curve_%s'%(e4)).points[0][1],lp_node_p,len(lp_nodes)])
                        print (len(lp_nodes))
                    else:
                        wn.remove_link('pump_%s'%(e4))
                        wn.remove_curve('curve_%s'%(e4))
                        wn.add_pipe(p_name, 
                            '%s'%(e3), 
                            '%s'%(e4), 
                            length=length, 
                            diameter=dia, 
                            roughness=150.0,
                            status='OPEN')

                        sim = wntr.sim.EpanetSimulator(wn)
                        results = sim.run_sim()
                        pressure = results.node['pressure']
                        lp_nodes=[n for n in G_flow.nodes() if float(pressure.loc[:,'%s'%(n)])<30 and\
                            n not in reservoirs]
                        print ('pump_removed, pipes-%s,pumps-%s'%(wn.num_pipes,
                            wn.num_pumps),len(lp_nodes))


        
        pump_number.append(wn.num_pumps)
        try:
            if pump_number[-1]==pump_number[-2]:
                print ('pump_removed, pipes-%s,pumps-%s'%(wn.num_pipes,
                                wn.num_pumps),len(lp_nodes)) 
                break
        except:
            it+=1
            continue
        
        

    df_pump=pd.DataFrame(pump_details,columns = range(7))
    print(df_pump)
    df_pump.columns=['itr','st_node','end_node','flow','head','lp_previous','lp_after']
    df_pump.to_csv('pump.csv',index=False)

                







    
        


