#!/usr/bin/env python
# coding: utf-8

# In[ ]:

#streamlit run AmSam_rainfall_app.py

#set up streamlit app
import pandas as pd
import numpy as np
import os
# import matplotlib.pyplot as plt
# import datetime
import matplotlib.dates as dates
# import scipy
# from scipy import stats
from dash import Dash, html, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

import plotly.io as pio
pio.renderers.default='browser'

station_metadata = pd.read_csv("Rainfall_database_Metadata.csv")
station_metadata = station_metadata[station_metadata['Site name'] != 'Poloa']
station_metadata.drop(columns=['Source', 'Time Resolution'], inplace=True)

datasamples = []
monthly_frames = []
rainfall_figures = []

#get data, resample all to monthly
for i in range(len(station_metadata['Site name'])):
    datasamples.append(pd.read_csv(os.path.join(station_metadata.iloc[i]['Filename'])))
    
    # Check and fix if airport data
    if station_metadata.iloc[i]['Site name'] == 'Airport_PPG':
        station_metadata.iat[i, 0] = 'Airport'
        datasamples[i]['RNF_in'].replace(to_replace=' ', value=np.nan, inplace=True)
        datasamples[i]['RNF_in'] = datasamples[i]['RNF_in'].astype(float)

    datasamples[i]["DateTime"] = pd.to_datetime(datasamples[i]["DateTime"])
    monthly_frames.append(datasamples[i].resample('M', on='DateTime').sum())
    x_dates = monthly_frames[i].index
    x_num = dates.date2num(x_dates)
    trend = np.polyfit(x_num, monthly_frames[i]['RNF_in'], deg=1)
    fitting_function = np.poly1d(trend)
    monthly_frames[i]['Linear_fit'] = fitting_function(x_num)
    fig = go.Figure(data=[go.Scatter(x=monthly_frames[i].index, 
                                     y=monthly_frames[i]['RNF_in'], 
                                     line=go.scatter.Line(color='rebeccapurple'),
                                     name='Scatter'), 
                          go.Scatter(x=monthly_frames[i].index, 
                                     y=monthly_frames[i]['Linear_fit'], 
                                     line=go.scatter.Line(color='royalblue', 
                                                          dash='dash'),
                                     name='Trendline')
                          ], 
                    )
    fig.update_layout(title_text='Rainfall plot for ' + str(station_metadata.iloc[i]['Site name']) + ' station.')
    fig.update_xaxes(title_text='Date')
    fig.update_yaxes(title_text='Rainfall (in.)')
    rainfall_figures.append(fig)

map_fig_2 = px.scatter_geo(station_metadata, 
                           lon=station_metadata["LON"], 
                           lat=station_metadata["LAT"], 
                           hover_name=station_metadata["Site name"]
                           )

map_fig_2.update_layout(title_text="A poorly resolved American Samoa", 
                        geo=dict(resolution=50, 
                                 center=dict(lat=-14.0310, lon=-171.6322), 
                                 projection_scale=100))

# map_fig_2.show()

# begin dash server
app = Dash(__name__)

app.layout = html.Div(children=[html.H1(children='A primitive layout'),
                                html.Button("Download Metadata CSV", 
                                            id="btn-Metadata-csv"),
                                dcc.Download(id="download-Metadata-dataframe-csv"),
                                html.H3(children='''
                                         Station map
                                         '''),
                                dcc.Graph(id='Map 2',
                                          figure=map_fig_2
                                          ),
                                html.H3(children='''Figures by station'''
                                         ),
                                dcc.Graph(id='graph0',
                                          figure=rainfall_figures[0]
                                          ),
                                dcc.RangeSlider(monthly_frames[0].index.min().year,
                                           monthly_frames[0].index.max().year,
                                           step=1,
                                           value=[monthly_frames[0].index.min().year, monthly_frames[0].index.max().year],
                                           marks={str(date): str(date) for date in monthly_frames[0].index.strftime('%m/%Y, %r')},
                                           id='Afono-slider'
                                           ),
                                html.Button("Download Afono CSV", 
                                            id="btn-Afono-csv"),
                                dcc.Download(id="download-Afono-dataframe-csv"),
                                dcc.Graph(id='graph1',
                                          figure=rainfall_figures[1]
                                          ),
                                dcc.RangeSlider(monthly_frames[1].index.min().year,
                                           monthly_frames[1].index.max().year,
                                           step=1,
                                           value=[monthly_frames[1].index.min().year, monthly_frames[1].index.max().year],
                                           marks={str(date): str(date) for date in monthly_frames[1].index.strftime('%m/%Y, %r')},
                                           id='Aasu-slider'
                                           ),
                                html.Button("Download Aasu CSV", 
                                            id="btn-Aasu-csv"),
                                dcc.Download(id="download-Aasu-dataframe-csv"),
                                dcc.Graph(id='graph2',
                                          figure=rainfall_figures[2]
                                          ),
                                dcc.RangeSlider(monthly_frames[2].index.min().year,
                                           monthly_frames[2].index.max().year,
                                           step=1,
                                           value=[monthly_frames[2].index.min().year, monthly_frames[2].index.max().year],
                                           marks={str(date): str(date) for date in monthly_frames[2].index.strftime('%m/%Y, %r')},
                                           id='Vaipito-slider'
                                           ),
                                html.Button("Download Vaipito CSV", 
                                            id="btn-Vaipito-csv"),
                                dcc.Download(id="download-Vaipito-dataframe-csv"),
                                dcc.Graph(id='graph3',
                                          figure=rainfall_figures[3]
                                          ),
                                dcc.RangeSlider(monthly_frames[3].index.min().year,
                                           monthly_frames[3].index.max().year,
                                           step=1,
                                           value=[monthly_frames[3].index.min().year, monthly_frames[3].index.max().year],
                                           marks={str(date): str(date) for date in monthly_frames[3].index.strftime('%m/%Y, %r')},
                                           id='Airport-slider'
                                           ),
                                html.Button("Download Airport CSV", 
                                            id="btn-Airport-csv"),
                                dcc.Download(id="download-Airport-dataframe-csv")
                               ]
                     )

