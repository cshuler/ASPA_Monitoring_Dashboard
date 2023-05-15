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


streamflow_metadata = pd.read_csv('Data/Streamflow/Streamflow_Station_Metadata.csv')
weather_metadata = pd.read_csv('Data/Weather/Weather_Station_Metadata.csv')

with open('Data/MasterStationList.txt', 'r') as master_station_file:
    station_names = [line.strip() for line in master_station_file.readlines()]

with open('Data/Streamflow/DataFileNames.txt', 'r') as streamflow_station_file:
    streamflow_files = [line.strip() for line in streamflow_station_file.readlines()]
    
with open('Data/Weather/DataFileNames.txt', 'r') as weather_station_file:
    weather_files = [line.strip() for line in weather_station_file.readlines()]


streamflow_name_dict = {}
weather_name_dict = {}


for i in range(len(weather_metadata)):
    location_name = str(weather_metadata.iloc[i]['Site_name'])
    with open('Data/Weather/'+location_name+"_column_names.txt", 'r') as fileHandle:
        columnNames = [line.strip() for line in fileHandle.readlines()]
        weather_name_dict[location_name] = columnNames
        
for i in range(len(streamflow_metadata)):
    location_name = str(streamflow_metadata.iloc[i]['Site_name'])
    with open('Data/Streamflow/'+location_name+"_column_names.txt", 'r') as fileHandle:
        columnNames = [line.strip() for line in fileHandle.readlines()]
        streamflow_name_dict[location_name] = columnNames

streamflow_frames = {}
weather_frames = {}

for key, columns in streamflow_name_dict.items():
    streamflow_frames[key] = {column: pd.read_csv('Data/Streamflow/'+str(key)+'_'+str(column)+'_processed.csv', index_col="DateTime", infer_datetime_format=True, parse_dates=True) for column in columns}

for key, columns in weather_name_dict.items():
    weather_frames[key] = {column: pd.read_csv('Data/Weather/'+str(key)+'_'+str(column)+'_processed.csv', index_col="DateTime", infer_datetime_format=True, parse_dates=True) for column in columns}

streamflow_markers = [dl.CircleMarker(center=[streamflow_metadata.iloc[i]["LAT"], streamflow_metadata.iloc[i]["LON"]], color='red', id=str(streamflow_metadata.iloc[i]['Site_name']+'_Streamflow_map_token'), children=dl.Tooltip("Streamflow: "+str(streamflow_metadata.iloc[i]['Site_name']))) for i in range(len(streamflow_metadata))]
weather_markers = [dl.CircleMarker(center=[weather_metadata.iloc[i]["LAT"], weather_metadata.iloc[i]["LON"]], color='blue', id=str(weather_metadata.iloc[i]['Site_name']+'_Weather_map_token'), children=dl.Tooltip("Weather: "+str(weather_metadata.iloc[i]['Site_name']))) for i in range(len(weather_metadata))]

app = Dash(
    __name__,
    # Use a style from dash bootstrap components
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.title = "American Samoa Weather Data"
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
                    children="A data portal for data collected by ... in American Samoa",
                    ),
                ],
                ),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.P(
                        "To begin, select a weather (blue) or streamflow (red) station.",  
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
                    dl.Map(children=[dl.TileLayer(), dl.LayerGroup(weather_markers), dl.LayerGroup(streamflow_markers)],
                           bounds=[[(weather_metadata.query("Site_name == @bound_name")["LAT"].values+0.3)[0], (weather_metadata.query("Site_name == @bound_name")["LON"].values+0.3)[0]],
                                   [(weather_metadata.query("Site_name == @bound_name")["LAT"].values-0.3)[0], (weather_metadata.query("Site_name == @bound_name")["LON"].values-0.3)[0]]],
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
                        children=["Select a data option from the menu below: "],
                        ),
                    dcc.Dropdown(
                        options=[
                            {"label": "Select a station to begin",
                             "value": "N/A"},
                            ],
                        value="N/A",
                        id="chart-dropdown",
                        ),
                    dcc.Graph(  
                        id="selected-station",
                        figure=go.Figure()
                        ),
                    dcc.RangeSlider(
                        min=2000,
                        max=2025,
                        value = [2000, 2025],
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
     Output("graph-slider", "value"),
     Output("chart-dropdown", "options")
    ],
     #INPUT: Anything that triggers the callback. They are the function parameters in order
     [ #INPUT: Anything that triggers the callback. They are the function parameters in order
      Input("chart-dropdown", "value"),
      Input("graph-slider", "value"),
      Input("chart-dropdown", "options")
      ]+[Input(str(streamflow_metadata.iloc[i]['Site_name'])+'_Streamflow_map_token', "n_clicks") 
       for i in range(len(streamflow_metadata))]
       +[Input(str(weather_metadata.iloc[i]['Site_name'])+'_Weather_map_token', "n_clicks") 
        for i in range(len(weather_metadata))]
       # TODO: Add weather markers,
    ) # STATE: An optional parameter that is used by the callback but does not trigger it. They follow the inputs as function parameters
