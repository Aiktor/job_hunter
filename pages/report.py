from dash import register_page, html, dcc, Output, Input, State, callback, ctx, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from utils.appvar import engine, update_banned
from utils.promts import promts
from utils.giga import get_giga
from flask import session
import logging
import pandas as pd
from datetime import date as dt
from datetime import datetime
from locale_ru import AG_GRID_LOCALE_RU
import requests
import dash_daq as daq
import re

register_page(__name__,
                   title="Журнал корректировок")

def clean_html(text):
    # Создаем регулярное выражение для обработки нужных тегов
    # Удаляем открывающие теги <p>, <ul>, <li>, <strong>
    # Заменяем закрывающие теги на перенос строки ++++++ h2, div, h3
    pattern = re.compile(
        r'(?s)'  # Включаем режим точки, которая соответствует любому символу
        r'(<p\b[^>]*?>)|'  # Открывающий тег <p>
        r'(<ul\b[^>]*?>)|'  # Открывающий тег <ul>
        r'(<li\b[^>]*?>)|'  # Открывающий тег <li>
        r'(<strong\b[^>]*?>)|'  # Открывающий тег <strong>
        r'(<span\b[^>]*?>)|'  # Открывающий тег <span>
        r'(<em\b[^>]*?>)|'  # Открывающий тег <em>
        r'(<br\b[^>]*?>)|'  # Тег <br>
        r'(<div\b[^>]*?>)|'  # Открывающий тег <div>
        r'(<h2\b[^>]*?>)|'  # Открывающий тег <h2>
        r'(<h3\b[^>]*?>)|'  # Открывающий тег <h3>
        r'(<\/p>)|'  # Закрывающий тег </p>
        r'(<\/ul>)|'  # Закрывающий тег </ul>
        r'(<\/li>)|'  # Закрывающий тег </li>
        r'(<\/strong>)|'  # Закрывающий тег </strong>
        r'(<\/span>)|'  # Закрывающий тег </span>
        r'(<\/em>)|'  # Закрывающий тег </em>
        r'(<\/div>)|'  # Закрывающий тег </div>
        r'(<\/h2>)|'  # Закрывающий тег </h2>
        r'(<\/h3>)'  # Закрывающий тег </h3>
    ) 
    
    # Функция замены для подстановки
    def replace_match(match):
        # Если найден открывающий тег - возвращаем пустую строку
        if match.group(1) or match.group(2) or match.group(3) or match.group(4):
            return ''
        # Если найден закрывающий тег - возвращаем перенос строки
        else:
            return '\n'
    
    # Применяем замену
    cleaned_text = pattern.sub(replace_match, text)
    
    # Убираем лишние пробелы и переносы строк
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

def vaclist(user):
    dbConnection = engine.connect()
    vaclist = pd.read_sql(f'''
            select  
                v.id as id,
                "location",
                "type",
                title,
                company,
                logo,
                url,
                salary_from,
                salary_to,
                currency,
                published_at,
                requirement,
                responsibility,
                schedule,
                schedule1,
                schedule2,
                professional_roles,
                experience,
                employment,
                date_query,
                time_query,
                count_import,
                d.id as opened,
                d.banned 
            from movie.t01_jh_vacancies v
            left join movie.t06_jh_details d on v.id=d.id
            where user_query='{user}' 
                and banned is null or banned=False
            order by published_at desc
            limit 10000;
''', dbConnection).sort_values('published_at', ascending=False)
    dbConnection.close()
    vaclist['published_at'] = pd.to_datetime(vaclist['published_at']).dt.strftime('%Y.%m.%d %H:%M')
    vaclist['date_query'] = pd.to_datetime(vaclist['date_query'])
    vaclist['date_query'] =vaclist['date_query'].dt.date
    return vaclist

def get_row_style(params):
    if params['data']['opened'] != '':
        return {'backgroundColor': '#a6b0e1'}
    return {}

getRowStyle = {
    "styleConditions": [
        {
            "condition": "params.data.opened && params.data.opened !== ''",
            "style": {"backgroundColor": "#a6b0e1"},
        },
    ],
}

options = [{"label": key, "value": idx + 1} for idx, key in enumerate(promts.keys())]

