# -*- coding: utf-8 -*-
"""

Inspired by the example described in 
https://towardsdatascience.com/measuring-pedestrian-accessibility-97900f9e4d56

Chunks of code taken from 
http://kuanbutts.com/2017/08/08/how-to-pdna/

Beware: multiple bugs needed to be sorted out in order to install all the necessary libraries

Created on Sat Dec 29 22:17:24 2018

@author: Bonny
"""

print("\nLoading libraries")
import os 
os.environ["PROJ_LIB"] = "C:\\Users\\Bonny\\Anaconda3\\Lib\\site-packages\\pyproj\\data"
import pandas as pd
from copy import copy
#import mpl_toolkits
#mpl_toolkits.__path__.append("C:\\Users\\Bonny\\Anaconda3\\Lib\\site-packages\\mpl_toolkits")
from mpl_toolkits.basemap import Basemap ### needs basemap lib: conda install -c conda-forge basemap
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.colorbar import colorbar
import matplotlib.pyplot as plt

import osmnx as ox
import pandana as pdna
from pandana.loaders import osm

from shapely.geometry import Point
from descartes import PolygonPatch

from accessibility_helpers import *



melbourne_bbox = {'south':-37.83, 'west':144.855 ,'north':-37.73, 'east':145.010}
melbourne_house_poi = Point( 144.97766, -37.75807) # our house, Lincoln Street

torino_bbox = {'south':45.0027314, 'west':7.6118697 ,'north':45.1139324, 'east':7.6973155}
torino_house_poi = Point(7.6486667, 45.0656553) # Dario's house

city_name = 'Melbourne'
max_dist = 3000 #CONSIDER ONLY AMENITIES WITHIN THIS DISTANCE (IN METERS)
max_pois = 3    #consider a max number of points of interest (always within the max distance)


if city_name=='Torino':
    bbox = torino_bbox
    house_poi = torino_house_poi
elif city_name=='Melbourne':
    bbox = melbourne_bbox
    house_poi = melbourne_house_poi
else:
    raise ValueError('Invalid city name {}'.format(city_name))


### EXTRACT OPENSOURCEMAP NETWORK INFORMATION
print("\nExtracting OpenSourceMap network info with osmnx")
### Use the osmnx library; full documents and examples at
### https://github.com/gboeing/osmnx

### one can select specifiic areas...
#places = ['Melbourne, Victoria, Australia', 'Carlton, Victoria, Australia', 
#          'North Melbourne, Victoria, Australia', 'Parkville, Victoria, Australia',
#          'Brunswick, Victoria, Australia',  'Brunswick East, Victoria, Australia',  
#          'Brunswick West, Victoria, Australia', 'Fitzroy, Victoria, Australia', 
#          'Fitzroy North, Victoria, Australia','Richmond, Victoria, Australia' ]
#
#G = ox.graph_from_place(places, network_type='drive')#distance=2000, distance_type='bbox')

### ...or pick everything within a certain radius...
#network_centre_coords = ( -37.813, 144.944) # Melbourne
#network_radius = 7000 # in meters
#G = ox.graph_from_point(network_centre_coords, distance=network_radius, network_type='drive')

### or pass directly a bounding box of lat/lon coordinates

G = ox.graph_from_bbox(bbox['north'], bbox['south'], bbox['east'], bbox['west'], network_type='drive')

###the output G is a networkx multidigraph; can be plotted easily
print("\nPlotting network")
#nodes = G.nodes
#edges = G.edges
plt.ion()
fig, ax = ox.plot_graph(G, fig_height=10, node_size=0, show=False, close=False)
#add a red marker for our house
house_patch = PolygonPatch(house_poi.buffer(0.001), fc='red', ec='red', linewidth=3,alpha=1, zorder=1)
ax.add_patch(house_patch)
ax.set_aspect(1)
fig.savefig('./{}_fig01.png'.format(city_name), bbox_inches='tight')
plt.gcf().clear()

### extract the nodes and edges from the OSMNX object anc cast them into pandas dataframes
### The pd df will be then imported into pandana objects



print("\nImporting edges into a df")
edges_df = create_edges_df(G)
print("\nImporting nodes into a df")
nodes_df = create_nodes_df(G)


# Instantiate a Pandana (pdna) network (net)
print("\nCreating pandana network")
net = pdna.Network(nodes_df['x'], nodes_df['y'],
                   edges_df['st_node'], edges_df['en_node'],
                   edges_df[['weight']])

net.precompute(max_dist*1.1)

### Now we download the location of interesting amenities via the pandana library
### We will then overlap them onto the network we have just downloaded above and
### compute the distances

### define your selected amenities and bounding box
### full list of amenities: https://wiki.openstreetmap.org/wiki/Map_Features#Amenity
amenities = ['hospital', 'clinic', 'doctors', 'pharmacy', 'dentist', 'school', 'police', 'swimming_pool']# 
amenities2 = ['restaurant','cafe','bank','park']

# request them from the OpenStreetMap API (Overpass)
print("\nImporting list of Points Of Interest")
all_pois = osm.node_query(bbox['south'], bbox['west'], bbox['north'], bbox['east'])#,tags="amenity")
pois = all_pois[all_pois['amenity'].isin(amenities)]

print("\nComputing accessibility for the closest {} POIs within {} meters".format(max_pois, max_dist))
for amenity in amenities:
    pois_subset = pois.loc[pois['amenity']==amenity , ]
    net.set_pois(category=amenity, maxdist=max_dist, maxitems=max_pois, x_col=pois_subset['lon'], y_col=pois_subset['lat'])

n1 = net.nearest_pois(max_dist, "school", num_pois=max_pois, include_poi_ids=True)
print("\n***************")
print(n1.describe())
print("\n***************\n")
 
fig_size=None
if city_name=='Torino':
    fig_size=(8,10)
    
for a in amenities:
    print("\nPlotting {}".format(a))
    house_patch2 = PolygonPatch(house_poi.buffer(0.001), fc='red', ec='red', linewidth=3,alpha=1, zorder=1)
    patches = [house_patch2]
    sel_pois = pois.loc[pois['amenity']==a, ['amenity','name','lat','lon']]
    for i in range(0,sel_pois.shape[0],1):
        tmp_poi = Point( (sel_pois['lon'].values)[i], (sel_pois['lat'].values)[i])
        patches.append(PolygonPatch(tmp_poi.buffer(0.001), fc='purple', ec='purple', linewidth=3,alpha=1, zorder=1) )
    
    bm, fig, ax = plot_nearest_amenity(net, a, 1, list(bbox.values()), max_dist, max_pois, city_name=city_name, 
                                       patches=patches, fig_size=fig_size)
    #ax.add_patch(house_patch2)
    fig.savefig('./{}_accessibility_{}.png'.format( city_name,a), bbox_anchor='tight')
    plt.gcf().clear()