# Afono, Aasu, Vaipito, Airport
# Datasamples is all data (change to 'monthly' for filtered data)                                        
@app.callback(
    Output("download-Afono-dataframe-csv", "data"),
    Input("btn-Afono-csv", "n_clicks"),
    prevent_initial_call=True,
    )
def Afono_func(n_clicks):
    return dcc.send_data_frame(datasamples[0].to_csv, "Afono.csv")


@app.callback(
    Output("download-Aasu-dataframe-csv", "data"),
    Input("btn-Aasu-csv", "n_clicks"),
    prevent_initial_call=True,
    )
def Aasu_func(n_clicks):
    return dcc.send_data_frame(datasamples[1].to_csv, "Aasu.csv")


@app.callback(
    Output("download-Vaipito-dataframe-csv", "data"),
    Input("btn-Vaipito-csv", "n_clicks"),
    prevent_initial_call=True,
    )
def Vaipito_func(n_clicks):
    return dcc.send_data_frame(datasamples[2].to_csv, "Vaipito.csv")


@app.callback(
    Output("download-Airport-dataframe-csv", "data"),
    Input("btn-Airport-csv", "n_clicks"),
    prevent_initial_call=True,
    )
def Airport_func(n_clicks):
    return dcc.send_data_frame(datasamples[3].to_csv, "Airport.csv")


@app.callback(
    Output("download-Metadata-dataframe-csv", "data"),
    Input("btn-Metadata-csv", "n_clicks"),
    prevent_initial_call=True,
    )
def Metadata_func(n_clicks):
    return dcc.send_data_frame(station_metadata.to_csv, "station_metadata.csv")


@app.callback(
    Output("graph0", "figure"),
    Input("Afono-slider", "value"),
    prevent_initial_call=True,   
    )
def update_Afono_slider(value):
    mask = (monthly_frames[0].index > str(value[0])+'-01-01') & (monthly_frames[0].index < str(value[1])+'-12-31')
    filtered_data = monthly_frames[0].loc[mask]
    fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                     y=filtered_data['RNF_in'], 
                                     line=go.scatter.Line(color='rebeccapurple'),
                                     name='Scatter'),
                          go.Scatter(x=filtered_data.index, 
                                     y=filtered_data['Linear_fit'], 
                                     line=go.scatter.Line(color='royalblue', 
                                                          dash='dash'),
                                     name='Trendline')
                          ], 
                    )
    fig.update_layout(transition_duration=500)
    return fig
    
@app.callback(
    Output("graph1", "figure"),
    Input("Aasu-slider", "value"),
    prevent_initial_call=True,   
    )
def update_Aasu_slider(value):
    mask = (monthly_frames[1].index > str(value[0])+'-01-01') & (monthly_frames[1].index < str(value[1])+'-12-31')
    filtered_data = monthly_frames[1].loc[mask]
    fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                     y=filtered_data['RNF_in'], 
                                     line=go.scatter.Line(color='rebeccapurple'),
                                     name='Scatter'), 
                          go.Scatter(x=filtered_data.index, 
                                     y=filtered_data['Linear_fit'], 
                                     line=go.scatter.Line(color='royalblue', 
                                                          dash='dash'),
                                     name='Trendline')
                          ], 
                    )
    fig.update_layout(transition_duration=500)
    return fig


@app.callback(
    Output("graph2", "figure"),
    Input("Vaipito-slider", "value"),
    prevent_initial_call=True,   
    )
def update_Vaipito_slider(value):
    mask = (monthly_frames[2].index > str(value[0])+'-01-01') & (monthly_frames[2].index < str(value[1])+'-12-31')
    filtered_data = monthly_frames[2].loc[mask]
    fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                     y=filtered_data['RNF_in'], 
                                     line=go.scatter.Line(color='rebeccapurple'),
                                     name='Scatter'), 
                          go.Scatter(x=filtered_data.index, 
                                     y=filtered_data['Linear_fit'],
                                     line=go.scatter.Line(color='royalblue', 
                                                          dash='dash'),
                                     name='Trendline')
                          ], 
                    )
    fig.update_layout(transition_duration=500)
    return fig


@app.callback(
    Output("graph3", "figure"),
    Input("Airport-slider", "value"),
    prevent_initial_call=True,   
    )
def update_Airport_slider(value):
    mask = (monthly_frames[3].index > str(value[0])+'-01-01') & (monthly_frames[3].index < str(value[1])+'-12-31')
    filtered_data = monthly_frames[3].loc[mask]
    fig = go.Figure(data=[go.Scatter(x=filtered_data.index, 
                                     y=filtered_data['RNF_in'], 
                                     line=go.scatter.Line(color='rebeccapurple'),
                                     name='Scatter'), 
                          go.Scatter(x=filtered_data.index, 
                                     y=filtered_data['Linear_fit'], 
                                     line=go.scatter.Line(color='royalblue', 
                                                          dash='dash'),
                                     name='Trendline')
                          ], 
                    )
    fig.update_layout(transition_duration=500)
    return fig


if __name__ == '__main__':     
    app.run_server(debug=False)