allowed_tags = ["p", "ul", "li", "strong"]
allowed_attributes = {"*": ["class"]}  # Разрешили атрибут "class" для всех тегов

dwnld_btn =   dbc.Button([html.Img(src='assets/icon_download.png', className="nac-icon", style={'margin-right': '5px',}), "  Скачать журнал"], id="dwnld-button", className='bottom-cust')
flt_btn =     dbc.Button([html.Img(src='assets/icon_filter_d.png',style={'margin-right': '5px',}), "  Расширенный фильтр"], id="filter-btn", n_clicks=0,  className='bottom-cust')
filter_pp = dbc.Offcanvas([
                html.P("Локация", style={'margin-bottom': '0'}),
                    dcc.Dropdown(multi=True, placeholder="Выберите город",  className='default-select', style={'fontSize': '12px', 'high': '15px'}, id='filter-location'),
                html.Br(),   
                html.P("Тип", style={'margin-bottom': '0'}),
                    dcc.Dropdown(multi=True, placeholder="Выберите тип",  className='default-select', style={'fontSize': '12px', 'high': '15px'}, id='filter-type'),
                html.Br(),                                       
                html.P("Занятость", style={'margin-bottom': '0'}),
                    dcc.Dropdown(multi=True, placeholder="Выберите тип занятости",  className='default-select', style={'fontSize': '12px', 'high': '15px'}, id='filter-employment'),
                html.Br(),                 
                html.P("Период публикации", style={'margin-bottom': '0'}),
                    dcc.DatePickerRange(
                        id='published-range',
                        display_format='DD.MM.YYYY',
                        month_format='MMMM Y',
                        end_date_placeholder_text='MMMM Y',
                        end_date = dt.today(),
                        max_date_allowed=dt.today(),
                        style= {'Size': '5px',
                                'height':'7px',
                                'margin-bottom': '10px'}),
                    html.Br(),   html.Br(),         
                html.P("Требуемый опыт", style={'margin-bottom': '0'}),
                    dcc.Dropdown(multi=True, placeholder="Выберите требуемый опыт",  className='default-select', style={'fontSize': '12px', 'high': '15px'}, id='filter-expirience'),
                html.Br(), 
                html.P("Количество выгрузок", style={'margin-bottom': '0'}),
                    dcc.Dropdown(multi=True, placeholder="Выберите .....",  className='default-select', style={'fontSize': '12px', 'high': '15px'}, id='filter-count'),
                html.Br(),     
                html.Div(
                    dbc.Button([html.Img(src='assets/icon_filter_d.png',style={'margin-right': '5px',}), " Применить"], id="apply-filter-exc", n_clicks=0),
                    style={"display": "flex", "justify-content": "flex-end"}),
                ],
                id="filter-exc-offcanvas",
                title="Фильтр по журналу",
                class_name='light-canvas',
                is_open=False)

filterParams= {"maxNumConditions": 1, "filterOptions": ["contains"]}
RangeFilterParams= {"maxNumConditions": 1, "filterOptions": ["greaterThan", "lessThan", "inRange", "blank", "notBlank"]}
columnDefs_vaclist = [
    {'field': 'id', 'headerName': 'ID', 'suppressSizeToFit': True, 'maxWidth': 120, "cellStyle": {'textAlign': 'center'}, "filterParams": filterParams},
    {'field': 'title', 'headerName': 'Название', 'suppressSizeToFit': True, "cellStyle": {'textAlign': 'left'}, "filterParams": filterParams},
    {'field': 'company', 'headerName': 'Компания', 'suppressSizeToFit': True, "cellStyle": {'textAlign': 'left'}, "filterParams": filterParams},
    {'field': 'salary_from', 'headerName': 'ЗП от', 'suppressSizeToFit': True, 'maxWidth': 100, "cellStyle": {'textAlign': 'center'}, "filter": False},
    {'field': 'salary_to', 'headerName': 'ЗП до', 'suppressSizeToFit': True, 'maxWidth': 100, "cellStyle": {'textAlign': 'center'}, "filter": False},
    {'field': 'published_at', 'headerName': 'Опубликовано',  'suppressSizeToFit': True, 'maxWidth': 150, 'suppressSizeToFit': True, "cellStyle": {'textAlign': 'left'}, "filter": False},
    {'field': 'professional_roles', 'headerName': 'Проф. роли', 'suppressSizeToFit': True, "cellStyle": {'textAlign': 'left'}, "filter": False},
    {'field': 'experience', 'headerName': 'Опыт', 'suppressSizeToFit': True, 'maxWidth': 150, "cellStyle": {'textAlign': 'center'}, "filter": False},
    {'field': 'employment', 'headerName': 'Занятость', 'suppressSizeToFit': True, "cellStyle": {'textAlign': 'left'}, "filter": False},
    {'field': 'date_query', 'headerName': 'Выгружена', 'suppressSizeToFit': True, 'maxWidth': 120, "cellStyle": {'textAlign': 'left'}, "filter": False},
    {'field': 'time_query', 'headerName': 'Время', 'suppressSizeToFit': True, 'maxWidth': 80, "cellStyle": {'textAlign': 'left'}, "filter": False},
    ]
