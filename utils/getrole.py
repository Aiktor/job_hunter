from flask import session
import pandas as pd
from sqlalchemy import create_engine
from utils.appvar import engine 

def get_user():
    user_data = session.get('user', {})
    username = user_data.get('username', 'Guest')  
    if username!='Guest':
        dbConnection = engine.connect()
        get_user = pd.read_sql(f"select * from movie.t05_jh_users where user_login='{username}';", dbConnection)
        dbConnection.close()
        if len(get_user) == 0:
            get_user.loc[-1] = ['Denied', None,  None]
        return get_user.iloc[0]
    return None # pd.Series({'login':'Guest'})