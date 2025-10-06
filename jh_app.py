from dash import Dash, dcc, html, Input, Output, ALL, State, ctx, page_container, no_update
import dash_bootstrap_components as dbc
import dash_daq as daq
import logging
import os
from dotenv import load_dotenv
# from authlib.integrations.flask_client import OAuth
from utils.appvar import envpath, log_file
from flask import Flask, session
from utils.getrole import get_user


load_dotenv(envpath) 
custom_time_format = '%Y-%m-%d %H:%M:%S'
log_file = log_file
logging.basicConfig(
    level=logging.DEBUG, 
    filename = log_file, 
    encoding='utf-8',
    format = "%(asctime)s >>> %(module)s >>> %(levelname)s >>> %(funcName)s >>> %(lineno)d >>> %(message)s", 
    datefmt=custom_time_format,
    )
#===================================================================================================   
server = Flask(__name__)
app = Dash(__name__,
           server=server, 
            pages_folder='pages',
            use_pages=True,
            external_stylesheets=[dbc.themes.MORPH, 'assets/style.css', #dbc.icons.BOOTSTRAP#, dbc_css # 
                                  ],
            prevent_initial_callbacks="initial_duplicate",
            suppress_callback_exceptions=True)

server.config.update(SECRET_KEY=os.getenv('SECRET_KEY'))

'''NAVBAR'''
navbar_html = html.Div(
    children=[    
        dbc.NavbarSimple(
            children=[    
                dbc.NavItem(dbc.NavLink(
                    [html.Img(src='assets/icon_monitor_n.png', className="nac-icon", style={'margin-right': '5px'}, id='icon_dashboard'), "Дашборд "], 
                    href="#"), style={'font-size': '16px', 'display':'flex'}),
                dbc.NavItem(dbc.NavLink(
                    [html.Img(src='assets/icon_report_n.png', className="nac-icon", style={'margin-right': '5px'}, id='icon_hhparser'), "НН Парсер "], 
                    href="#"), style={'font-size': '16px', 'display':'flex'}),
                dbc.NavItem(dbc.NavLink("login", href="/login", style={'font-size': '16px'}, id="user-status-header-navlink"), id="user-status-header"),
                dbc.NavItem(dbc.NavLink("Guest", disabled=True, style={'font-size': '16px'}, href="#", id="user-status-header1-navlink"), id="user-status-header1"),
                dbc.NavItem(html.Div(
                    [html.Img(src='assets/icon_sun_n.png', className="nac-icon", style={'margin-right': '5px'}, id='icon_sun'), 
                     daq.ToggleSwitch(value=True, id='daq-toggleswitch'),
                     html.Img(src='assets/icon_moon_n.png', className="nac-icon", style={'margin-left': '5px'}, id='icon_moon')],
                    style={'display': 'flex', 'align-items': 'center'}
                )),
            ],
            id='navbar',
            className='navbar' 
        )
    ]
)
app.title = 'Job Hunter'
app.layout = html.Div(
    [
        dcc.Location(id="url"),
        dcc.Store(id='theme-store', data='dark-theme', storage_type='session'),  # Хранение текущей темы
        dcc.Store(id='switch-store', storage_type='session'),  # Хранение текущей темы
        navbar_html,
        page_container,
    ],
            id='main_div',
)

@app.callback(
    Output('theme-store', 'data'),
    Input('daq-toggleswitch', 'value'),
    prevent_initial_call=True
)
def update_theme(toggle_value):
    return 'dark-theme' if toggle_value else 'light-theme'

@app.callback(
    Output('main_div', 'className'), 
    Output('icon_dashboard', 'src'),
    Output('icon_hhparser', 'src'),
    Output('icon_sun', 'src'),
    Output('icon_moon', 'src'),
    Input('theme-store', 'data'))
def update_class(theme):
    if theme == 'light-theme':
        return 'light-theme', 'assets/icon_monitor_d.png',  'assets/icon_report_d.png',  'assets/icon_sun_d.png', 'assets/icon_moon_d.png'  # Применяем класс светлой темы
    else:
        return 'dark-theme', 'assets/icon_monitor_n.png',  'assets/icon_report_n.png',  'assets/icon_sun_n.png', 'assets/icon_moon_n.png'# Применяем класс темной темы

@app.callback(
    Output("user-status-header-navlink", "children"),
    Output("user-status-header-navlink", "href"),
    Output("user-status-header1-navlink", "children"),
    Output('url','pathname'),
    Output('daq-toggleswitch', 'value'),
    Input("url", "pathname"),
    Input({'index': ALL, 'type':'redirect'}, 'n_intervals')
    , State('theme-store', 'data')
)
def update_authentication_status(path, n, theme):
    us = 'Guest'
    lnk = "login"
    lnkh="/login"
    switch = True if theme=='dark-theme' else False
    stl = {'font-size': '16px', 'display':'none'} if session.get('rights') is None or int(session.get('rights'))>3 else {'font-size': '16px', 'display':'block'}
    ### logout redirect
    if n:
        if n[0]==1:
            session.clear()
            state = os.urandom(16).hex()  # Генерация уникального состояния
            session['oauth_state'] = state  # Сохраняем в сессии
            # stl = {'font-size': '16px', 'display':'none'} if session.get('rights') is None or int(session.get('rights'))>3 else {'font-size': '16px', 'display':'block'}
            return lnk, lnkh, us, '/login', switch
    c_user = get_user()
    # ### check if user is logged in
    user = session.get('user')['username'] if session.get('user') is not None and 'username' in session.get('user') else 'Guest'
    logging.info(f"{user} ==> Переход из меню на страницу {path}")
    if c_user is not None:
        if c_user.user_login=='Denied':
            session.clear()
            state = os.urandom(16).hex()  # Генерация уникального состояния
            session['oauth_state'] = state  # Сохраняем в сессии
            # stl = {'font-size': '16px', 'display':'none'} if session.get('rights') is None or int(session.get('rights'))>3 else {'font-size': '16px', 'display':'block'}
            return lnk, lnkh, us, '/denied', switch
        rights = c_user['rights'].astype(str)   
        session['rights'] = rights
        us = c_user.user_login
        lnk = "logout"
        lnkh = "/logout"
    if path in ['/'] and session.get('rights') is None :
        return lnk, lnkh, us, '/login', switch
    if path in ['/'] and int(session.get('rights')) in [5, 6] :
        return lnk, lnkh,  us, '/report', switch
    return lnk, lnkh, us, no_update, switch


# Поменять для buz.mts-corp на:     app.run_server(debug=False, port=port)
if __name__ == '__main__':
    app.run(debug=True, port=8052)