defaultColDef = {
    "wrapHeaderText": True,
    "autoHeaderHeight": True,
    "suppressMenu": True,
    "filter": True,
    'floatingFilter': True,
    'height': '200px',
    'tooltipComponent': 'CustomTooltip'
}

grid_vaclist = dag.AgGrid(
        id='vaclist-grid',
        columnDefs=columnDefs_vaclist,
        getRowStyle=getRowStyle,
        columnSize='sizeToFit',
        defaultColDef=defaultColDef,
        dashGridOptions={'pagination': True,
                        "resizable": True,
                        'headerHeight': 40,
                        "rowSelection": "single",
                        "localeText": AG_GRID_LOCALE_RU,
                        "rowHeight": 20},  
        # className='dbc dbc-ag-grid', 
        className='ag-theme-quartz',
        style={'margin-top': '20px',
            'margin-left':'20px',
            'margin-right':'20px',
            "fontSize": "14px",
            "height": 400,
            'width':'95%'})

layout =    html.Div([
            dcc.Location(id='url-report', refresh=True),
            dcc.Download(id="download-dataframe-xlsx"),
            dcc.Store(id='store-update'),
            dbc.Row([dbc.Col(html.H3('Журнал вакансий'), width={"size": 3}),
                     dbc.Col(flt_btn, className='centered-col', width={"size": 3, 'offset':6})], style={'margin-bottom':'10px', 'margin-left':'30px', 'padding-top':'10px'}),
            dbc.Row(filter_pp),
            html.Div([grid_vaclist,
                    dbc.Row( dbc.Col(dwnld_btn, className='centered-col', width={"size": 3, 'offset':9}))],
                    className='divblock'),         
            dbc.Collapse(
                dbc.Tabs([
                    dbc.Tab(
                        html.Div(
                            dbc.Row([        
                                    dbc.Col(
                                        html.Div(id='det_id', style={'width':'100%'})
                                        , className='centered-col', width={"size": 6}),
                                    dbc.Col([
                                            html.Div('Описание вакансии',  className='centered-div'),
                                            html.Div( id='vacancy_discription', style={'white-space': 'normal', 'overflow': 'hidden', 'textAlign':'left'})],className='centered-col', width={"size": 6}),
                        ]), className='divblock',),
                        label="Детализация вакансии", label_class_name="ls", active_label_class_name="als"),
                    dbc.Tab(html.Div([
                                dbc.Alert("ОШИБКА генерации ответа GigaChat", 
                                        id="alert-giga", 
                                        dismissable=True,
                                        is_open=False,
                                        duration=4000,
                                        class_name='fail-alert',
                                        style={"zIndex": 1050}), 
                                dbc.Row([        
                                    dbc.Col(
                                        html.Div([
                                            dbc.Row(
                                                dbc.Row(['Ключ авторизации: ', dbc.Input(id="auth_key", placeholder="Вставьте ключ авторизации GigaChat", type="text", size="sm", class_name='default-item', style={'margin-bottom':'10px'})], ), #Ключ авторизации
                                            ),
                                            dbc.Row(dbc.Button([html.Img(src='assets/icon_download.png', className="nac-icon", style={'margin-right': '5px',}), "  Сгенерировать резюме и сопроводительное письмо на вакансию"], id="startgiga-button", className='bottom-cust')),
                                            dbc.Row(dbc.Spinner(html.Div(id='spinner'), size="sm")),
                                            dbc.Row(dbc.RadioItems(options=options, 
                                                                   value=1,
                                                                    id="show-promt",
                                                                    className='custom-radio',
                                                                    inline=False,)),
                                            
                                            dbc.Row(html.Div(id='current_promt',  className='centered-div'))], style={'width':'95%'})
                                        , className='centered-col', width={"size": 6}),
                                    dbc.Col([
                                            html.Div('Результат от GigaChat',  className='centered-div'),
                                            html.Div( id='giga2', style={'white-space': 'normal', 'overflow': 'hidden', 'textAlign':'left'})],className='centered-col', width={"size": 6}),
                        ], style={'width': '100%'})], id='gigachat-tab', className='divblock', style={'height': '95%', 'overflow': 'auto'}), label="GigaChat резюме", label_class_name="ls", active_label_class_name="als"),
                ], class_name="custom-tabs"),
                id="show_vac",
                is_open=None,)
            ],  className='maindivblock', style={'min-height': '92vh', 'height':'100%', 'width':'100%', 'overflow-x':'hidden'})

