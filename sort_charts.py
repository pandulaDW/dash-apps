import pandas as pd
import os
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_auth
import plotly.graph_objs as go
import json

app = dash.Dash()
server = app.server

cols = ['All: Net Profit', 'All: ProfitFactor', 'All: TS Index']

# Function to convert the text files to dataframes
def main_func(list_txtfiles, path_text):
    df_list_final = []
    counter = 0
    list_dir = list_txtfiles

    for item in range(len(cols)):
        df_list = []
        for i in range(len(list_dir)):
            df = pd.read_csv("{}/{}".format(path_text, list_dir[i]), usecols=[cols[item]])
            df.sort_values(cols[item], ascending=False, inplace=True)
            df.reset_index(drop=True, inplace=True)
            df.columns = ["{}".format(list_dir[i]).split(".")[0]]
            df_list.append(df)
            counter += 1
        df_list_final.append(df_list)

    data = []

    for i in range(len(df_list_final)):
        df = pd.concat(df_list_final[i], axis=1)
        data.append(df)

    return data

# Filtering function
def func(data, condition):
    s1 = list(map(lambda x : x >= data['Base'].mean(), data.apply(np.median, axis=0)))
    if condition == 'base_higher':
        df = data.loc[:,s1].copy()
    elif condition == 'base_lower':
        s1 = [not i for i in s1]
        df = data.loc[:,s1].copy()
    else :
        df = data.copy()

    return df

# Creating the options for the drop downs
labels = [i.split(': ')[1] for i in cols]
data_options = []

for i, label in list(enumerate(labels)):
    data_options.append({'label':label, 'value':i})

filer_options = [{'label': 'Higher than Base', 'value':'base_higher'}, {'label': 'Lower than Base', 'value':'base_lower'},
                 {'label': 'Reset', 'value':'reset'}]

# layout of the app
app.layout = html.Div([
             html.Div([dcc.Input(
                 id='number-in',
                 value="Enter your filepath here",
                 style={'fontSize':12}
             ),
             html.Button(
                 id='submit-button',
                 n_clicks=0,
                 children='Submit',
                 style={'fontSize':14, 'margin-left': 12}
             ),
             html.P()]),
             html.Div([
                dcc.Dropdown(id='df-picker', options=data_options,
                            value=0)], style={'width':'48%', 'display':'inline-block'}),
                html.Div([
                   dcc.Dropdown(id='condition', options=filer_options,
                               value='reset')], style={'width':'48%', 'display':'inline-block'}),
                dcc.Graph(id='graph', style={'height': 600}),
                html.Div(id='intermediate-value', style={'display': 'none'})
])

@app.callback(
    Output('intermediate-value', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('number-in', 'value')])
def output(n_clicks, text):
    list_dir = os.listdir(text)
    return json.dumps(list_dir)

@app.callback(Output('graph', 'figure'),
             [Input('df-picker', 'value'),
             Input('condition', 'value'),
             Input('intermediate-value', 'children')],
             [State('number-in', 'value')])
def update_figure(selected_df, condition, json_list, path_text):

    list_txtfiles = json.loads(json_list)
    data = main_func(list_txtfiles=list_txtfiles, path_text=path_text)
    df = data[selected_df]
    df = func(df, condition)

    traces = []

    for i in range(len(df.columns)):
        traces.append(go.Scatter(
            x = df.index,
            y = df.iloc[:,i],
            mode = 'lines',
            name=df.columns[i]
        ))

    return {'data': traces,
            'layout': go.Layout(title='Dashboard',
                                    xaxis={'title':'Index'},
                                    yaxis={'title':labels[selected_df]})}

if __name__ == '__main__':
    app.run_server(debug=True)
