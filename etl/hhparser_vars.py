import requests
import pandas as pd
from datetime import datetime
import re
import logging
from sqlalchemy import create_engine, text
import os
import sys
from dotenv import load_dotenv
from telebot import TeleBot


def main(WAREHOUSE_URL, TELEGRAM_TOKEN, CHAT_ID):
    load_dotenv()
    custom_time_format = '%Y-%m-%d %H:%M:%S'
    log_file = "/home/viktor/airflow/dags/scripts/jh_etl.log"
    # log_file = "jh_etl.log"

    logging.basicConfig(
        level=logging.DEBUG, 
        filename = log_file, 
        encoding='utf-8',
        format = "%(asctime)s >>> %(module)s >>> %(levelname)s >>> %(funcName)s >>> %(lineno)d >>> %(message)s", 
        datefmt=custom_time_format)
    logging.info(f"START скрипт hhparser.py")
    
    def send_telegram_file(file_path):
        bot = TeleBot(TELEGRAM_TOKEN)
        with open(file_path, 'rb') as file:
            bot.send_document(chat_id=CHAT_ID, document=file)

    def fetch_vacancies(text, area=None, page=0, per_page=20, experience=None, employment=None, schedule=None):
        base_url = "https://api.hh.ru/vacancies"
        params = {
            "text": text,
            "page": page,
            "per_page": per_page,
        }
        
        if area is not None:
            params["area"] = area
        if experience is not None:
            params["experience"] = experience
        if employment is not None:
            params["employment"] = employment
        if schedule is not None:
            params["schedule"] = schedule
            
        response = requests.get(base_url, params=params)
        return response.json()
    def logo(empl):
        if 'logo_urls' in empl:
            if empl['logo_urls'] is not None:
                if '90' in empl['logo_urls']:
                    return  empl['logo_urls']['90']
        return None
    engine = create_engine(WAREHOUSE_URL)    

    dbConnection = engine.connect()
    hhParsers = pd.read_sql('select * from movie.t07_jh_hhparsers;', dbConnection)
    dbConnection.close() 
    for i in range(hhParsers.shape[0]):
        if hhParsers.iloc[i]['active']==True:
            user = hhParsers.iloc[i]['user']
            logging.info(f"пользователь {user}- начало выгрузки")
            # Параметры поиска
            search_text_list = hhParsers.iloc[i]['searechfield'].split(',') # строка поиска (название вакансии)
            region_code = hhParsers.iloc[i]['area']  # 1=Москва, 26=Воронеж; код региона (если None, ищем по всей России)
            results_per_page = 100 # количество записей на страницу
            experience= hhParsers.iloc[i]['experience']
            employment= hhParsers.iloc[i]['employment']
            schedule= hhParsers.iloc[i]['schedule']
            df = pd.DataFrame()
            for search_text in search_text_list:
                for page_number in range(20):
                    response_data = fetch_vacancies(search_text, region_code, page_number, results_per_page, experience, employment, schedule)
                    # Преобразуем полученные данные в DataFrame
                    data = []
                    for vacancy in response_data['items']:
                        a = vacancy['professional_roles'][1]['name'] if len(vacancy['professional_roles'])>1 else None
                        data.append({
                            'id': vacancy['id'],
                            'location': vacancy['area']['name'],
                            'type': vacancy['type']['name'],
                            'title': vacancy['name'],
                            'company': vacancy['employer']['name'],
                            'logo': logo(vacancy['employer']),
                            'url': vacancy['alternate_url'],
                            'salary_from': vacancy['salary']['from'] if vacancy['salary'] else None,
                            'salary_to': vacancy['salary']['to'] if vacancy['salary'] else None,
                            'currency': vacancy['salary']['currency'] if vacancy['salary'] else None,
                            'created_at': vacancy['created_at'],
                            'published_at': vacancy['published_at'],
                            'archived': vacancy['archived'],
                            'requirement': vacancy['snippet']['requirement'],
                            'responsibility': vacancy['snippet']['responsibility'],
                            'schedule': vacancy['schedule']['name'],
                            'schedule1': vacancy['work_format'][0]['name'] if len(vacancy['work_format'])>=1 else None,
                            'schedule2': vacancy['work_format'][1]['name'] if len(vacancy['work_format'])>1 else None,
                            'professional_roles': vacancy['professional_roles'][0]['name'],
                            'experience': vacancy['experience']['name'],
                            'employment': vacancy['employment']['name'],
                            'user_query': user,
                            'date_query': datetime.now().strftime("%Y-%m-%d"),
                            'time_query': datetime.now().strftime("%H-%M"),

                        })
                    df1 = pd.DataFrame(data)
                    logging.info(f"пользователь {user}- по запросу {search_text} выгружено {df1.shape[0]} вакансий")
                    df = pd.concat([df, df1], axis=0, ignore_index=True)
                    if df1.shape[0]<100:
                        break
            logging.info(f"пользователь {user}- выгрузка с hh.ru завершена. количество не очищенных записей {df.shape[0]}")
            # Функция очистки текста от тегов highlighttext
            def clean_highlight_tags(text):
                if isinstance(text, str):
                    cleaned_text = re.sub(r'<highlighttext>|</highlighttext>', '', text)
                    return cleaned_text.strip()  # Удаляем лишние пробелы
                return text

            # Применяем очистку к столбцу description
            df['requirement'] = df['requirement'].apply(clean_highlight_tags)
            df['responsibility'] = df['responsibility'].apply(clean_highlight_tags)

            def select_row(group):
                row = group.iloc[0] 
                if len(group)>1:
                    if len(set(group['requirement']))>1:
                        row['requirement']='|'.join(set(group['requirement']))
                    if len(set(group['responsibility']))>1:
                        row['responsibility']='|'.join(set(group['responsibility']))
                return row
            df_uniq = df.groupby('id', as_index=False).apply(select_row, include_groups=False)
            logging.info(f"пользователь {user}- осталось уникальных записей {df_uniq.shape[0]}")
            # fileName=f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}_{user}"
            # df_uniq.to_excel(f"D:/Портфолио/JH/бэкапы выгрузок/{fileName}.xlsx", index=False)

            logging.info(f"пользователь {user}- выгрузка с hh.ru завершена. Начало выгрузки имеющихся в базе вакансий")
            dbConnection = engine.connect()
            base_vacancies = pd.read_sql(f'''
            select 
                id,
                count_import,
                date_query
            from movie.t01_jh_vacancies
            where  user_query = '{user}';                           
            ''', dbConnection)
            dbConnection.close() 

            logging.info(f"обновление резервной таблицы на текущую перед внесением изменений")
            backup_query =  text('''
                DROP TABLE IF EXISTS public.t01_jh_vacancies;
                CREATE TABLE public.t01_jh_vacancies AS SELECT * FROM movie.t01_jh_vacancies;
            ''')
            with engine.connect() as connection:
                connection.execute(backup_query)

            
            new_v = df_uniq[~df_uniq['id'].isin(base_vacancies['id'])].copy()
            if new_v.shape[0]>0:
                new_v.loc[:, 'count_import'] = 1
                logging.info(f"пользователь {user}- загрузка новых вакансий в количестве {new_v.shape[0]}")
                new_v.to_sql("t01_jh_vacancies", con=engine, schema='movie', if_exists='append', index=False)
                send_bot = new_v[['title', 'company']].copy()
                file_path = 'table.csv'
                send_bot.to_csv(file_path, index=False)
                send_telegram_file(file_path)
                        
            logging.info(f"пользователь {user}- обновление имеющихся вакансий")
            base_v_old = base_vacancies[base_vacancies['date_query']!=datetime.now().strftime("%Y-%m-%d")].copy()
            update_v = df_uniq[df_uniq['id'].isin(base_v_old['id'])].copy()
            base_v_old['count_import'] = base_v_old['count_import']+1
            tmp_df = update_v.merge(base_v_old[['id', 'count_import']], on='id', how='left')

            id_list = list(tmp_df['id'])
            delete_query = text('''
                DELETE FROM movie.t01_jh_vacancies
                WHERE id = ANY(:ids)
                AND user_query = :user_query
            ''')
            with engine.connect() as connection:
                connection.execute(delete_query, {"ids": id_list, "user_query": user})
                connection.commit()

            if not connection.closed:
                connection.close()
            tmp_df.to_sql("t01_jh_vacancies", con=engine, schema='movie', if_exists='append', index=False)

            logging.info(f"пользователь {user}- обновление таблицы статистики загрузки")
            df1 = pd.DataFrame({'date': [datetime.now().strftime('%Y-%m-%d %H-%M')], 
                                'user_query': [user],
                                'download_rows': [df_uniq.shape[0]],
                                'new_rows': [new_v.shape[0]],
                                'update_rows': [tmp_df.shape[0]]})
            df1.to_sql("t02_jh_etl", con=engine, schema='movie', if_exists='append', index=False)
    logging.info(f"END скрипт hhparser.py")

if __name__ == "__main__":
    # Получаем параметры из командной строки
    param1 = sys.argv[1]
    param2 = sys.argv[2]
    param3 = sys.argv[3]
    main(param1, param2, param3)    