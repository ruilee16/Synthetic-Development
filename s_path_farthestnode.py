# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 10:11:16 2019

@author: sahmad20
"""

import pandas as pd
import networkx as nx
import os 

def path(c_name):

    cityname=c_name
    
    df_wtp=pd.read_csv('%s_treatmentPlant.csv'%(cityname))

    T=nx.read_graphml(os.path.join(os.getcwd(),'data','%s_drive.graphml'%(cityname)))
    trt_plant=[str(w) for w in range(1,len(df_wtp.index)+1)]


    T.remove_nodes_from(trt_plant)
    pos=[[i,(float(T.node[i]['x']),float(T.node[i]['y']))] for i in T.nodes]
    nx.set_node_attributes(T,dict(pos),'pos')
    #
    for e1,e2,data in T.edges(data='length'):
        T[e1][e2]['len_flt']=float(data)
    #    
    #peri_nodes=nx.algorithms.distance_measures.extrema_bounding(T,compute="periphery")
    
    df_peri_nodes=pd.read_csv('peri_nodes.csv',header=None)

    
    paths=[]
    path_11=nx.dijkstra_path(T,str(df_peri_nodes.iloc[1,0]),
                             str(df_peri_nodes.iloc[2,0]),weight='len_flt')
    all_ass_nodes=[]
    all_ass_nodes.extend(path_11)
    path_11[0:0]=[0]
    paths.append(path_11)
    
    
    
    
    
    
    
    dfTrunk=pd.read_csv('sPathToTrunk.csv')
    
    
    
    
    
    
    for j in range(len(dfTrunk['target'].unique())):
    #for j in range(5):
        
        #print ('main line - %s_%s'%(j+1,len(dfTrunk['target'].unique())))
        tn=dfTrunk['target'].unique()[j]
        df1=dfTrunk[dfTrunk.target==tn]
        ass_nodes=[]
        
        sub_nodes=list(df1.source)
        sub_nodes.append(tn)
        sub_nodes=[str(n) for n in sub_nodes]
        T_sub=nx.subgraph(T,sub_nodes)
        #len_path = dict(nx.all_pairs_dijkstra_path_length(T_sub,weight='len_flt'))
        len_path = dict(nx.all_pairs_dijkstra_path_length(T_sub))
        
        
        
        
        def target_trunk(s,target):
            
            s=str(s)
            
            
            mydict=len_path[s]
            mylist=sorted([(k,mydict[k]) for k in target],key=lambda x:x[1])
            return (s,mylist[0][0],mylist[0][1])
        
        p_serial=1
        
        for i in range(len(df1.source)):
            #path1=nx.dijkstra_path(T,str(df1.source.iloc[i]),str(tn),weight='len_flt')
            path1=nx.dijkstra_path(T,str(df1.source.iloc[i]),str(tn))
            if set.intersection(set(all_ass_nodes),set(path1[:-1]))==set():
                
            
                ass_nodes.extend(path1[:-1])
                all_ass_nodes.extend(path1[:-1])
                path1[0:0]=[p_serial]
                
                paths.append(path1)
                
                print ('%s_%s--%s--%s--%s--%s--%s'%(j+1,len(dfTrunk['target'].unique()),
                            p_serial,len(T.nodes),len(all_ass_nodes),
                                             len(T_sub),len(ass_nodes)))
                
    #            print ('sub line - %s\n'%(p_serial),
    #                   'total nodes-%s'%(len(T.nodes)),'all assigned nodes- %s\n'%(len(all_ass_nodes)),
    #                   'sub nodes -%s'%(len(T_sub)),
    #                   'assigned sub nodes- %s'%(len(ass_nodes)))
        p_serial+=1
        rem_nodes=[n for n in df1.source if str(n) not in ass_nodes]
        while len(rem_nodes)>0:
        
            
            
            rem_list=sorted([target_trunk(s,ass_nodes) for s in rem_nodes],
                             key=lambda x: x[2],reverse=True)
            
            
            for rm in rem_list:
                #path2=nx.dijkstra_path(T_sub,rm[0],rm[1],weight='len_flt')
                path2=nx.dijkstra_path(T_sub,rm[0],rm[1])
                if set.intersection(set(all_ass_nodes),set(path2[:-1]))==set():
                    ass_nodes.extend(path2[:-1])
                    all_ass_nodes.extend(path2[:-1])
                    path2[0:0]=[p_serial]
                    
                    paths.append(path2)
            print ('%s_%s--%s--%s--%s--%s--%s'%(j+1,len(dfTrunk['target'].unique()),
                            p_serial,len(T.nodes),len(all_ass_nodes),
                                             len(T_sub),len(ass_nodes)))
            rem_nodes=[n for n in df1.source if str(n) not in ass_nodes]
            p_serial+=1
    print ('No of Pipes- %s'%(len(paths)))
    df_paths=pd.DataFrame(paths)
    df_paths.to_csv('paths.csv',header=False,index=False)


#path('tempe')



