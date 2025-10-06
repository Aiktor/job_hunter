import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import Output, Input, State, callback, dcc
from flask import session
import os
from utils.appvar import engine
import pandas as pd

dash.register_page(__name__)

layout = html.Div(dbc.Col([
        dcc.Location(id="url-login"),
        html.Br(),
        html.H4("Пожалуйста, авторизуйтесь:", id="h1"),
                dbc.Row(dbc.Input(placeholder="Логин", type="text", id="uname-box", name='username', className='loginput',)),
                dbc.Row(dbc.Input(placeholder="Пароль", type="password", id="pwd-box", name='password', className='loginput',)),
                dbc.Row(dbc.Button(children="Авторизоваться", n_clicks=0, type="submit", id="login-button-db"
                                                    , className="bottom-cust"
                                                    , style={'margin-top':20},)),
                    ], width={'size': 3, 'offset': 5})
                    , style={'width':'100%', 'height':'100vh'})

@callback( 
    Output('url-login','pathname'),
    Input("login-button-db", "n_clicks"),
    State("uname-box", "value"),
    State("pwd-box", "value"),
    prevent_initial_call=True)
def sts(nclick, usr, pwd):
    dbConnection = engine.connect()
    get_user = pd.read_sql(f"select * from movie.t05_jh_users where user_login='{usr}' and pass='{pwd}';", dbConnection)
    dbConnection.close()
    if len(get_user) == 0:
        return '/denied'
    state = os.urandom(16).hex()  # Генерация уникального состояния
    session['oauth_state'] = state  # Сохраняем в сессии
    session['user'] = {"name": usr,
                       "username": usr} 
    get_user = get_user.iloc[0]
    rights = get_user['rights'].astype(str)   
    session['rights'] = rights
    return  '/'