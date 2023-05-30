import pandas as pd

import sys

import variables

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

import centroid_update_using_road_network

def network_dist(centroids,n_iterations):
    """Return the network distance of the two geo-coordinates"""
    temp_df_centroids = pd.DataFrame(centroids, columns=['longitude', 'latitude'])
    temp_df_centroids.to_csv(
        '/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/temp_df_centroids.csv')

    processing.run("qneat3:OdMatrixFromLayersAsTable",
                   {'INPUT': '/Users/muhammadabdul/Desktop/Work/NTRC_Lahore-Road-Network/Lahore_District.shp',
                    'FROM_POINT_LAYER': 'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/temp_df_centroids.csv?type=csv&maxFields=10000&detectTypes=yes&xField=Longitude&yField=Latitude&crs=EPSG:3857&spatialIndex=no&subsetIndex=no&watchFile=no',
                    'FROM_ID_FIELD': 'field_1',
                    'TO_POINT_LAYER': f'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/to_point_layer_{n_iterations}.csv?type=csv&maxFields=10000&detectTypes=yes&xField=longitude&yField=latitude&crs=EPSG:3857&spatialIndex=no&subsetIndex=no&watchFile=no',
                    'TO_ID_FIELD': 'field_1', 'STRATEGY': 0, 'ENTRY_COST_CALCULATION_METHOD': 0,
                    'DIRECTION_FIELD': 'direction', 'VALUE_FORWARD': '1', 'VALUE_BACKWARD': '1', 'VALUE_BOTH': '0',
                    'DEFAULT_DIRECTION': 2, 'SPEED_FIELD': '', 'DEFAULT_SPEED': 5, 'TOLERANCE': 0,
                    'OUTPUT': '/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/df_OD.csv'})

    to_point_layer = pd.read_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/to_point_layer_{n_iterations}.csv')

    df_OD = pd.read_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/df_OD.csv')

    nan_destination_ids=df_OD[df_OD['network_cost'].isna()]['destination_id'].unique()

    nan_df_lahore_lat_long = to_point_layer.iloc[nan_destination_ids,:]

    to_point_layer = to_point_layer.drop(nan_destination_ids).reset_index(drop=True)

    for _id in nan_destination_ids:
        df_OD.drop(df_OD.query('destination_id==@_id').index,inplace=True)

    to_point_layer.to_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/to_point_layer_{n_iterations}.csv')

    df_OD.reset_index(drop=True,inplace=True)

    lst_distances = []

    unique_ids=df_OD["destination_id"].unique()
    for i in unique_ids:
        temp_OD = df_OD.query(f"destination_id=={i}")
        lst_distances.append(temp_OD["network_cost"].tolist())

    return lst_distances, nan_df_lahore_lat_long[['longitude', 'latitude']]

def network_dist_new_centroids(new_centroids,centroids):
    temp_df_centroids = pd.DataFrame(centroids, columns=['longitude', 'latitude'])

    temp_df_new_centroids = pd.DataFrame(new_centroids, columns=['longitude', 'latitude'])

    temp_df_centroids.to_csv(
        '/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/temp_df_centroids.csv')
    
    temp_df_new_centroids.to_csv(
        '/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/temp_df_new_centroids.csv')


    processing.run("qneat3:OdMatrixFromLayersAsTable",
                   {'INPUT': '/Users/muhammadabdul/Desktop/Work/NTRC_Lahore-Road-Network/Lahore_District.shp',
                    'FROM_POINT_LAYER': 'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/temp_df_centroids.csv?type=csv&maxFields=10000&detectTypes=yes&xField=Longitude&yField=Latitude&crs=EPSG:3857&spatialIndex=no&subsetIndex=no&watchFile=no',
                    'FROM_ID_FIELD': 'field_1',
                    'TO_POINT_LAYER': 'delimitedtext://file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/temp_df_new_centroids.csv?type=csv&maxFields=10000&detectTypes=yes&xField=longitude&yField=latitude&crs=EPSG:3857&spatialIndex=no&subsetIndex=no&watchFile=no',
                    'TO_ID_FIELD': 'field_1', 'STRATEGY': 0, 'ENTRY_COST_CALCULATION_METHOD': 0,
                    'DIRECTION_FIELD': 'direction', 'VALUE_FORWARD': '1', 'VALUE_BACKWARD': '1', 'VALUE_BOTH': '0',
                    'DEFAULT_DIRECTION': 2, 'SPEED_FIELD': '', 'DEFAULT_SPEED': 5, 'TOLERANCE': 0,
                    'OUTPUT': '/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/df_OD_centroids_changes.csv'})

    df_OD = pd.read_csv('/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/df_OD_centroids_changes.csv')

    df_OD = df_OD.query('origin_id == destination_id').fillna(0)

    return df_OD['network_cost'].tolist()


