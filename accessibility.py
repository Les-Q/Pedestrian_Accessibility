# -*- coding: utf-8 -*-
"""

Inspired by the example described in 
https://towardsdatascience.com/measuring-pedestrian-accessibility-97900f9e4d56

Chunks of code taken from 
http://kuanbutts.com/2017/08/08/how-to-pdna/

Beware: multiple bugs needed to be sorted out in order to install all the necessary libraries

Created on Sat Dec 29 22:17:24 2018

@author: Les
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

from shapely.geometry import Point, Polygon, MultiPolygon
from descartes import PolygonPatch

from accessibility_helpers import *



melbourne_bbox = {'south':-37.83, 'west':144.855 ,'north':-37.73, 'east':145.010}
melbourne_house_poi = Point( 144.97766, -37.75807) # our house, Lincoln Street

torino_bbox = {'south':45.005, 'west':7.578 ,'north':45.140, 'east':7.773}
torino_house_poi = Point(7.6486667, 45.0656553) # Dario's house
#torino_bbox = {'south':44.85, 'west':7.6118697 ,'north':45.25, 'east':7.6973155}

city_name = 'Torino'
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


### import also the boundaries of the city
# get the place shape
gdf_string = ""
if city_name=='Melbourne':
    gdf_string = "Melbourne, Victoria, Australia"
if city_name=='Torino':
    gdf_string = "Torino, Italy"
    
gdf = ox.gdf_from_place(gdf_string)

###the output G is a networkx multidigraph; can be plotted easily
print("\nPlotting network")
#nodes = G.nodes
#edges = G.edges
fig_height=20
w_over_h = (bbox['east'] - bbox['west']) / (bbox['north'] - bbox['south']) 
plt.ion()
fig, ax = ox.plot_graph(G, fig_height=fig_height, fig_width=fig_height*w_over_h, node_size=0, show=False, close=False)

# to this matplotlib axis, add the place shape as descartes polygon patches
for geometry in gdf['geometry'].tolist():
    if isinstance(geometry, (Polygon, MultiPolygon)):
        if isinstance(geometry, Polygon):
            geometry = MultiPolygon([geometry])
        for polygon in geometry:
            patch = PolygonPatch(polygon, fc='white', ec='royalblue', linewidth=2, alpha=1, zorder=-1)
            ax.add_patch(patch)

# optionally set up the axes extents all nicely
margin = 0.02
gdf_west, gdf_south, gdf_east, gdf_north = gdf.unary_union.bounds
margin_ns = (gdf_north - gdf_south) * margin
margin_ew = (gdf_east - gdf_west) * margin
ax.set_ylim((gdf_south - margin_ns, gdf_north + margin_ns))
ax.set_xlim((gdf_west - margin_ew, gdf_east + margin_ew))

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
#all_pois = osm.node_query(bbox['south'], bbox['west'], bbox['north'], bbox['east'])#,tags="amenity")
all_pois= pd.read_pickle('./{city}_POIs_nodes-and-ways_amenities-only.pkl'.format(city=city_name))
pois = all_pois[all_pois['amenity'].isin(amenities)]

print("\nComputing accessibility for the closest {} POIs within {} meters".format(max_pois, max_dist))
for amenity in amenities:
    pois_subset = pois.loc[pois['amenity']==amenity , ]
    net.set_pois(category=amenity, maxdist=max_dist, maxitems=max_pois, x_col=pois_subset['lon'], y_col=pois_subset['lat'])
#### end for loop
    
###     
n1 = net.nearest_pois(max_dist, amenities[0], num_pois=max_pois, include_poi_ids=True)
print("\n***************")
print(n1.describe())
print("\n***************\n")
 
fig_size=( fig_height*w_over_h*1.15,fig_height)#add some buffer for the side colorbar
#if city_name=='Torino':
#    fig_size=(8,10)
    
for amenity in amenities:
    print("\nPlotting {}".format(amenity))
    house_patch2 = PolygonPatch(house_poi.buffer(0.001), fc='red', ec='red', linewidth=3,alpha=1, zorder=1)
    patches = [house_patch2]
    sel_pois = pois.loc[pois['amenity']==amenity, ['amenity','name','lat','lon']]
    for i in range(0,sel_pois.shape[0],1):
        tmp_poi = Point( (sel_pois['lon'].values)[i], (sel_pois['lat'].values)[i])
        patches.append(PolygonPatch(tmp_poi.buffer(0.001), fc='purple', ec='purple', linewidth=3,alpha=1, zorder=1) )
    
    bm, fig, ax = plot_nearest_amenity(net, amenity, 1, list(bbox.values()), max_dist, max_pois, city_name=city_name, 
                                       plot_type='hex', patches=patches, fig_size=fig_size)
    
    # to this matplotlib axis, add the place shape as descartes polygon patches
    for geometry in gdf['geometry'].tolist():
        if isinstance(geometry, (Polygon, MultiPolygon)):
            if isinstance(geometry, Polygon):
                geometry = MultiPolygon([geometry])
            for polygon in geometry:
                patch = PolygonPatch(polygon, fill=False, ec='yellow', linewidth=4, alpha=1, zorder=1)
                ax.add_patch(patch)

    #ax.add_patch(house_patch2)
    fig.savefig('./{}_accessibility_{}_hex.png'.format( city_name,amenity), bbox_anchor='tight')
    plt.gcf().clear()

####now same but in scatter plot format
    bmB, figB, axB = plot_nearest_amenity(net, amenity, 1, list(bbox.values()), max_dist, max_pois, city_name=city_name, 
                                       plot_type='scatter', patches=patches, fig_size=fig_size)
    
    # to this matplotlib axis, add the place shape as descartes polygon patches
    for geometry in gdf['geometry'].tolist():
        if isinstance(geometry, (Polygon, MultiPolygon)):
            if isinstance(geometry, Polygon):
                geometry = MultiPolygon([geometry])
            for polygon in geometry:
                patch = PolygonPatch(polygon, fill=False, ec='yellow', linewidth=4, alpha=1, zorder=1)
                axB.add_patch(patch)

    #ax.add_patch(house_patch2)
    figB.savefig('./{}_accessibility_{}_scatter.png'.format( city_name,amenity), bbox_anchor='tight')
    plt.gcf().clear()
