# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 11:16:53 2020

@author: Satakshi Tiwari
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import urllib

from datetime import datetime

def getMarks(start, end, df, Nth=30):
    result = {}
    for i, date in enumerate(df['date'].unique()):
        if(i%Nth == 1):
            # Append value to dict
            result[np.datetime_as_string(date, unit='D')] = np.datetime_as_string(date, unit='D')
    return result

## External stylesheets to make sure the row and column 
## from bootstrap library work
external_stylesheets = [dbc.themes.BOOTSTRAP]

app = dash.Dash(external_stylesheets=external_stylesheets)

## Read file
outfilename = r"../Data/owid-covid-data.xlsx"
url_of_file = "https://covid.ourworldindata.org/data/owid-covid-data.xlsx"
urllib.request.urlretrieve(url_of_file, outfilename)
df = pd.read_excel(r"../Data/owid-covid-data.xlsx")

## Remove data about World - we will be looking at individual locations
df = df[df['location']!='World']

## Fill 0 if new cases on a day was null
df['new_cases'] = df['new_cases'].fillna(0)

## Sort by date so we have in a proper order
df = df.sort_values(by=['date'])

## As we will be visualizing on month instead of date; create column
## for month and year
df['monthYear'] = pd.to_datetime(df['date']).dt.strftime("%B-%Y")

## Will need to map the month year column to a number as plotly
## graphs don't work with strings in background
dateMapping = {i:(str(datetime.strptime(j,'%Y-%m').strftime('%B-%Y'))) for i, j in enumerate(pd.to_datetime(df['date']).dt.strftime("%Y-%m").unique().tolist())}
d = {k: oldk for oldk, k in dateMapping.items()}

df["key"] = df['monthYear'].map(d)

## to limit our scale
worldPop = 16000000

app.layout = html.Div([
    html.Div([
        dcc.Loading([
            dcc.Graph(id='my-graph'),
            ])
        ]),
    html.Div([
        dcc.Slider(
        id='date-slider',
        min = 0,
        max = len(pd.to_datetime(df['date']).dt.strftime("%Y-%m").unique().tolist()),
        value = 1,
        marks = {i:(str(datetime.strptime(j,'%Y-%m').strftime('%B-%Y'))) for i, j in enumerate(pd.to_datetime(df['date']).dt.strftime("%Y-%m").unique().tolist())}
        ),
        ]),
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Loading([
                        dcc.Graph(id='bar-graph')
                        ])
                    ])
                ],
                width=6,
                ),
            dbc.Col([
                html.Div([
                    dcc.Loading([
                        dcc.Graph(id='bar-graph2')
                        ])
                    ]),
                ],
                width=6,
                )
            ])
        ]),
    ])

@app.callback(
    [dash.dependencies.Output('my-graph', 'figure'),
     dash.dependencies.Output('bar-graph', 'figure'),
     dash.dependencies.Output('bar-graph2', 'figure'),
     ],
    [dash.dependencies.Input('date-slider', 'value')])
def update_output(value):
    dataDF = df[(df['key']>=0)&(df['key']<=value)][['key',
                                                   'location',
                                                   'new_cases',
                                                   'new_deaths']]
    dataDF = dataDF.groupby(['location']).agg({'new_cases':'sum',
                                               'new_deaths':'sum'}).reset_index()
    dataDF = dataDF.sort_values('new_cases',ascending=False)
    
    fig = go.Figure(
        data=go.Choropleth(
            locations = dataDF['location'], # Spatial coordinates
            z = dataDF['new_cases'], # Data to be color-coded
            locationmode = 'country names', # set of locations match entries in `locations`
            colorscale = 'Reds',
            zmin = 0,
            zmax = worldPop,
        )   
    )
    fig.update_layout(
    title={
        'text': "Global Spread of Coronavirus",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    
    fig2 = go.Figure([
        go.Bar(
            x=dataDF['location'].head(5), 
            y=dataDF['new_cases'].head(5)
            )
        ])
    fig2.update_layout(
    title={
        'text': "5 counties with most cases",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})
    
    dataDF = dataDF.sort_values('new_deaths',ascending=False)
    
    fig3 = go.Figure([
        go.Bar(
            x=dataDF['location'].head(5), 
            y=dataDF['new_deaths'].head(5)
            )
        ])
    fig3.update_layout(
    title={
        'text': "5 counties with most deaths",
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})

    return fig, fig2, fig3

if __name__ == '__main__':
    app.run_server(debug=True)
