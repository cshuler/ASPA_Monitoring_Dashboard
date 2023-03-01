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
from dash import Dash, html, dcc
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
                                html.H3(children='''
                                         Station map
                                         '''),
                                dcc.Graph(id='Map 2',
                                          figure=map_fig_2
                                          ),
                                html.H3(children='''Figures by station'''
                                         ),
                                dcc.Graph(id='0',
                                          figure=rainfall_figures[0]
                                          ),
                                dcc.Graph(id='1',
                                          figure=rainfall_figures[1]
                                          ),
                                dcc.Graph(id='2',
                                          figure=rainfall_figures[2]
                                          ),
                                dcc.Graph(id='3',
                                          figure=rainfall_figures[3]
                                          )
                               ]
                     )


if __name__ == '__main__':     
    app.run_server(debug=False)
