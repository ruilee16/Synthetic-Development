'''
required files - 

1) city boundary in shapefile format
2) IUWM water demand data from eRAMS (https://erams.com/iuwm)
3) water treatment plant location
4) Google map elevation key for elevation


'''



from datetime import datetime
start=datetime.now()


import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
#import seaborn
import os
import pandas as pd
import geopy.distance
from operator import itemgetter
import shutil



# download all data from OpenStreetMap

import getData

cityname=getData.data()


# Find the water main and other branches of the water network

from sPathToTrunk import pathToTrunk
pathToTrunk('%s'%(cityname))

from s_path_farthestnode import path

path('%s'%(cityname))


# Estimate diameter of pipes

from getDiameter import flow

flow('%s'%(cityname))

# Convert to shapefile

from toShp import shp

shp('%s'%(cityname))

# Convert to EPANET inp file

from toEpanet import epa_1
epa_1('%s'%(cityname))


# Move all necessary outputs to output folder

try:
    os.mkdir('output')
except:
    shutil.rmtree('output')
    os.mkdir('output')

shutil.move('%s_dia.graphml'%(cityname),'output')
shutil.move('%s.inp'%(cityname),'output')
shutil.move('%s_shp'%(cityname),'output')

print ('Total time taken : %s'%(datetime.now()-start))