from datetime import datetime
start=datetime.now()

import networkx as nx 
import pyproj
import matplotlib.pyplot as plt
import numpy as np
import os


def perinode(city):

	G=nx.read_graphml(os.path.join(os.getcwd(),'data','%s_drive.graphml'%(city)))

	for i in range(1,10):

		try:
			G.remove_node(str(i))
		except:
			continue

	for n in G.nodes():

		try:
			G.node[n]['x']=G.node[n]['longitude']
			G.node[n]['y']=G.node[n]['latitude']
		except:
			continue

	print (nx.number_of_nodes(G),nx.number_of_edges(G))

	
	
	bc_n=nx.edge_betweenness_centrality(G,normalized=True)
	nx.set_edge_attributes(G, bc_n, 'betweenness_n')

	

	nx.write_graphml(G, "%s_bc.graphml"%(city))

	print ('betweeness done')

	
	bc=[]

	for (e1,e2) in G.edges():

		bc.append([(e1,e2),G[e1][e2]['betweenness_n']])
		G[e1][e2]['len_flt']=float(G[e1][e2]['length'])


	bc=sorted(bc,key=lambda x:x[1],reverse=True)


	G1_nodes=list(bc[0][0])

	print (G1_nodes)

	G1_nodes.append(list(nx.bfs_tree(G,G1_nodes[0]))[-1])

	print (G1_nodes)

	all_path=nx.single_source_dijkstra_path(G, G1_nodes[-1])

	print ('all_path',all_path[list(all_path.keys())[1]])

	path=[]

	print (G1_nodes[:2])

	for k in all_path.keys():

		if set.intersection(set(all_path[k]),set(G1_nodes[:2]))==set(G1_nodes[:2]):

			path.append([k,len(all_path[k])])

	path=sorted(path,key=lambda x:x[1],reverse=True)

	G1_nodes.append(path[0][0])

	G1=nx.subgraph(G,G1_nodes)

	print (G1_nodes)

	

	return G1_nodes[2:]


#print (perinode("tempe"))

# print ('Total time taken : %s'%(datetime.now()-start))



 