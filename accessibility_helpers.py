# -*- coding: utf-8 -*-
"""
Helper functions used fro accessibility analysis
Created on Sun Dec 30 15:33:36 2018

@author: Les
"""

import pandas as pd
from copy import copy
#import mpl_toolkits
#mpl_toolkits.__path__.append("C:\\Users\\Bonny\\Anaconda3\\Lib\\site-packages\\mpl_toolkits")
from mpl_toolkits.basemap import Basemap ### needs basemap lib: conda install -c conda-forge basemap
import matplotlib.pyplot as plt

import osmnx as ox
import pandana as pdna
from pandana.loaders import osm

from shapely.geometry import Point
from descartes import PolygonPatch


# Given a graph, generate a dataframe (df)
# representing all graph nodes

def create_nodes_df(G):
    # first make a df from the nodes
    # and pivot the results so that the 
    # individual node ids are listed as
    # row indices
    
    nodes_ref = {}
    
    for n in G.nodes.keys():
        n1_dict = G.nodes[n]
        name = n
        nodes_ref[name] ={'node_id':n, 'x':n1_dict['x'],  'y':n1_dict['y'] }
        
    nodes_df = pd.DataFrame( nodes_ref  ).T

    # cast it as an integer
    nodes_df['node_id'] = nodes_df['node_id'].astype('int64')
    nodes_df = nodes_df[['node_id', 'x', 'y']]
    return nodes_df
###
    
# Given a graph, generate a dataframe (df)
# representing all graph edges

def create_edges_df(G):
    # First, we must move the nested objects
    # to a signle top level dictionary
    # that can be consumed by a Pandas df
    edges_ref = {}
    
    # move through first key (origin node)
    for e in G.edges.keys():
        e_dict = G.edges[e]
        start = e[0]
        end = e[1]
        weight = e[2]
        edge_length = e_dict['length']

        # ugly, and unnecessary but might as
        # well name the index something useful
        name = '{}_{}'.format(start, end)
        # update the top level reference dict
        # with this new, prepared sub-dict
        edges_ref[name] = {'st_node':start, 'en_node':end, 'weight':weight, 'length':edge_length}
    ### end for loop over edges 
        
       
    # let's take the resulting dict and convert it
    # to a Pandas df, and pivot it as with the nodes
    # method to get unique edges as rows
    edges_df = pd.DataFrame(edges_ref).T
    
    # for the purposes of this example, we are not going
    # to bother with impedence along edge so they all get
    # set to the same value of 1
    edges_df['weight'] = 100
    edges_df = edges_df[['st_node', 'en_node', 'length', 'weight']]
    # update the edge start and stop nodes as integers
    # which is necessary for Pandana
    edges_df['st_node'] = edges_df['st_node'].astype('int64')
    edges_df['en_node'] = edges_df['en_node'].astype('int64')
    
    return edges_df
###


# function to plot distance to selected amenity
# -- default: distance to nearest amenity
# -- if a parameter n is supplied, distance to the nth nearest amenity

def plot_nearest_amenity(network,amenity,n, bbox, max_dist=1000, max_pois=1, city_name='Melbourne',
                         plot_type='scatter', patches=None, fig_size=None):
    
    accessibility = network.nearest_pois(distance=max_dist, category=amenity, num_pois=max_pois)
    
    if fig_size is None:
        fig_size=(14,10)
    # keyword arguments to pass for scatter plots
    plot_kwargs = {'s':2, 'alpha':0.9, 'cmap':'viridis_r', 'edgecolor':'none'}
    #bm, fig, ax = network.plot(accessibility[n], bbox,plot_type='scatter',plot_kwargs=plot_kwargs)
    fig, (ax1, ax2) = plt.subplots(1,2,figsize=fig_size, gridspec_kw = {'width_ratios':[15, 1]})
    bmap = Basemap( bbox[1], bbox[0], bbox[3], bbox[2], ax=ax1)
    bmap.drawcoastlines(color='red')
    bmap.drawmapboundary()
    x, y = bmap(network.nodes_df.x.values, network.nodes_df.y.values)
    
    if plot_type=='scatter':
        plot_kwargs = {'s':8, 'alpha':0.9, 'cmap':'viridis_r', 'edgecolor':'none'}
        plot = bmap.scatter( x, y, c=accessibility[n].values,latlon=True, **plot_kwargs)
    elif plot_type=='hex':
        plot_kwargs = { 'alpha':0.9, 'cmap':'viridis_r', 'edgecolor':'none'}
        plot = bmap.hexbin( x, y, C=accessibility[n].values, **plot_kwargs)
    else:
        raise ValueError("Invalid 'plot_type' input argument ({}). Valid options are: 'scatter', 'hex'".format(plot_type))
    # create an axes on the right side of ax. The width of cax will be 5%
    # of ax and the padding between cax and ax will be fixed at 0.05 inch.
    #divider = make_axes_locatable(ax1)
    #cax = divider.append_axes("right", size=0.05, pad=0.05)
    cb = plt.colorbar(plot, cax=ax2)
    cb.set_label('Distance (m)', fontsize=20)
    ax1.set_facecolor('k')
    ax1.set_title('Pedestrian accessibility in {} \n(Walking distance to closest {})'.format(city_name,amenity), 
                  fontsize=24);
    
    if patches is not None:
        for p in patches:
            ax1.add_patch(copy(p) )
              
                  
    ax1.set_aspect('auto')
    
    
    
    plt.tight_layout()
    return bmap,fig, ax1
