import pandas as pd

import sys

from qgis.core import *

qgs = QgsApplication([], False)

QgsApplication.setPrefixPath("/Applications/QGIS.app/Contents/MacOS", True)

qgs.initQgis()

sys.path.append('/Applications/QGIS.app/Contents/Resources/python/plugins')

import processing

from processing.core.Processing import Processing

Processing.initialize()

from QNEAT3.Qneat3Provider import Qneat3Provider

provider = Qneat3Provider()

QgsApplication.processingRegistry().addProvider(provider)

sys.path.append(r'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization')

import variables

BOOL_WEIGHT = variables.BOOL_WEIGHT

GRID_SIZE = variables.GRID_SIZE

def add_points(name,cluster):
    data_cluster = pd.read_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/{name}.csv')
    
    data_cluster.query(f'cluster=={cluster}').reset_index(drop=True).to_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_cluster.csv')

    uri = f"file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_cluster.csv?encoding=%s&delimiter=%s&xField=%s&yField=%s&crs=%s" % (
    "UTF-8", ",", "longitude", "latitude", "epsg:3857")

    # Make a vector layer
    point_layer = QgsVectorLayer(uri, f"{name}_temp", "delimitedtext")

    # Check if layer is valid
    if not point_layer.isValid():
        print("Layer not loaded")

    return point_layer

def creat_grid(layer):
    extent = layer.extent()  
    x_min = extent.xMinimum()
    y_min = extent.yMinimum()
    x_max = extent.xMaximum()
    y_max = extent.yMaximum()
    
    extent = f'{x_min},{x_max},{y_min},{y_max} [EPSG:3857]'

    processing.run("native:creategrid", {'TYPE':2,'EXTENT':extent,
                                        'HSPACING':GRID_SIZE,'VSPACING':GRID_SIZE,'HOVERLAY':0,'VOVERLAY':0,'CRS':QgsCoordinateReferenceSystem('EPSG:3857'),
                                        'OUTPUT':'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_grid.gpkg'})

def overlapping_points_grid():
    processing.run("native:countpointsinpolygon", {'POLYGONS':'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_grid.gpkg',
                                                    'POINTS':'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_cluster.csv?encoding=UTF-8&delimiter=,&xField=longitude&yField=latitude&crs=epsg:3857',
                                                    'WEIGHT':'','CLASSFIELD':'','FIELD':'NUMPOINTS','OUTPUT':'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_overlap.gpkg'})

def centroids_on_overlap():
    processing.run("native:centroids", {'INPUT':'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_overlap.gpkg|subset=NUMPOINTS > 0',
                                        'ALL_PARTS':False,'OUTPUT':'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_centroids.csv'})


    temp_centroids_csv = pd.read_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_centroids.csv')

    temp_centroids_csv ['longitude'] = (temp_centroids_csv['left'] + temp_centroids_csv['right']) / 2
    temp_centroids_csv ['latitude'] = (temp_centroids_csv['top'] + temp_centroids_csv['bottom']) / 2

    temp_centroids_csv[['longitude','latitude']].to_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_centroids.csv')

def attach_centroid_to_nearest_node():
    processing.run("qgis:distancetonearesthublinetohub", {'INPUT':'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_centroids.csv?encoding=UTF-8&delimiter=,&xField=longitude&yField=latitude&crs=epsg:3857',
                                                        'HUBS':'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/vertices.csv?encoding=UTF-8&delimiter=,&xField=longitude&yField=latitude&crs=epsg:3857',
                                                        'FIELD':'field_1','UNIT':0,'OUTPUT':'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_new_centroids_road_network.csv'})

    temp_new_centroids_road_network = pd.read_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_new_centroids_road_network.csv')[['HubName']]

    vertices = pd.read_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/vertices.csv')

    vertices ['field_1'] = vertices.index

    temp_new_centroids_road_network.merge(vertices,left_on='HubName',right_on='field_1')[['longitude','latitude']].to_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_neareast_vertices.csv')

