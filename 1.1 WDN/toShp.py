# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 09:34:27 2019

@author: sahmad20
"""

import geopandas as gpd
import os
import networkx as nx
import pandas as pd
import shutil
#cityname=input('enter city name-')



def shp(cityname):
	G=nx.read_graphml('%s_dia.graphml'%(cityname))
	# path=os.getcwd()

	# path=os.path.join(path,'%s_drive'%(cityname),'edges','edges.shp')

	tempe=gpd.read_file(os.path.join(os.getcwd(),'data','%s_drive'%(cityname),'edges','edges.shp'))

	tempe['id']=''

	for i in range(len(tempe.index)):
	    
	    tempe['id'].iloc[i]=str(tempe['from'].iloc[i])+tempe['to'].iloc[i]

	print (len(tempe.index),len(G.edges),len(tempe['id'].unique()))
	#print (list(G.edges)[5:7])

	#df_edge=pd.DataFrame()
	edge=[]
	for (e1,e2) in list(G.edges):
	    
	    #print (G[e1][e2])
	    
	    try:
	    
	        edge.append([str(e1)+str(e2),G[e1][e2]['dia(in)']])
	    except:
	        continue
	        

	print (len(edge))
	#
	df_edge=pd.DataFrame(edge)
	#
	df_edge.columns=['id','dia']
	print (df_edge.dtypes)
	tempe=tempe.merge(df_edge,on='id')
	#
	print (len(tempe.id))

	print (tempe.crs)

	try:
		os.mkdir('%s_shp'%(cityname))
	except:
		shutil.rmtree('%s_shp'%(cityname))
		os.mkdir('%s_shp'%(cityname))


	tempe.to_file(os.path.join(os.getcwd(),'%s_shp'%(cityname),
	                           '%s_edges.shp'%(cityname)))
        