#Фильтр и применить фильтр
@callback(
    Output('filter-exc-offcanvas', 'is_open'),     
    Output('filter-location', 'options'),
    Output('filter-type', 'options'),
    Output('filter-employment', 'options'),
    Output('published-range', 'start_date'),
    Output('filter-expirience', 'options'),
    Output('apply-filter-exc', 'className'),
    Output('vaclist-grid', 'rowData'),     
    Output('filter-count', 'options'),

    Input('filter-btn', 'n_clicks'),
    Input('apply-filter-exc', 'n_clicks'),
    State('theme-store', 'data'),
    State('filter-location', 'value'),
    State('filter-type', 'value'),
    State('filter-employment', 'value'),
    State('published-range', 'start_date'),
    State('published-range', 'end_date'),
    State('filter-expirience', 'value'),
    Input('store-update', 'data'),
    State('filter-count', 'value')
)
def auc_info_area(get, apply, theme, location, type, employment, sday, eday, experience, data, count):
    triggered_id = ctx.triggered_id
    user = session.get('user')['username'] if session.get('user') is not None and 'username' in session.get('user') else 'Guest'      
    vaqclist = vaclist(user)
    # if triggered_id == 'store-update' and data is not None:
    #     vaqclist = vaqclist[vaqclist['id_exc_pk'].isin(data)]
    #     vaqclist = vaqclist if statuses==None or statuses == [] else vaqclist[vaqclist['статус'].isin(statuses)]
    if triggered_id == 'apply-filter-exc':
        logging.info(f"{user} ==> Кнопка /Применить фильтр/ на странице report")
        vaqclist = vaqclist[(vaqclist['published_at']>=datetime.strptime(sday, "%Y-%m-%d").date()) & (vaqclist['published_at']<=datetime.strptime(eday, "%Y-%m-%d").date())]
        vaqclist = vaqclist if location==None or location == [] else vaqclist[vaqclist['location'].isin(location)]
        vaqclist = vaqclist if type==None or type == [] else vaqclist[vaqclist['type'].isin(type)]
        vaqclist = vaqclist if employment==None or employment == [] else vaqclist[vaqclist['employment'].isin(employment)]
        vaqclist = vaqclist if experience==None or experience == [] else vaqclist[vaqclist['experience'].isin(experience)]
        vaqclist = vaqclist if count==None or count == [] else vaqclist[vaqclist['count_import'].isin(count)]
        return False, no_update, no_update, no_update, no_update, no_update, no_update, vaqclist.to_dict('records'), no_update
    elif triggered_id=='filter-btn':
        logging.info(f"{user} ==> Кнопка /Расширенный фильтр/ на странице report")
        return True, \
                sorted(vaqclist['location'].unique()), \
                sorted(vaqclist[~vaqclist['type'].isna()]['type'].unique()), \
                sorted(vaqclist[~vaqclist['employment'].isna()]['employment'].unique()), \
                vaqclist['published_at'].min(), \
                sorted(vaqclist[~vaqclist['experience'].isna()]['experience'].unique()),  \
                'light-bottom-cust' if theme=='light-theme' else 'dark-bottom-cust', \
                no_update, \
                sorted(vaqclist[~vaqclist['count_import'].isna()]['count_import'].unique()),
    return  no_update, no_update, no_update, no_update, no_update, no_update, no_update, vaqclist.to_dict('records'), no_update

