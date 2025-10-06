from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime, timedelta
from airflow.models import Variable


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dag_hh_pars_vars",
    default_args=default_args,
    schedule_interval="8 4-16 * * 1-5",
    start_date=datetime(2025, 9, 1),
    catchup=False,
    tags=["jh"],
) as dag:

    hh_parser = SSHOperator(
        task_id="hh_parser_vars",
        ssh_conn_id="serv_ssh",
        command=f"bash -c 'source /home/viktor/venv/bin/activate && python /home/viktor/airflow/dags/scripts/hhparser_vars.py {Variable.get('WAREHOUSE_URL_postgresql_superset')} {Variable.get('jh_bot_token')} {Variable.get('chat_id_jhbot')}'",
        cmd_timeout=600  # устанавливаем таймаут в секундах
    )
