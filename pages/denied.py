import dash
import dash_bootstrap_components as dbc
from dash import Output, Input, html, dcc, callback
from flask import session

dash.register_page(__name__)


layout = html.Div(
    [       dcc.Location(id='url-dennied', refresh=False),
            html.Br(),
            dbc.Container([               dbc.Row([
                    dbc.Col(
                        dbc.Alert([
                            html.H4("ACCESS DENIED!", className="alert-heading"),
                            html.Hr(style={'height': '1px', 'border': 'none', 'border-top': '1px solid #d988cd'}),
                            html.P([ "Для доступа требуется ",
                                    html.A("залогиниться", href="/", style={'color':'#d988cd', 'text-decoration': 'underline', 'font-weight': 'bold'}, id="alertlink"), 
                                    " под пользователем, имеющим права на просмотр"], className="mb-0" ),
                            ], class_name='fail-alert',
                            ),
                        width={'size': 8, 'offset': 2}
                    )
                ])
            ])]
            # , id='body_denied'
    , style={'width':'100%', 'height':'100vh'}
)

@callback(
    Output('alertlink', 'href'),
    Input('url-dennied', 'pathname')# Используем изменение URL как триггер
)
def update_table_denied(pathname):
    if session.get('rights') is None:
        return '/logout'#, 'dark-theme' if theme == 'dark-theme' else 'light-theme'
    else:
        return '/login'#, 'dark-theme' if theme == 'dark-theme' else 'light-theme'
