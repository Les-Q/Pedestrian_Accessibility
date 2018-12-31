# -*- coding: utf-8 -*-
"""
Created on Sun Dec 30 21:26:11 2018

@author: Les
"""
#from urllib.error import HTTPError
from requests.exceptions import HTTPError
import pandas as pd
from pandana.loaders import osm


def build_node_query_TEMP(lat_min, lng_min, lat_max, lng_max, tags=None):
    """
    Build the string for a node-based OSM query.
    Parameters
    ----------
    lat_min, lng_min, lat_max, lng_max : float
    tags : str or list of str, optional
        Node tags that will be used to filter the search.
        See http://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
        for information about OSM Overpass queries
        and http://wiki.openstreetmap.org/wiki/Map_Features
        for a list of tags.
    Returns
    -------
    query : str
    """
    if tags is not None:
        if isinstance(tags, str):
            tags = [tags]
        tags = ''.join('[{}]'.format(t) for t in tags)
    else:
        tags = ''

    query_fmt = (
        '[out:json];'
        '('
        '  node'
        '  {tags}'
        '  ({lat_min},{lng_min},{lat_max},{lng_max});'
        ');'
        'out;')

    return query_fmt.format(
        lat_min=lat_min, lng_min=lng_min, lat_max=lat_max, lng_max=lng_max,
        tags=tags)
    
def build_feature_query(lat_min, lng_min, lat_max, lng_max, tags=None):
    """
    Build the string for a node-based OSM query.
    Parameters
    ----------
    lat_min, lng_min, lat_max, lng_max : float
    tags : str or list of str, optional
        Node tags that will be used to filter the search.
        See http://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
        for information about OSM Overpass queries
        and http://wiki.openstreetmap.org/wiki/Map_Features
        for a list of tags.
    Returns
    -------
    query : str
    """
    if tags is not None:
        if isinstance(tags, str):
            tags = [tags]
        tags = ''.join('[{}]'.format(t) for t in tags)
    else:
        tags = ''


    query_fmt_node = (
      #  '('
        '  node'
        '  {tags}'
        '  ({lat_min},{lng_min},{lat_max},{lng_max});')
#        ');')
    query_node = query_fmt_node.format(
        lat_min=lat_min, lng_min=lng_min, lat_max=lat_max, lng_max=lng_max,
        tags=tags)
    query_fmt_way = (
        #'('
        '  way'
        '  {tags}'
        '  ({lat_min},{lng_min},{lat_max},{lng_max});')
        #');')
    query_way = query_fmt_way.format(
        lat_min=lat_min, lng_min=lng_min, lat_max=lat_max, lng_max=lng_max,
        tags=tags)
    
    query_fmt = (
        '[out:json];'
        '({q_node}'
        '{q_way} );'
        '(._;>;);'
        'out;')

    return query_fmt.format(q_node=query_node, q_way=query_way)

def build_way_query(lat_min, lng_min, lat_max, lng_max, tags=None):
    """
    Build the string for a node-based OSM query.
    Parameters
    ----------
    lat_min, lng_min, lat_max, lng_max : float
    tags : str or list of str, optional
        Node tags that will be used to filter the search.
        See http://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
        for information about OSM Overpass queries
        and http://wiki.openstreetmap.org/wiki/Map_Features
        for a list of tags.
    Returns
    -------
    query : str
    """
    if tags is not None:
        if isinstance(tags, str):
            tags = [tags]
        tags = ''.join('[{}]'.format(t) for t in tags)
    else:
        tags = ''


    query_fmt_way = (
        #'('
        '  way'
        '  {tags}'
        '  ({lat_min},{lng_min},{lat_max},{lng_max});')
        #');')
    query_way = query_fmt_way.format(lat_min=lat_min, lng_min=lng_min, 
                                     lat_max=lat_max, lng_max=lng_max,
                                     tags=tags)
    
    query_fmt = (
        '[out:json];'
        '( {q_way} );'
        'out;')

    return query_fmt.format(q_way=query_way)


def process_way(e):
    """
    Process a way element entry into a dict suitable for going into
    a Pandas DataFrame.
    Parameters
    ----------
    e : dict
    Returns
    -------
    node : dict
    """

    uninteresting_tags = {
        'source',
        'source_ref',
        'source:ref',
        'history',
        'attribution',
        'created_by',
        'tiger:tlid',
        'tiger:upload_uuid',
    }

    all_node_ids = e['nodes']

    nodes = []
    nodes.append( node_query_by_id(all_node_ids, True) )   
    nodes_df = pd.DataFrame.from_records(nodes, index='id')
    avg_lat = nodes_df['lat'].mean()
    avg_lon = nodes_df['lon'].mean()
    way = {
        'id': e['id'],
        'lat': avg_lat,
        'lon': avg_lon
    }

    if 'tags' in e:
        for t, v in list(e['tags'].items()):
            if t not in uninteresting_tags:
                way[t] = v

    return way


