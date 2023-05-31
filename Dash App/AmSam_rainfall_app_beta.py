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

# Read in files
with open('Data/MasterStationList.txt', 'r') as master_station_file:
    station_names = [line.strip() for line in master_station_file.readlines()]

with open('Data/Streamflow/DataFileNames.txt', 'r') as streamflow_station_file:
    streamflow_files = [line.strip() for line in streamflow_station_file.readlines()]
    
with open('Data/Weather/DataFileNames.txt', 'r') as weather_station_file:
    weather_files = [line.strip() for line in weather_station_file.readlines()]


streamflow_name_dict = {}
weather_name_dict = {}

# Read in column name files and build dictionaries
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

# Organise data
for key, columns in streamflow_name_dict.items():
    streamflow_frames[key] = {column: pd.read_csv('Data/Streamflow/'+str(key)+'_'+str(column)+'_processed.csv', index_col="DateTime", infer_datetime_format=True, parse_dates=True) for column in columns}

for key, columns in weather_name_dict.items():
    weather_frames[key] = {column: pd.read_csv('Data/Weather/'+str(key)+'_'+str(column)+'_processed.csv', index_col="DateTime", infer_datetime_format=True, parse_dates=True) for column in columns}

# Create map markers
streamflow_markers = [dl.CircleMarker(center=[streamflow_metadata.iloc[i]["LAT"], streamflow_metadata.iloc[i]["LON"]], color='red', id=str(streamflow_metadata.iloc[i]['Site_name']+'_Streamflow_map_token'), children=dl.Tooltip("Streamflow: "+str(streamflow_metadata.iloc[i]['Site_name']))) for i in range(len(streamflow_metadata))]
weather_markers = [dl.CircleMarker(center=[weather_metadata.iloc[i]["LAT"], weather_metadata.iloc[i]["LON"]], color='blue', id=str(weather_metadata.iloc[i]['Site_name']+'_Weather_map_token'), children=dl.Tooltip("Weather: "+str(weather_metadata.iloc[i]['Site_name']))) for i in range(len(weather_metadata))]

