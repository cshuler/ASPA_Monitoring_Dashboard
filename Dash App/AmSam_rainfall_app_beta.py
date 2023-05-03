# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 14:41:46 2023

@author: achie
"""

import os
import pathlib
import re

from datetime import datetime, timedelta

import pandas as pd
from dash.dependencies import Input, Output, State
import cufflinks as cs

import dash_bootstrap_components as dbc
import numpy as np
import matplotlib.dates as dates
from dash import Dash, html, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import dash_leaflet as dl

import plotly.io as pio
pio.renderers.default='browser'


master_station_file = open('Data/MasterStationList.txt', 'r')
streamflow_station_file = open('Data/Streamflow/DataFileNames.txt', 'r')
rainfall_station_file = open('Data/Rainfall/DataFileNames.txt', 'r')
weather_station_file = open('Data/Weather/DataFileNames.txt', 'r')

rainfall_metadata = pd.read_csv('Data/Rainfall/Rainfall_database_Metadata.csv', header=0, skiprows=[3])
streamflow_metadata = pd.read_csv('Data/Streamflow/Streamflow_Station_Metadata.csv')
weather_metadata = pd.read_csv('Data/Weather/Weather_Station_Metadata.csv')

station_names = [line.strip() for line in master_station_file.readlines()]
streamflow_files = [line.strip() for line in streamflow_station_file.readlines()]
rainfall_files = [line.strip() for line in rainfall_station_file.readlines()]
weather_files = [line.strip() for line in weather_station_file.readlines()]

rainfall_name_dict = {}
streamflow_name_dict = {}
weather_name_dict = {}

for i in range(len(rainfall_metadata)):
    rainfall_name_dict[i] = rainfall_metadata.iloc[i]['Site_name']

for i in range(len(streamflow_metadata)):
    streamflow_name_dict[i] = streamflow_metadata.iloc[i]['Site_name']

for i in range(len(weather_metadata)):
    weather_name_dict[i] = weather_metadata.iloc[i]['Site_name']

master_station_file.close()
streamflow_station_file.close()
rainfall_station_file.close()
weather_station_file.close()

streamflow_frames = {"m3ps" : [pd.read_csv('Data/Streamflow/'+str(name)+'_m3ps_processed.csv', index_col="DateTime", infer_datetime_format=True, parse_dates=True) for name in streamflow_files]}
rainfall_frames = {"RNF_in" : [pd.read_csv('Data/Rainfall/'+str(name)+'_RNF_in_processed.csv', index_col="DateTime", infer_datetime_format=True, parse_dates=True) for name in rainfall_files]}
weather_frames = {"SlrMJ_Tot": [pd.read_csv('Data/Weather/'+str(name)+'_SlrMJ_Tot_processed.csv', index_col="TIMESTAMP", infer_datetime_format=True, parse_dates=True) for name in weather_files]}

streamflow_markers = [dl.Marker(position=[streamflow_metadata.iloc[i]["LAT"], streamflow_metadata.iloc[i]["LON"]], id=str(streamflow_metadata.iloc[i]['Site_name']+'_Streamflow_map_token'), children=dl.Tooltip("Streamflow: "+str(streamflow_metadata.iloc[i]['Site_name']))) for i in range(len(streamflow_metadata))]
rainfall_markers = [dl.Marker(position=[rainfall_metadata.iloc[i]["LAT"], rainfall_metadata.iloc[i]["LON"]], id=str(rainfall_metadata.iloc[i]['Site_name']+'_Rainfall_map_token'), children=dl.Tooltip("Rainfall: "+str(rainfall_metadata.iloc[i]['Site_name']))) for i in range(len(rainfall_metadata))]
weather_markers = []

app = Dash(
    __name__,
    # Use a style from dash bootstrap components
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.title = "American Samoea Rainfall"
server = app.server

bound_name = 'Vaipito'

# [[-13.9829, -170.4105], [-14.5829, -171.0105]]

app.layout = html.Div(
    id="root",
    children=[
        dbc.Row([
                # html.A(
                    # html.Img(id="logo", src=app.get_asset_url("dash-logo.png")),
                    # href="https://plotly.com/dash"),
                html.H4(children="Public Watershed Data for American Samoa"),
                html.P(
                    id="description",
                    children="This will be a description",
                    ),
                ],
                ),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.P(
                        "Select a station in American Samoa to Begin",  
                        id="map-description"),
                    # dcc.Dropdown(
                        # options=[
                            # {"label": name,
                             # "value": name} for name in station_name_index_rainfall.keys()                                          
                            # ],
                        # value=list(station_name_index_rainfall.keys())[0],
                        # id="station-dropdown",
                        # ),
                    # dcc.Graph(
                        # id="map-of-samoa",
                        # figure=map_fig_2,
                        # ),
                    dl.Map(children=[dl.TileLayer(), dl.LayerGroup(rainfall_markers), dl.LayerGroup(streamflow_markers)],
                           bounds=[[(rainfall_metadata.query("Site_name == @bound_name")["LAT"].values+0.3)[0], (rainfall_metadata.query("Site_name == @bound_name")["LON"].values+0.3)[0]],
                                   [(rainfall_metadata.query("Site_name == @bound_name")["LAT"].values-0.3)[0], (rainfall_metadata.query("Site_name == @bound_name")["LON"].values-0.3)[0]]],
                           style={'height': '1000px', 'width':'1000px'},
                           id="leaflet-map")
                    ],
                    ),
                ],
                ),
            dbc.Col([
                html.Div([
                    html.P(
                        id="chart-selector",
                        children=["Select chart: "],
                        ),
                    dcc.Dropdown(
                        options=[
                            {"label": "Streamflow Data",
                             "value": "show_streamflow_data"},
                            {"label": "Weather Station Data",
                             "value": "show_weather_data"},
                            {"label": "Rainfall Data",
                             "value": "show_rainfall_data"}
                            ],
                        value="show_rainfall_data",
                        id="chart-dropdown",
                        ),
                    dcc.Graph(  
                        id="selected-station",
                        figure=go.Figure()
                        ),
                    dcc.RangeSlider(
                        min=2000,
                        max=2025,
                        value=[2000,2025],
                        marks={
                            str(year): {
                                "label": str(year),
                                "style": {"color": "#7fafdf"},
                            }
                            for year in range(2000, 2025)
                        },
                        id="graph-slider",
                        ),
                    html.Button("Download", 
                        id="selected-download-btn"),
                    dcc.Download(id="download-dataframe-csv")
                    ],
                    ),
                ],
                ),
            ],
            ),
    ],
    )

# TODO: Pull new data and update every 15 minutes TBD where/how this will work.

update_record = {"Streamflow": np.zeros((len(streamflow_metadata))),
                 "Rainfall": np.zeros((len(rainfall_metadata))),
                 "Weather": np.zeros((len(weather_metadata)))}

update_station = False
current_station = ['', 0] # Passed as a list, due to pass by reference requirements
graph_type = ['']

# ALL CALLBACKS FOLLOW THE SAME SYNTAX
# callback functions that update data
@app.callback(
    [# OUTPUT: What is changed by the callback. They are the function returns in order
     Output("selected-station", "figure"),
     Output("graph-slider", "min"),
     Output("graph-slider", "max"),
     Output("graph-slider", "marks"),
     Output("graph-slider", "value")
    ],
     #INPUT: Anything that triggers the callback. They are the function parameters in order
     [ #INPUT: Anything that triggers the callback. They are the function parameters in order
      Input("chart-dropdown", "value"),
      Input("graph-slider", "value"),
      ]+[Input(str(streamflow_metadata.iloc[i]['Site_name'])+'_Streamflow_map_token', "n_clicks") 
       for i in range(len(streamflow_metadata))]
       +[Input(str(rainfall_metadata.iloc[i]['Site_name'])+'_Rainfall_map_token', "n_clicks") 
        for i in range(len(rainfall_metadata))]
       # TODO: Add weather markers,
    ) # STATE: An optional parameter that is used by the callback but does not trigger it. They follow the inputs as function parameters
def display_selected_data(chart_dropdown, years, *args):
    new_years = years[:]
    streamflow_args = args[:len(streamflow_markers)]
    rainfall_args = args[len(streamflow_markers):]
    arg_data = {"Streamflow": streamflow_args,
                "Rainfall": rainfall_args}
    for i in range(len(update_record['Streamflow'])):
        if args[i] == None:
            update_record['Streamflow'][i]
        elif arg_data['Streamflow'][i] > update_record['Streamflow'][i]:
            update_record['Streamflow'][i] += 1
            graph_type[0] = 'Streamflow'
            current_station[0] = 'm3ps'
            current_station[1] = i
            year_min = streamflow_frames[current_station[0]][current_station[1]].dropna().index.min().year
            year_max = streamflow_frames[current_station[0]][current_station[1]].dropna().index.max().year
            new_years = [year_min, 
                         year_max]
    for i in range(len(update_record['Rainfall'])):
        if args[len(streamflow_args)+i] == None:
            update_record['Rainfall'][i] = 0
        elif arg_data['Rainfall'][i] > update_record['Rainfall'][i]:
            update_record['Rainfall'][i] += 1
            graph_type[0] = 'Rainfall'
            current_station[0] = 'RNF_in'
            current_station[1] = i
            year_min = rainfall_frames[current_station[0]][current_station[1]].index.min().year
            year_max = rainfall_frames[current_station[0]][current_station[1]].index.max().year
            new_years = [year_min,
                         year_max]
    """
    for i in range(len(update_record['Weather'])):
        if args[len(streamflow_args)+len(rainfall_args)+i] == None:
            update_record['Weather'] = 0
        elif arg_data['Weather'][i] > update_record['Weather'][i]:
            update_record['Weather'][i] += 1
            graph_type[0] = 'Weather'
            current_station[0] = 'SlrMJ_Tot'
            current_station[1] = i
            year_min = rainfall_frames[current_station[0]][current_station[1]].index.min().year
            year_max = rainfall_frames[current_station[0]][current_station[1]].index.max().year
            new_years = [year_min,
                         year_max]
    """
    # Convert decimal years to days
    if graph_type[0] == "Streamflow":
        base0 = datetime(int(np.floor(new_years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
        base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0]))) # timedelta returns a time change
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        mask = (streamflow_frames[current_station[0]][current_station[1]].index > result0) & (streamflow_frames[current_station[0]][current_station[1]].index < result1)
        filtered_data = streamflow_frames[current_station[0]][current_station[1]].loc[mask]
        new_fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[0]], 
                                         line=go.scatter.Line(color='rebeccapurple'),
                                         name='Scatter'),
                              go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[0]+'_Linear_fit'], 
                                         line=go.scatter.Line(color='royalblue', 
                                                              dash='dash'),
                                         name='Trendline')
                              ], 
                        )

        new_fig.update_layout(title_text='Streamflow plot for ' + str(streamflow_metadata.iloc[current_station[1]]['Site_name']) + ' station.')
        year_min = streamflow_frames[current_station[0]][current_station[1]].index.min().year
        year_max = streamflow_frames[current_station[0]][current_station[1]].index.max().year
    elif graph_type[0] == "Rainfall":
        base0 = datetime(int(np.floor(new_years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
        base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0]))) # timedelta returns a time change
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        mask = (rainfall_frames[current_station[0]][current_station[1]].index > result0) & (rainfall_frames[current_station[0]][current_station[1]].index < result1)
        filtered_data = rainfall_frames[current_station[0]][current_station[1]].loc[mask]
        new_fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[0]], 
                                         line=go.scatter.Line(color='rebeccapurple'),
                                         name='Scatter'),
                              go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[0]+'_Linear_fit'], 
                                         line=go.scatter.Line(color='royalblue', 
                                                              dash='dash'),
                                         name='Trendline')
                              ], 
                        )
        new_fig.update_layout(title_text='Rainfall plot for ' + str(rainfall_metadata.iloc[current_station[1]]['Site_name']) + ' station.')
        year_min = rainfall_frames[current_station[0]][current_station[1]].index.min().year
        year_max = rainfall_frames[current_station[0]][current_station[1]].index.max().year
    else:
        """
        base0 = datetime(int(np.floor(new_years[0])), 1, 1)
        base1 = base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0]))) # timedelta returns a time change
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        mask = (weather_frames[current_station[0]][current_station[1]].index > result0) & (weather_frames[current_station[0]][current_station[1]].index < result1)
        filtered_data = weather_frames[current_station[0]][current_station[1]].loc[mask]
        new_fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[0]], 
                                         line=go.scatter.Line(color='rebeccapurple'),
                                         name='Scatter'),
                              go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[0]+'_Linear_fit'], 
                                         line=go.scatter.Line(color='royalblue', 
                                                              dash='dash'),
                                         name='Trendline')
                              ], 
                        )
        new_fig.update_layout(title_text='Weather plot for ' + str(weather_metadata.iloc[current_station[1]]['Site_name']) + ' station.')
        year_min = weather_frames[current_station[0]][current_station[1]].index.min().year
        year_max = weather_frames[current_station[0]][current_station[1]].index.max().year
        """
        new_fig = go.Figure()
        new_years = [2000, 2025]
        base0 = datetime(int(np.floor(new_years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
        base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0])))
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        new_fig.update_layout(transition_duration=500)
        year_min = new_years[0]
        year_max = new_years[1]
    new_marks={
        str(year): {
            "label": str(year),
            "style": {"color": "#7fafdf"},
        }
        for year in range(year_min, year_max)
    }
    return new_fig, year_min, year_max, new_marks, new_years
    
@app.callback(
    Output("download-dataframe-csv", "data"), 
    [Input("selected-download-btn", "n_clicks")],
    [State("graph-slider", "value")],
    prevent_initial_call=True
    )
def download_func(n_clicks, years):
    station_name = current_station[0]
    station_index = current_station[1]
    # Takes the Input and State values (in order) from above. 
    # n_clicks comes from the "n_clicks" in Input. 
    base0 = datetime(int(np.floor(years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
    base1 = datetime(int(np.floor(years[1])), 1, 1)
    result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(years[0] - np.floor(years[0]))) # timedelta returns a time change
    result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(years[1] - np.floor(years[1])))
    if station_name == "Streamflow":
        mask = (streamflow_frames[station_name][station_index].index > result0) & (streamflow_frames[station_name][station_index].index < result1)
        return dcc.send_data_frame(streamflow_frames[station_name][station_index].loc[mask].to_csv, str(streamflow_metadata.iloc[station_index]['Site_name'])+"_data.csv")
    elif station_name == "Rainfall":
        mask = (rainfall_frames[station_name][station_index].index > result0) & (rainfall_frames[station_name][station_index].index < result1)
        return dcc.send_data_frame(rainfall_frames[station_name][station_index].loc[mask].to_csv, str(rainfall_metadata.iloc[station_index]['Site_name'])+"_data.csv")

    
if __name__ == '__main__':     
    app.run_server(debug=False)