@callback(
    Output('show_vac', 'is_open')
    , Output('store-update', 'data')
    , Output('det_id', 'children')
    # , Output('det_name', 'children')
    # , Output('det_company', 'children')
    , Output('vacancy_discription', 'children')

    , Input("vaclist-grid", "selectedRows")   
    , State('vaclist-grid', 'rowData')
    , State('theme-store', 'data')
)
def output_actions(selected_rows, rows, theme):
    triggered_id = ctx.triggered_id
    if selected_rows:
        dbConnection = engine.connect()
        details = pd.read_sql(f"select * from movie.t06_jh_details where id='{selected_rows[0]['id']}';", dbConnection)
        dbConnection.close()
        if details.shape[0]>0:
            descript = details.iloc[0]['description']
            favorite = details.iloc[0]['favorite']
            banned = details.iloc[0]['banned']
        else:
            get_vacancy = requests.get(f"https://api.hh.ru/vacancies/{selected_rows[0]['id']}").json()
            data = []
            data.append({
            'id':get_vacancy['id'],
            'description':get_vacancy['description'],
            'favorite': False,
            'banned':False,
            'response_date': pd.NaT
            })
            descript = get_vacancy['description']
            favorite, banned = False, False
            pd.DataFrame(data).to_sql("t06_jh_details", con=engine, schema='movie', if_exists='append', index=False)
        block = [
            dbc.Row([
                dbc.Col(html.Div(f"ID {selected_rows[0]['id']}", style={'display': 'inline-block', 'vertical-align': 'middle'}), width={"size": 3, }),
                dbc.Col(html.A(
                    f"{selected_rows[0]['title']}",
                    href=f"{selected_rows[0]['url']}",
                    target="_blank",
                    className="navbar",
                    style={'display': 'inline-block', 'vertical-align': 'middle', 'padding-left': '15px', 'padding-right': '15px',}
                ), width={"size": 5, }),
                dbc.Col([html.Img(
                    src=selected_rows[0]['logo'],
                    className="nac-icon",
                    style={
                        'height': '30px',
                        'width': '30px',
                        'margin-left': '5px',
                        'margin-right': '5px',
                        'object-fit': 'contain',
                        'display': 'inline-block',
                        'vertical-align': 'middle'
                    }
                ),
                html.Div(f"{selected_rows[0]['company']}", style={'display': 'inline-block', 'vertical-align': 'middle'})
                ], width={"size":4, })
            ], style={'text-align': 'left', 'with':'100%'}, justify="start"),
            dbc.Row([
                dbc.Col(dbc.Badge(selected_rows[0]['location'], color="primary", className="me-1"), width={"size": 1, }),
                dbc.Col([html.Div(f"Тип", style={'display': 'inline-block', 'vertical-align': 'middle'}),
                         dbc.Badge(selected_rows[0]['type'], color="secondary", className="me-1")], width={"size": 1, }),
                # dbc.Col(html.Div(f"Тип: {selected_rows[0]['type']}", style={'display': 'inline-block', 'vertical-align': 'middle'}), width={"size": 2, }),
                dbc.Col(daq.ToggleSwitch(value=favorite, id='switch-favorite', label='В избранное', labelPosition='left'), width={"size": 3, }),
                dbc.Col(daq.ToggleSwitch(value=banned, id='switch-banned', label='Заблокировать', labelPosition='left'), width={"size": 3, }),
                dbc.Col(html.Div(f"ЗП: {selected_rows[0]['salary_from']} - {selected_rows[0]['salary_to']} {selected_rows[0]['currency']}", style={'display': 'inline-block', 'vertical-align': 'middle'}), width={"size": 3, })
            ], style={'text-align': 'left', 'with':'100%', 'margin-top': '5px'}, justify="start"),
            dbc.Row([
                dbc.Col(html.Div(f"Опубликовано: {selected_rows[0]['published_at']},   Спарсено: {selected_rows[0]['date_query']} {selected_rows[0]['time_query']}, Количество: {selected_rows[0]['count_import']}", style={'display': 'inline-block', 'vertical-align': 'middle'})),
            ], style={'text-align': 'left', 'with':'100%', 'margin-top': '5px'}, justify="start"),
            # dbc.Row([
            #     dbc.Col(html.Div(f"ЗП: {selected_rows[0]['salary_from']} - {selected_rows[0]['salary_to']} {selected_rows[0]['currency']}", style={'display': 'inline-block', 'vertical-align': 'middle'})),
            # ], style={'text-align': 'left', 'with':'100%', 'margin-top': '5px'}, justify="start"),
            dbc.Row([
                dbc.Col([html.Div(f"Профессиональные роли", style={'display': 'inline-block', 'vertical-align': 'middle'}),
                        dbc.Badge(selected_rows[0]['professional_roles'], color="secondary", className="me-1")
                         ], width={"size": 3, }),
                dbc.Col([html.Div(f"Требуемый опыт", style={'display': 'inline-block', 'vertical-align': 'middle'}),
                         dbc.Badge(selected_rows[0]['experience'], color="secondary", className="me-1")]),
                dbc.Col([html.Br(), dbc.Badge(selected_rows[0]['schedule'], color="primary", className="me-1")]),
                dbc.Col([html.Br(), dbc.Badge(selected_rows[0]['schedule1'], color="primary", className="me-1")]),
                dbc.Col([html.Br(), dbc.Badge(selected_rows[0]['schedule2'], color="primary", className="me-1")]),        
            ], style={'text-align': 'left', 'with':'100%', 'margin-top': '5px'}, justify="start"),
            html.Br(),
            dbc.Row([
                dbc.Col(html.Div([
                    html.B("требования"),
                    html.P(f"{selected_rows[0]['requirement']}")], style={'display': 'inline-block', 'vertical-align': 'middle'})),
            ], style={'text-align': 'left', 'with':'100%', 'margin-top': '5px'}, justify="start"),  
            html.Br(),
            dbc.Row([
                dbc.Col(html.Div([
                    html.B("Обязанности"),
                    html.P(f"{selected_rows[0]['responsibility']}")], style={'display': 'inline-block', 'vertical-align': 'middle'})),
            ], style={'text-align': 'left', 'with':'100%', 'margin-top': '5px'}, justify="start"),          
        ]
        return True, no_update, block, clean_html(descript)
    else:
        return None, no_update, no_update, no_update