def display_selected_data(chart_dropdown, years, chart_options, *args):
    new_years = years[:]
    streamflow_args = args[:len(streamflow_markers)]
    weather_args = args[len(streamflow_markers):]
    arg_data = {"Streamflow": streamflow_args,
                "Weather": weather_args}
    for i in range(len(update_record['Streamflow'])):
        if args[i] == None:
            update_record['Streamflow'][i]
        elif arg_data['Streamflow'][i] > update_record['Streamflow'][i]:
            update_record['Streamflow'][i] += 1
            graph_type[0] = 'Streamflow'
            current_station[0] = streamflow_metadata.iloc[i]['Site_name']

    for i in range(len(update_record['Weather'])):
        if args[len(streamflow_args)+i] == None:
            update_record['Weather'][i] = 0
        elif arg_data['Weather'][i] > update_record['Weather'][i]:
            update_record['Weather'][i] += 1
            graph_type[0] = 'Weather'
            current_station[0] = weather_metadata.iloc[i]['Site_name']
    
    
    # Convert decimal years to days
    if graph_type[0] == "Streamflow":
        if chart_dropdown == "N/A" or not (chart_dropdown in streamflow_name_dict[current_station[0]]):
            column_names = streamflow_name_dict[current_station[0]]
            current_station[1] = column_names[0]
            chart_options = [
                {"label": name,
                 "value": name} for name in column_names
                ]
        else:
            current_station[1] = chart_dropdown
        base0 = datetime(int(np.floor(new_years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
        base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0]))) # timedelta returns a time change
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        mask = (streamflow_frames[current_station[0]][current_station[1]].index > result0) & (streamflow_frames[current_station[0]][current_station[1]].index < result1)
        filtered_data = streamflow_frames[current_station[0]][current_station[1]].loc[mask]
        new_fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[1]], 
                                         line=go.scatter.Line(color='rebeccapurple'),
                                         name='Scatter'),
                              go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[1]+'_Linear_fit'], 
                                         line=go.scatter.Line(color='royalblue', 
                                                              dash='dash'),
                                         name='Trendline')
                              ],
                            layout=dict(xaxis=dict(title='Time'),
                                        yaxis=dict(title=str(current_station[1])+' summed monthly'),
                                                   )
                        )
        new_fig.update_layout(title_text=str(current_station[1])+' plot for ' + str(current_station[0]) + ' station.')
        year_min = streamflow_frames[current_station[0]][current_station[1]].index.min().year
        year_max = streamflow_frames[current_station[0]][current_station[1]].index.max().year
    elif graph_type[0] == "Weather":
        if chart_dropdown == "N/A" or not (chart_dropdown in weather_name_dict[current_station[0]]):
            column_names = weather_name_dict[current_station[0]]
            current_station[1] = column_names[0]
            chart_options = [
                {"label": name,
                 "value": name} for name in column_names
                ]
        else:
            current_station[1] = chart_dropdown
        base0 = datetime(int(np.floor(new_years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
        base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0]))) # timedelta returns a time change
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        mask = (weather_frames[current_station[0]][current_station[1]].index > result0) & (weather_frames[current_station[0]][current_station[1]].index < result1)
        filtered_data = weather_frames[current_station[0]][current_station[1]].loc[mask]
        new_fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[1]], 
                                         line=go.scatter.Line(color='rebeccapurple'),
                                         name='Scatter'),
                              go.Scatter(x=filtered_data.index, 
                                         y=filtered_data[current_station[1]+'_Linear_fit'], 
                                         line=go.scatter.Line(color='royalblue', 
                                                              dash='dash'),
                                         name='Trendline')
                              ],
                            layout=dict(xaxis=dict(title='Time'),
                                        yaxis=dict(title=str(current_station[1])+' summed monthly'),
                                                   )
                            )
        new_fig.update_layout(title_text=str(current_station[1])+' plot for ' + str(current_station[0]) + ' station.')
        year_min = weather_frames[current_station[0]][current_station[1]].index.min().year
        year_max = weather_frames[current_station[0]][current_station[1]].index.max().year
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
    return new_fig, year_min, year_max, new_marks, new_years, chart_options
    
@app.callback(
    Output("download-dataframe-csv", "data"), 
    [Input("selected-download-btn", "n_clicks")],
    [State("graph-slider", "value")],
    prevent_initial_call=True
    )
def download_func(n_clicks, years):
    station_name = current_station[0]
    station_column = current_station[1]
    # Takes the Input and State values (in order) from above. 
    # n_clicks comes from the "n_clicks" in Input. 
    base0 = datetime(int(np.floor(years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
    base1 = datetime(int(np.floor(years[1])), 1, 1)
    result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(years[0] - np.floor(years[0]))) # timedelta returns a time change
    result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(years[1] - np.floor(years[1])))
    if graph_type[0] == "Streamflow":
        mask = (streamflow_frames[station_name][station_column].index > result0) & (streamflow_frames[station_name][station_column].index < result1)
        return dcc.send_data_frame(streamflow_frames[station_name][station_column].loc[mask].to_csv, str(station_name)+'_'+str(station_column)+"_data.csv")
    elif graph_type[0] == "Weather":
        mask = (weather_frames[station_name][station_column].index > result0) & (weather_frames[station_name][station_column].index < result1)
        return dcc.send_data_frame(weather_frames[station_name][station_column].loc[mask].to_csv, str(station_name)+'_'+str(station_column)+"_data.csv")

    
if __name__ == '__main__':     
    app.run_server(debug=False)