# Start the app
app = Dash(
    __name__,
    # Use a style from dash bootstrap components
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.title = "Territory of American Samoa: Weather Station and Streamflow Data"
server = app.server

# Where the map will be centered initially
bound_name = 'Vaipito'

# App webpage code/organisation
# Note: a dbc.Container is a wrapper object that allows for "fluid" fitting of the objects with the appropriate screen resolution.
app.layout = dbc.Container(
    children=[
        html.Div(
            id="root",
            children=[
                dbc.Container(
                    children=[
                        dbc.Row(
                            children=[
                                html.H4(children="Public Watershed Data for American Samoa", style={'textAlign': 'center', 'color': 'White'}),                      
                                html.P(
                                    id="title-description",
                                    children="Information about water availability and movement is fundamental to ensuring economic well-being, protecting lives and property, and promoting sustainable use of water resources. On remote oceanic islands, resource limitations can be a defining factor in an island’s habitability. Therefore, it is essential to maintain an up-to-date understanding of rainfall, weather, surface water, and groundwater in these settings, especially in the face of a changing climate and uncertain future. Starting in the 1950’s weather monitoring and stream gauging services for the territory of American Samoa were performed by the United States Geological Survey (USGS). However, in 2008 this program was discontinued. Because of the critical nature of these datasets, the University of Hawaii (UH) Water Resources Research Center (WRRC) and the territory’s sole water utility, American Samoa Power Authority (ASPA), have entered into a cooperative agreement for the purpose of developing a new weather station, stream gauging, and aquifer monitoring network.",
                                    style={"border":"2px gray solid", 'border-radius': '10px', 'backgroundColor':'White'}
                                    ),
                                ],
                            ),
                        ],
                    fluid=True
                    ),
                dbc.Container(
                    children=[
                        dbc.Row(
                            children=[
                                dbc.Col(
                                    children=[                    
                                        html.H5(children="Weather Stations", style={'color': 'White'}),
                                        html.P(
                                            id="weather-description",
                                            children="The ASPA-WRRC weather station (Wx) network consists of seven solar powered Spectrum Watchdog or Campbell Scientific stations which record data on 15 minute intervals and transmit data via WiFi. The weather stations are sited in the best available locations given the limited amount of open space on the island and stations cover an elevation range from near sea level to 475 m at the peak of Mt. Alava.",
                                            style={"border":"2px gray solid", 'border-radius': '10px', 'backgroundColor':'White'},
                                            ),
                                        ],
                                    ),
                                dbc.Col(
                                    children=[
                                        html.H5(children="Stream Gauges", style={'color': 'White'}),
                                        html.P(
                                            id="gauge-description",
                                            children="The ASPA-WRRC stream gauge network currently consists of eight gauges located on different streams throughout Tutuila. Stream gauges are instrumented with stainless steel HOBO brand water-level logging pressure transducers installed in durable steel housings, which are permanently mounted to stream-side bridges or bedrock outcroppings.",
                                            style={"border":"2px gray solid", 'border-radius': '10px', 'backgroundColor':'White'},
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            ],
                    fluid=True
                    ),
                    dbc.Row(
                        children=[
                            dbc.Col(
                                children=[
                                    dbc.Container(
                                        children=[
                                            html.Div([
                                                html.P(
                                                    children="TO BEGIN: Select a weather station (blue circle) or streamflow station (red circle).",  
                                                    id="map-description",
                                                    style={'color': 'White'}),
                                                    # Code for the map
                                                    dl.Map(
                                                        children=[dl.TileLayer(), dl.LayerGroup(weather_markers), dl.LayerGroup(streamflow_markers)],
                                                        bounds=[[(weather_metadata.query("Site_name == @bound_name")["LAT"].values+0.3)[0], (weather_metadata.query("Site_name == @bound_name")["LON"].values+0.3)[0]],
                                                                [(weather_metadata.query("Site_name == @bound_name")["LAT"].values-0.3)[0], (weather_metadata.query("Site_name == @bound_name")["LON"].values-0.3)[0]]],
                                                        style={'width': '915px', 'height':'915px', 'align':'center'},
                                                        id="leaflet-map")
                                                    ],
                                                ),
                                            ],
                                        fluid=True,
                                    ),
                                ],
                            ),
                            dbc.Col(
                                children=[
                                    dbc.Container(
                                        children=[
                                            html.Div([
                                                html.P(
                                                    id="chart-selector",
                                                    children=["Select a data option from the menu below: "],
                                                    style={'color': 'White'}
                                                    ),
                                                # Char dropdown selection
                                                dcc.Dropdown(
                                                    options=[
                                                        {"label": "Select a station from the map to begin",
                                                         "value": "N/A"},
                                                        ],
                                                    value="N/A",
                                                    id="chart-dropdown",
                                                    ),
                                                dcc.Graph(  
                                                    id="selected-station",
                                                    figure=go.Figure()
                                                    ),
                                                html.P(id="range-descriptor", 
                                                       children=["Adjust the displayed data (notches demarked by year)"],
                                                       style={'color':'White'}
                                                       ),
                                                # Creates the year selector
                                                dcc.RangeSlider(
                                                    min=2000,
                                                    max=2025,
                                                    value = [2000, 2025],
                                                    id="graph-slider",
                                                    ),
                                                html.P(id="button-descriptor",
                                                       children=["Click the button to download only the displayed data."],
                                                       style={'color':'White'}
                                                       ),
                                                html.Button("Download", 
                                                            id="selected-download-btn"),
                                                # A download object enabling file downloads
                                                dcc.Download(id="download-dataframe-csv")
                                                ],
                                                ),
                                            # All the logos
                                            dbc.Container(
                                                children=[
                                                    dbc.Row(
                                                        children=[
                                                            html.H6(children="Funding", style={"color": "White"}),
                                                            html.P(
                                                                id="funding-description",
                                                                children="Funding for this project was provided by American Samoa EPA, American Samoa Power Authority (ASPA), and US EPA Region IX Making a Visible Difference Project no. C00543, the Pacific Regional Integrated Sciences and Assessments (Pacific RISA) - NOAA Climate Program Office grant no. NA10OAR4310216, and the USGS Water Resources Research Institute Program (WRRIP).",
                                                                style={"border":"2px gray solid", 'border-radius': '10px', 'backgroundColor':'White'},
                                                                ),
                                                            ],
                                                        ),
                                                    dbc.Col(
                                                        children=[
                                                            html.A(
                                                                html.Img(id="Am-Sam-logo", src=app.get_asset_url("Seal_of_American_Samoa.svg.png"), style={'height':'100%', 'width':'10%'}),
                                                                href="https://www.americansamoa.gov/"),
                                                            html.A(
                                                                html.Img(id="PI-CASC-logo", src=app.get_asset_url("picasc_logo_border.png"), style={'height':'100%', 'width':'10%'}),
                                                                href="https://pi-casc.soest.hawaii.edu/"),
                                                            html.A(
                                                                html.Img(id="USGS-logo", src=app.get_asset_url("USGS_logo_green.svg.png"), style={'height':'100%', 'width':'15%'}),
                                                                href="https://www.usgs.gov/"),
                                                            ],
                                                        ),
                                                    ],
                                                fluid=True,
                                                ),
                                            ],
                                        fluid=True,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    dbc.Row(
                        children=[
                            html.A(
                                html.Img(id="monitoring-instruments", src=app.get_asset_url("monitoring_instruments4.png"), style={'width': '33%'}),
                                style={'textAlign': 'center'}
                                ),
                            ],
                        ),
                    ],
            ),
        ],
    fluid=True,
    style={'backgroundColor': '#5D5C61'}
)
  
# TODO: Pull new data and update every 15 minutes TBD where/how this will work.

# Internal mutable which will be used by the app.
update_record = {"Streamflow": np.zeros((len(streamflow_metadata))),
                 "Weather": np.zeros((len(weather_metadata)))}
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
    '''
    Update the graph and range slider based on station selection
    
    Parameters
    ----------
    
    The parameters are in the order of the [Input()] objects in the preceeding callback.
    
    chart_dropdown: str
        comes from the chart-dropdown value and is used to access the appropriate data column.
    years: list
        A list of two integers which represents the selected lower and upper bounds on the range slider.
    chart_options: dict
        A dictionary with key value pairs where the key is the text displayed in the dropdown,
        and the value is an internal value passed when the option in the dropdown is chosen. 
    args: 
        A tuple which contains the number of clicks for each station. 
        This is variable so that stations may be added or removed at a whim.
    
    Returns
    -------
    
    The return values are in the order of the [Output()] objects in the preceeding callback.
    
    new_fig: go.Figure() object
        This contains either the new graph or an empty go.Figure() if there is no data.
    year_min: int
        The absolute minimum value of the date range slider.
    year_max: int
        The absolute maximum value of the date range slider.
    new_marks: list
        A list of integers indicating what tick marks should be available on the date range slider.
    chart_options: dict
        A dictionary with key value pairs where the key is the text displayed in the dropdown,
        and the value is an internal value passed when the option in the dropdown is chosen.
    '''
    
    # Parse the inputs for use
    new_years = years[:]
    streamflow_args = args[:len(streamflow_markers)]
    weather_args = args[len(streamflow_markers):]
    arg_data = {"Streamflow": streamflow_args,
                "Weather": weather_args}
    
    # Determine if a new station was selected
    
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
    
    
    # If the station is a streamflow station
    if graph_type[0] == "Streamflow":
        # This is triggered when the station is updated
        if chart_dropdown == "N/A" or not (chart_dropdown in streamflow_name_dict[current_station[0]]):
            # Determine which data is available
            column_names = streamflow_name_dict[current_station[0]]
            current_station[1] = column_names[0]
            chart_options = [
                {"label": name,
                 "value": name} for name in column_names
                ]
        else:
            current_station[1] = chart_dropdown
            
        # Run a calculation to determine the range slider options
        base0 = datetime(int(np.floor(new_years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
        base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0]))) # timedelta returns a time change
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        
        # Only use data that is within the selected options of the range slider
        mask = (streamflow_frames[current_station[0]][current_station[1]].index > result0) & (streamflow_frames[current_station[0]][current_station[1]].index < result1)
        filtered_data = streamflow_frames[current_station[0]][current_station[1]].loc[mask]
        
        # Create the new figure
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
            
        # Run a calculation to determine the range slider options
        base0 = datetime(int(np.floor(new_years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
        base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0]))) # timedelta returns a time change
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        
        # Only use data that is within the selected options of the range slider
        mask = (weather_frames[current_station[0]][current_station[1]].index > result0) & (weather_frames[current_station[0]][current_station[1]].index < result1)
        filtered_data = weather_frames[current_station[0]][current_station[1]].loc[mask]
        
        # Create the new figure
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
        # Create an empty go.Figure()
        new_fig = go.Figure()
        new_years = [2000, 2025]
        base0 = datetime(int(np.floor(new_years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
        base1 = datetime(int(np.floor(new_years[1])), 1, 1)
        result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(new_years[0] - np.floor(new_years[0])))
        result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(new_years[1] - np.floor(new_years[1])))
        new_fig.update_layout(transition_duration=500)
        year_min = new_years[0]
        year_max = new_years[1]
    
    # Create the new tick marks
    new_marks={
        str(year): {
            "label": str(year),
            "style": {"color": "#7fafdf"},
        }
        for year in range(year_min, year_max+1)
    }
    return new_fig, year_min, year_max, new_marks, new_years, chart_options
    
@app.callback(
    Output("download-dataframe-csv", "data"), 
    [Input("selected-download-btn", "n_clicks")],
    [State("graph-slider", "value")],
    prevent_initial_call=True
    )
def download_func(n_clicks, years):
    '''
    A function to download the selected data
    
    Parameters
    ----------
    
    The parameters are in the order of the [Input()] objects in the preceeding callback.
    
    n_clicks: int
        This parameter is not used, but its status as an input allows it to trigger this callback.
    years: list
        A list of two integers which represents the selected lower and upper bounds on the range slider.
    
    Returns
    -------
    
    The return values are in the order of the [Output()] objects in the preceeding callback.
    
    A dcc.send_data_frame() function call containing the appropriately masked dataframes and a file name for the download.
    '''
    
    # Parse the inputs
    station_name = current_station[0]
    station_column = current_station[1]
    
    # Run a calculation to determine the range slider options
    base0 = datetime(int(np.floor(years[0])), 1, 1) # Establishes the beginning of the year for given year[i]
    base1 = datetime(int(np.floor(years[1])), 1, 1)
    result0 = base0 + timedelta(seconds=(base0.replace(base0.year+1) - base0).total_seconds()*(years[0] - np.floor(years[0]))) # timedelta returns a time change
    result1 = base1 + timedelta(seconds=(base1.replace(base1.year+1) - base1).total_seconds()*(years[1] - np.floor(years[1])))
    
    # Determine the outputs
    if graph_type[0] == "Streamflow":
        mask = (streamflow_frames[station_name][station_column].index > result0) & (streamflow_frames[station_name][station_column].index < result1)
        return dcc.send_data_frame(streamflow_frames[station_name][station_column].loc[mask].to_csv, str(station_name)+'_'+str(station_column)+"_data.csv")
    elif graph_type[0] == "Weather":
        mask = (weather_frames[station_name][station_column].index > result0) & (weather_frames[station_name][station_column].index < result1)
        return dcc.send_data_frame(weather_frames[station_name][station_column].loc[mask].to_csv, str(station_name)+'_'+str(station_column)+"_data.csv")

    
if __name__ == '__main__':     
    app.run_server(debug=False)
