import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import numpy as np
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

Np_options = [{'label': 'Profit greater than zero', 'value': 'NP'}, {'label': 'Profit greater than the given value', 'value': 'NP_1'}]

option_values = [{'label': 'Greater than $20,000', 'value': 20000}, {'label': 'Greater than $30,000', 'value': 30000},
                {'label': 'Greater than $40,000', 'value': 40000}]

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    html.Div([
          dcc.Dropdown(id='NP-picker', options=Np_options,
                   value= 'NP')], style={'width':'48%', 'display':'inline-block'}),
       html.Div([
          dcc.Dropdown(id='conditions', options=option_values,
                      value= 30000)], style={'width':'48%', 'display':'inline-block'}),
    html.Div(id='intermediate-value', style={'display': 'none'}),
    html.Div(id='output-table-1'),
    html.Div(id='output-table-2', style={'margin-top': 20})
])

# file upload function
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))

    except Exception as e:
        print(e)
        return None

    return df

# Table and cell styles
style_cell_conditional = [{
        'if': {'row_index': 'odd'},
        'backgroundColor': 'rgb(248, 248, 248)'},
        {
        'if': {'column_id': 'Data1: Interval'},
            'textAlign': 'left'
        }]

style_header = {'backgroundColor': 'white', 'fontWeight': 'bold'}

# Callback to Upload the data and the parse the excel file
@app.callback(Output('intermediate-value', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        df['NP'] = df['All: Net Profit'].apply(lambda x: True if x>0 else False)
        return df.to_json(orient='split')

# Net Profit based Pivot Tables
@app.callback(Output('output-table-1', 'children'),
             [Input('intermediate-value', 'children'),
             Input('conditions', 'value'),
             Input('NP-picker', 'value')])
def show_table(jsonified_data, option_to_pick, np_to_pick):

        df = pd.read_json(jsonified_data, orient='split')
        df['NP_1'] = df['All: Net Profit'].apply(lambda x: True if x > option_to_pick else False)

        pivot = df.pivot_table(values=np_to_pick, columns='Ins', aggfunc=sum,
                       index='Data1: Interval', margins=True, margins_name='Grand Total')

        pivot.sort_values(by="Grand Total", axis=1, ascending=False, inplace=True)
        pivot = pd.concat([pivot[pivot.columns[1:]], pivot['Grand Total']], axis=1)
        pivot.reset_index(inplace=True)

        if np_to_pick == 'NP':
            return html.Div([html.H6("Pivot table for Net Profit greater than 0"),
                        dash_table.DataTable(id = 'table', columns=[{'name': i, 'id': i} for i in pivot.columns],
                                            data = pivot.to_dict("rows"), style_header=style_header,
                                            style_cell_conditional=style_cell_conditional)])
        else:
            return html.Div([html.H6("Pivot table for Net Profit greater than {}".format(option_to_pick)),
                        dash_table.DataTable(id = 'table', columns=[{'name': i, 'id': i} for i in pivot.columns],
                                            data = pivot.to_dict("rows"), style_header=style_header,
                                            style_cell_conditional=style_cell_conditional)])

# Total trades based Pivot Tables
@app.callback(Output('output-table-2', 'children'),
             [Input('intermediate-value', 'children'),
             Input('conditions', 'value'),
             Input('NP-picker', 'value')])
def show_table(jsonified_data, option_to_pick, np_to_pick):

        df = pd.read_json(jsonified_data, orient='split')
        df['NP_1'] = df['All: Net Profit'].apply(lambda x: True if x > option_to_pick else False)
        df = df[df[np_to_pick] == 1].copy()

        pivot_2 = df.pivot_table(values='All: Total Trades', columns='Ins', aggfunc=np.mean, index='Data1: Interval').round(1).fillna(0)
        Total = pivot_2.apply(sum, axis=0).round(1)
        Total.name = 'Total'
        pivot_2 = pivot_2.append(Total)
        pivot_2.sort_values(by='Total', axis=1, ascending=False, inplace=True)
        pivot_2.reset_index(inplace=True)

        if np_to_pick == 'NP':
            return html.Div([html.H6("Pivot table for the average of total trades for NP greater than 0"),
                        dash_table.DataTable(id = 'table', columns=[{'name': i, 'id': i} for i in pivot_2.columns],
                                            data = pivot_2.to_dict("rows"), style_header=style_header,
                                            style_cell_conditional=style_cell_conditional)])
        else:
            return html.Div([html.H6("Pivot table for the average of total trades for NP greater than {}".format(option_to_pick)),
                        dash_table.DataTable(id = 'table', columns=[{'name': i, 'id': i} for i in pivot_2.columns],
                                            data = pivot_2.to_dict("rows"), style_header=style_header,
                                            style_cell_conditional=style_cell_conditional)])

if __name__ == '__main__':
    app.run_server(debug=True)