def kmeans(centroids, distf, centroidf, cutoff, n_iterations,dist_centroidf):
    
    k = len(centroids)

    nan_lst_lahore_lat_long = []
    
    itr = 1

    while itr <= n_iterations:
        print(f"currently on : {itr} iteration")
        print()

        distances = distf(centroids,n_iterations)

        print('OD-Matrix calculated')
        print()

        nan_lst_lahore_lat_long.append(distances[1])

        temp_data = pd.read_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/to_point_layer_{n_iterations}.csv')[['longitude', 'latitude','count']]
        
        data = temp_data.values.tolist()

        data_to_centroids = [min(enumerate(x), key=lambda x: x[1])[0] for x in distances[0]]

        nan_df_lahore_lat_long = pd.concat(nan_lst_lahore_lat_long,axis=0)

        df_new_centroids = pd.DataFrame(centroids , columns = ['longitude' , 'latitude'])

        df_new_centroids.to_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/df_new_centroids_network_distance_{itr-1}.csv')

        nan_df_lahore_lat_long.to_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/nan_df_lahore_lat_long_{itr-1}.csv')

        temp_data['cluster'] = data_to_centroids

        columns = []

        for i in range(len(centroids)):
            columns.append(f'distance_{i}')
        df_distance = pd.DataFrame(distances[0] , columns = columns )

        temp_data = pd.concat([temp_data, df_distance], axis=1)

        temp_data.to_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/data_with_cluster_network_distance_{itr-1}.csv')

        new_centroids = centroidf(itr,k)

        print('centroids updated')
        print()

        changes = dist_centroidf(new_centroids, centroids)

        if max(changes) <= cutoff:
            distances = distf(centroids,n_iterations)
            print('Final OD-Matrix calculated')
            print()
            print(f'cutoff criteria met, stopping at {itr} iteration')
            print()
            data_to_centroids = [min(enumerate(x), key=lambda x: x[1])[0] for x in distances[0]]
            nan_lst_lahore_lat_long.append(distances[1])
            return centroids, data_to_centroids, distances[0],nan_lst_lahore_lat_long,itr

        print(f'iteration {itr} completed')
        print('---------------------------------------------')

        itr = itr + 1

        centroids = new_centroids
    distances = distf(centroids,n_iterations)
    print('Final OD-Matrix calculated')
    print()

    nan_lst_lahore_lat_long.append(distances[1])

    data_to_centroids = [min(enumerate(x), key=lambda x: x[1])[0] for x in distances[0]]

    return centroids, data_to_centroids, distances[0],nan_lst_lahore_lat_long,n_iterations

def add_points_generic(name):
    uri = f"file:///Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/{name}.csv?encoding=%s&delimiter=%s&xField=%s&yField=%s&crs=%s" % (
    "UTF-8", ",", "longitude", "latitude", "epsg:3857")

    # Make a vector layer
    point_layer = QgsVectorLayer(uri, f"{name}", "delimitedtext")

    # Check if layer is valid
    if not point_layer.isValid():
        print("Layer not loaded")

    # Add CSV data
    QgsProject.instance().addMapLayer(point_layer)

def main(n_iterations,centroids,cutoff):
    file_name = variables.file_name

    data = pd.read_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/{file_name}.csv')

    n_iterations = n_iterations

    data.to_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/to_point_layer_{n_iterations}.csv')

    centroids = centroids

    network_centroid_factory = centroid_update_using_road_network.centroid_update_road_network

    centroids, data_to_centroids, distances , nan_lst_lahore_lat_long, itr= kmeans(centroids,  network_dist, network_centroid_factory, cutoff, n_iterations ,network_dist_new_centroids)

    nan_df_lahore_lat_long = pd.concat(nan_lst_lahore_lat_long,axis=0)

    df_new_centroids = pd.DataFrame(centroids , columns = ['longitude' , 'latitude'])

    df_new_centroids.to_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/df_new_centroids_network_distance_{itr}.csv')

    data = pd.read_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/to_point_layer_{n_iterations}.csv')[['longitude', 'latitude','count']]

    nan_df_lahore_lat_long.to_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/nan_df_lahore_lat_long_{itr}.csv')

    data['cluster'] = data_to_centroids

    columns = []

    for i in range(len(centroids)):
        columns.append(f'distance_{i}')
    df_distance = pd.DataFrame(distances , columns = columns )

    data = pd.concat([data, df_distance], axis=1)

    data.to_csv(f'/Users/muhammadabdul/Desktop/Work/micro_hub_optimization/layer_files/data_with_cluster_network_distance_{itr}.csv')



 