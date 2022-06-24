from datetime import datetime
start=datetime.now()
#from keys import google_elevation_api_key
import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn
import os
import pandas as pd
import geopy.distance
from operator import itemgetter
import shutil


def data():


    cityname=input('enter city name -')
    state=input('enter state name -')

    n_nodes_edges=[]

    # prepare water demand file downloaded from eRAMS/IUWM
    print(os.path.join(os.path.join(os.getcwd(),'IUWM_%s'%(cityname),
                                             'demand_%s.csv'%(cityname))))
    df=pd.read_csv(os.path.join(os.path.join(os.getcwd(),'IUWM_%s'%(cityname),'demand_%s.csv'%(cityname))))

    geoid=list(df['geoid'].unique())

    print (df.head())
    print (geoid[:10])


    total=[]

    for i in geoid:
        df_1=df.loc[df['geoid'] == i]
        df_1=df_1.sort_values(by='total_use', ascending=False)

        total.append(['0%s'%(df_1['geoid'].iloc[0]),'S0%s'%(df_1['geoid'].iloc[0]),
                      df_1['total_use'].iloc[0]])
    df_total=pd.DataFrame(total)
    df_total.columns=['GEOID10','geoid_s','demand']
    df_total['GEOID10']=df_total['GEOID10'].astype('str')

    df_total.to_csv('total_%s.csv'%(cityname),index=False)

    wd_shp=gpd.read_file(os.path.join(os.getcwd(),'IUWM_%s'%(cityname),
                                      '%s Census Block Group.dbf'%(cityname)))





    wd_shp['geoid_s']=wd_shp.apply(lambda x:'S%s'%(x['GEOID10']), axis=1)

    final_shp=wd_shp.merge(df_total,on='geoid_s')

    print (len(final_shp['geoid_s']))


    final_shp=final_shp.to_crs({'init': 'epsg:4326'})


    

    try:
        os.mkdir('wDemandIUWM_%s'%(cityname))
    except:
        shutil.rmtree('wDemandIUWM_%s'%(cityname))
        os.mkdir('wDemandIUWM_%s'%(cityname))

    path=os.path.join(os.getcwd(),'wDemandIUWM_%s'%(cityname))

    final_shp.to_file(os.path.join(path,'%s_waterDemand.shp'%(cityname)))

    print ('IUWM done')
    # get the graph

    #print (final_shp.columns)

    place_names = ['%s, %s, USA'%(cityname,state)]
    #place_names=['Tempe, Arizona, USA']

    orig_graph=[]
    drive_graph=[]
    for p in place_names:

        # G_drive=ox.graph_from_place(p, clean_periphery=False,
        #                          network_type='drive',simplify=True)

        wd_dis=gpd.read_file(os.path.join(os.getcwd(),'input_shp','%s.shp'%(cityname)))



        G_drive= ox.graph_from_polygon(wd_dis.geometry.iloc[0],
                               network_type='drive',simplify=True)
        
        
        print ('download done','nodes-%s'%(len(G_drive.nodes)),
               'edges-%s'%(len(G_drive.edges)),'time taken : %s'%(datetime.now()-start))

        df_wtp=pd.read_csv('%s_treatmentPlant.csv'%(cityname))
        for i in range(len(df_wtp.index)):
            G_drive.add_node(i+1, y=df_wtp['y'][i], x= df_wtp['x'][i],
                       osmid=i+1)
        
        



        # connect WTP to the network
        for i in range(1,len(df_wtp.index)+1):
            
            wtp=(df_wtp.iloc[i-1][1],df_wtp.iloc[i-1][2])
            distance=[[j,geopy.distance.vincenty(wtp, 
                            (G_drive.node[j]['y'],
                             G_drive.node[j]['x'])).meters] for j in G_drive.nodes ]
            
            #print (i,dict(distance[:5]))
            nx.set_node_attributes(G_drive,dict(distance),'D_%s'%(i))
            G_drive.add_edge(i,sorted(distance, key=itemgetter(1))[1][0],
                             length=sorted(distance, key=itemgetter(1))[1][1])
        
        #G_drive=ox.project_graph(G_drive)
        
        G_drive=G_drive.to_undirected()
        
        elev=input ('elevation key-') 
        #elev='Y'
        if elev!='N':
            G_drive= ox.add_node_elevations(G_drive, 
                        api_key='%s'%(elev))
            G_drive= ox.add_edge_grades(G_drive)
            
        
        
        print ('elevation done','time taken : %s'%(datetime.now()-start))
        
    #    ox.save_graph_shapefile(G_drive, filename='%s_drive_orig'%(cityname))
    #    ox.save_graphml(G_drive, filename='%s_drive_orig.graphml'%(cityname))
        
        orig_graph.append(G_drive)
        
        print ('connected=%s'%(nx.is_connected(G_drive)))
        
        
        # =============================================================================
        # simplify the graph
        # =============================================================================
        
        #remove self loops    
        G_drive.remove_edges_from(list(G_drive.selfloop_edges()))
        
        n_nodes_edges.append(['self_loop',G_drive.number_of_nodes(),
                              len(G_drive.edges)])
            
        #remove highways 
            
        highway=[] 
        
        
        
        for e1,e2,c in G_drive.edges(data='highway'):
            
            
            if c=='motorway_link' or c=='motorway':
                
                
                highway.append((e1,e2))
        
        
        G_drive.remove_edges_from(highway)
        
        n_nodes_edges.append(['highway',G_drive.number_of_nodes(),
                              len(G_drive.edges)])
        
        
        
        #remove parallel links      
        parallel=[]
        
        for e1,e2,c in G_drive.edges:
            
            if len(G_drive[e1][e2].keys())>1:
            
                #print (type(G[e1][e2]),len(G[e1][e2].keys()))
                parallel.append((e1,e2))
                
                
        
        for edge in list(set(parallel)):
            
            try:
                G_drive.remove_edge(edge[0],edge[1],key=2)
                G_drive.remove_edge(edge[0],edge[1],key=1)
                
            except:
                
                G_drive.remove_edge(edge[0],edge[1],key=1)
                
        n_nodes_edges.append(['parallel',G_drive.number_of_nodes(),
                              len(G_drive.edges)])
        
        # remove lone nodes to make the graph connected    
        lone_nodes=[]
        
        for node in G_drive.nodes:
            
            if G_drive.degree(node)==0:
                
                lone_nodes.append(node)
                
        
        G_drive.remove_nodes_from(lone_nodes)
        
        n_nodes_edges.append(['lone_nodes',G_drive.number_of_nodes(),
                              len(G_drive.edges)])
            
        #make the graph connected
            
        if nx.is_connected(G_drive)==False:
            
            print ('connected=%s'%(nx.is_connected(G_drive)))
            
            sub_graphs = nx.connected_component_subgraphs(G_drive)
            
            n_sg=[(i,sg.number_of_nodes()) for i,sg in enumerate(sub_graphs)]
            
            n_sg=sorted(n_sg,key=lambda x:x[1],reverse=True)[0][1]
            
            print (n_sg)
            
            sub_graphs = nx.connected_component_subgraphs(G_drive)
            
            dis_nodes=[]
            for i,sg in enumerate(sub_graphs):
                
                if sg.number_of_nodes()<n_sg:
                
                    #print (i,sg.number_of_nodes(),sg.nodes())
                    
                    dis_nodes.extend(list(sg.nodes()))
                    
            G_drive.remove_nodes_from(dis_nodes)
            
            n_nodes_edges.append(['dis_nodes',G_drive.number_of_nodes(),
                                  len(G_drive.edges)])
                
            print ('connected=%s'%(nx.is_connected(G_drive)))
            
        else:
            
            print ('connected=%s'%(nx.is_connected(G_drive)))
        
        
        drive_graph.append(G_drive)
        
        
        
        print ('simplification done','nodes-%s'%(len(G_drive.nodes)),
               'edges-%s'%(len(G_drive.edges)),'time taken : %s'%(datetime.now()-start))
        
     

    ox.save_graph_shapefile(G_drive, filename='%s_drive'%(cityname))
    ox.save_graphml(G_drive, filename='%s_drive.graphml'%(cityname))
    # =============================================================================
    # water demand
    # =============================================================================
    orig_edge=os.path.join(os.getcwd(),'data','%s_drive'%(cityname),'edges','edges.shp')
    orig_node=os.path.join(os.getcwd(),'data','%s_drive'%(cityname),'nodes','nodes.shp')
    #
    orig_edge=gpd.read_file(orig_edge)
    orig_node=gpd.read_file(orig_node)

    nodes=orig_node
    wdemand=gpd.read_file(os.path.join(os.getcwd(),
      'wDemandIUWM_%s'%(cityname),'%s_waterDemand.shp'%(cityname)))
    fig_wd, ax_wd = plt.subplots(1, 1)

    wdemand.plot(ax=ax_wd,column='demand',legend=True)
    ax_wd.set_xticks([])
    ax_wd.set_yticks([])
    ax_wd.axis('off')

    #fig_wd.savefig('%s_wdemand.pdf'%(cityname))

    print (nodes.crs,wdemand.crs)
    wdemand.crs=nodes.crs

    demand=gpd.sjoin(nodes,wdemand,op='within')



    df_demand=pd.DataFrame(demand)

    print (len(df_demand.index))

    uniqCenBlck=df_demand.geoid_s.unique()

    for cb in uniqCenBlck:
        
        df1=df_demand[df_demand.geoid_s==cb]
        w_demand=float(round(df1['demand'].iloc[0]/len(df1.index),2))
        
        for n in df1['osmid']:
            
            G_drive.node[int(n)]['wDemand']=w_demand
        
    wDemand=nx.get_node_attributes(G_drive,'wDemand')

    min_demand=min([val for val in wDemand.values() if val!=0])

    print (len(wDemand.values()),min_demand)

    for n in G_drive.nodes:
        
        try:
            
            G_drive.node[n]['wDemand']+=0
        except:
            
            G_drive.node[n]['wDemand']=min_demand
            
            
            
            

    wDemand=nx.get_node_attributes(G_drive,'wDemand')

    print (len(wDemand.values())) 

    print (G_drive.node[list(G_drive.nodes)[3]])
    ox.save_graph_shapefile(G_drive, filename='%s_drive'%(cityname))
    ox.save_graphml(G_drive, filename='%s_drive.graphml'%(cityname)) 
        
    print ('wdemand done','time taken : %s'%(datetime.now()-start))

    # minimum spanning tree

    T=nx.minimum_spanning_tree(G_drive)
    print ('span',len(T.edges),
           '%s percent edges removed'%((len(G_drive.edges)-len(T.edges))*100/len(G_drive.edges)))


    ox.save_graph_shapefile(T, filename='%s_span'%(cityname))
    ox.save_graphml(T, filename='%s_span.graphml'%(cityname))
    n_nodes_edges.append(['span_tree',T.number_of_nodes(),
                          len(T.edges)])
        
    df=pd.DataFrame(n_nodes_edges)
    df.columns=['Type','nodes','edges']
    #df.to_csv('no_node_edge.csv',index=False)
    #print ('Total time taken : %s'%(datetime.now()-start))

    return cityname
#data()