def OD_matrix_possible_hubs():

    processing.run("qneat3:OdMatrixFromLayersAsTable", {'INPUT':'/Users/muhammadabdul/Desktop/Work/NTRC_Lahore-Road-Network/Lahore_District.shp','FROM_POINT_LAYER':'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_neareast_vertices.csv?encoding=UTF-8&delimiter=,&xField=longitude&yField=latitude&crs=epsg:3857',
                                                        'FROM_ID_FIELD':'field_1','TO_POINT_LAYER':'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_cluster.csv?encoding=UTF-8&delimiter=,&xField=longitude&yField=latitude&crs=epsg:3857',
                                                        'TO_ID_FIELD':'field_1','STRATEGY':0,'ENTRY_COST_CALCULATION_METHOD':0,'DIRECTION_FIELD':'direction','VALUE_FORWARD':'1','VALUE_BACKWARD':'1',
                                                        'VALUE_BOTH':'0','DEFAULT_DIRECTION':2,'SPEED_FIELD':'','DEFAULT_SPEED':5,'TOLERANCE':0,'OUTPUT':'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_OD_possible_hubs.csv'})

def centroid():
    temp_OD_possible_hubs = pd.read_csv("/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_OD_possible_hubs.csv")

    temp_centroids = pd.read_csv("/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_neareast_vertices.csv")

    temp_cluster = pd.read_csv("/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_cluster.csv")
    number_points = temp_cluster.shape[0]

    df_count_distance_origin_id = pd.DataFrame([temp_OD_possible_hubs.groupby('origin_id').count()['network_cost'].rename('count'),temp_OD_possible_hubs.groupby('origin_id').mean('network_cost')['network_cost']]).T
    origin_id_min_network_cost = df_count_distance_origin_id.query(f'count=={number_points}')['network_cost'].idxmin()

    return temp_centroids.iloc[origin_id_min_network_cost,1:].to_list()

def weighted_centroid():
    temp_OD_possible_hubs = pd.read_csv("/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_OD_possible_hubs.csv")

    temp_centroids = pd.read_csv("/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_neareast_vertices.csv")

    temp_cluster = pd.read_csv("/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_cluster.csv",index_col = 0)
    temp_cluster['index'] = temp_cluster.index
    number_points = temp_cluster.shape[0]

    temp_OD_possible_hubs = temp_OD_possible_hubs.merge(temp_cluster[['index','count']],left_on = 'destination_id',right_on = 'index')
    temp_OD_possible_hubs['weighted_network_cost'] = temp_OD_possible_hubs['network_cost'] * ((temp_OD_possible_hubs['count']))

    df_count_distance_origin_id = pd.DataFrame([temp_OD_possible_hubs.groupby('origin_id').count()['weighted_network_cost'].rename('count'),temp_OD_possible_hubs.groupby('origin_id').mean('weighted_network_cost')['weighted_network_cost']]).T
    origin_id_min_weighted_network_cost = df_count_distance_origin_id.query(f'count=={number_points}')['weighted_network_cost'].idxmin()
    
    temp_OD_possible_hubs.to_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/centroid_update/temp_OD_possible_hubs.csv')
    
    return temp_centroids.iloc[origin_id_min_weighted_network_cost,1:].to_list()

def centroid_update_road_network(itr,number_of_clusters):
    name_itr = itr - 1 
    name = f'data_with_cluster_network_distance_{name_itr}'

    updated_centroids = []

    for cluster in range(number_of_clusters):

        print(f'updating centroid of {cluster} cluster')
        print()

        point_layer = add_points(name,cluster)

        creat_grid(point_layer)

        overlapping_points_grid()

        centroids_on_overlap()

        attach_centroid_to_nearest_node()

        OD_matrix_possible_hubs()

        if BOOL_WEIGHT :
            updated_centroid = weighted_centroid()
        else:
            updated_centroid = centroid()

        updated_centroids.append(updated_centroid)

        QgsProject.instance().clear()

    return updated_centroids
