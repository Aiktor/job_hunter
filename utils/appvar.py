from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

envpath = "etl/.env"
load_dotenv(envpath) 

log_file = "jh_app.log"

engine = create_engine(f"postgresql+psycopg2://{os.getenv('user')}:{os.getenv('pass')}@{os.getenv('hest')}:5432/{os.getenv('DB')}",
        isolation_level='AUTOCOMMIT')


def update_banned(id, banned):
        update_query = text(f"""
        UPDATE movie.t06_jh_details
        SET banned={banned}
        WHERE id = '{id}'
        """)

        # Выполняем запрос
        with engine.connect() as conn:
                result = conn.execute(
                        update_query
                )
                conn.commit()