def node_query_by_id(node_ids,v=False):
    
    
        if len(node_ids) < 1:
            raise ValueError('Empty list of Node IDs')
        query_all_nodes = ['node({n_id})'.format(n_id=n_id) for n_id in node_ids]
        query_fmt = (
        '[out:json];'
        '('
        '{nodes_str};'
        ');'
        '(._;>;);'
        'out;')
        query = query_fmt.format(nodes_str=';'.join(query_all_nodes))
#        if v:
#            print("processing node ID {}".format(node_ids[0]))
#            print(query)
        node_data = osm.make_osm_query(query)

        if len(node_data['elements']) == 0:
            raise RuntimeError('OSM query results contain no data.')
#        if v:
#            print(node_data['elements'])    
        return osm.process_node(node_data['elements'][0]) 
    
def node_query_TMP(query):
    """
    Search for OSM nodes within a bounding box that match given tags.
    Parameters
    ----------
    lat_min, lng_min, lat_max, lng_max : float
    tags : str or list of str, optional
        Node tags that will be used to filter the search.
        See http://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
        for information about OSM Overpass queries
        and http://wiki.openstreetmap.org/wiki/Map_Features
        for a list of tags.
    Returns
    -------
    nodes : pandas.DataFrame
        Will have 'lat' and 'lon' columns, plus other columns for the
        tags associated with the node (these will vary based on the query).
        Index will be the OSM node IDs.
    """
    node_data = osm.make_osm_query(query)

    if len(node_data['elements']) == 0:
        raise RuntimeError('OSM query results contain no data.')

    nodes = [osm.process_node(n) for n in node_data['elements']]
    return pd.DataFrame.from_records(nodes, index='id')
    
def way_query(lat_min, lng_min, lat_max, lng_max, tags):

    query = build_way_query(lat_min, lng_min, lat_max, lng_max, tags=tags)
    try:
        print(query)
        ways_data = osm.make_osm_query( query )
    except HTTPError as err:
        print(err)
        print("Query submitted by OSM API:\n{q}\n\n".format(q=query))
        raise 
        
    if len(ways_data['elements']) == 0:
        raise RuntimeError('OSM query results contain no data.')
    ways = [process_way(n) for n in ways_data['elements']]
    ways_df = pd.DataFrame()
    if len(ways)>0:
        ways_df = pd.DataFrame.from_records(ways, index='id')
        ways_df['type'] = 'way'
    return ways_df
 
def feature_query(lat_min, lng_min, lat_max, lng_max, tags, features=['nodes', 'ways', 'rels']):

    do_nodes=False
    do_ways=False
    do_rels=False
    if 'nodes' in features :
        do_nodes = True
    if 'ways' in features :
        do_ways = True
    if 'rels' in features :
        do_rels = True
    
    ### first retrieve all the node data in the bbox for those tags
    nodes_df = pd.DataFrame()
    if do_nodes:
        print("Retrieving nodes")
        nodes_df = osm.node_query(lat_min, lng_min, lat_max, lng_max, tags)    
        print("Retrieved {} nodes in the given bounding box".format(nodes_df.shape[0]))
    ### get the data relative to the ways in the same bbox
    ### warning: this might be slow because under the hood it will 
    ### also query all the nodes associated to each query in order to
    ### compute an average lat/lon for the way
    ways_df = pd.DataFrame()
    if do_ways:
        print("Retrieving ways")
        ways_df = way_query(lat_min, lng_min, lat_max, lng_max, tags)
        print("Retrieved {} ways in the given bounding box".format(ways_df.shape[0]))
    
    ### TO-DO: add same thing for relationships
    rels_df = pd.DataFrame()
    
    ### append all results in one output df
    all_df = pd.concat([nodes_df, ways_df, rels_df], ignore_index=True, sort=False)
    
    return all_df
    
if __name__=='__main__':
    melbourne_bbox = {'south':-37.83, 'west':144.855 ,'north':-37.73, 'east':145.010}
    torino_bbox = {'south':45.0027314, 'west':7.6118697 ,'north':45.1139324, 'east':7.6973155}

    q1 = osm.build_node_query(melbourne_bbox['south'], melbourne_bbox['west'], melbourne_bbox['north'], melbourne_bbox['east'], tags='amenity')
    print(q1)
    #node_data1 = node_query_TMP(q1)
    q2 = build_way_query(melbourne_bbox['south'], melbourne_bbox['west'], melbourne_bbox['north'], melbourne_bbox['east'], tags='amenity')
    print(q2)
    node_data2 = feature_query(torino_bbox['south'], torino_bbox['west'], torino_bbox['north'], torino_bbox['east'], 
                               tags='amenity', features=['nodes', 'ways'])
    node_data2.to_pickle('./Torino_POIs_nodes-and-ways_amenities-only.pkl')
#    xml_data2 = osm.make_osm_query(q2)
#    nodes = [osm.process_node(n) for n in node_data['elements']]