@callback(
    Input("switch-favorite", "value"),
    Input('switch-banned', 'value'),
    State("vaclist-grid", "selectedRows"),
    prevent_initial_call=True
)
def output_actions(favorite, banned, selected_rows):
    update_banned(selected_rows[0]['id'], banned)

@callback(
    Output("current_promt", "children"),
    Input("show-promt", "value")
)

def change_promt(val):
    return list(promts.values())[val-1]

@callback(
    Output('spinner', 'children'),
    Output('giga2', 'children'),
    Output('alert-giga', 'is_open'),
    Input("startgiga-button", "n_clicks"),
    State("vaclist-grid", "selectedRows"),
    State("auth_key", "value"),
    State("current_promt", "children"),
    State('vacancy_discription', 'children')
)

def apply_giga(n_click, selected_rows, auth_key, promt, description):
    if n_click:
        if pd.isna(auth_key) or len(auth_key)<100:
            return "", "", True
        name = ''.join(char for char in selected_rows[0]['title'] if char.isalnum() or char.isspace())
        time = datetime.now().strftime("%Y-%m-%d %H-%M")
        reply =get_giga(auth_key, promt, selected_rows[0]['id'], name, description, time)
        return f'''Сохренено в файл "{selected_rows[0]['id']} {name} {time}.docx"''', reply, no_update
    return "", "", no_update 