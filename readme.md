Описание сформировано автоматически. Доступно на https://deepwiki.com/Aiktor/job_hunter

Overview
--------

Relevant source files

*   [LICENSE.txt](https://github.com/Aiktor/job_hunter/blob/03bd14bd/LICENSE.txt)
*   [jh\_app.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py)
*   [requirements.txt](https://github.com/Aiktor/job_hunter/blob/03bd14bd/requirements.txt)

Purpose and Scope
-----------------

This document provides a technical overview of the **Job Hunter** application, an automated job vacancy aggregation and analysis system designed for the Russian job market. The system extracts job postings from the HeadHunter API (hh.ru), stores them in a PostgreSQL database, and provides a web-based interface for browsing, filtering, and generating AI-powered application materials.

This overview covers the system's architecture, core components, and data flows at a high level. For detailed information about specific subsystems, see:

*   ETL pipeline implementation: [ETL Pipeline](https://deepwiki.com/Aiktor/job_hunter/2-etl-pipeline)
*   Web application structure: [Web Application](https://deepwiki.com/Aiktor/job_hunter/3-web-application)
*   Database schema details: [Database Schema](https://deepwiki.com/Aiktor/job_hunter/2.3-database-schema)
*   Frontend components: [Frontend Assets](https://deepwiki.com/Aiktor/job_hunter/5-frontend-assets)

**Sources:** [jh\_app.py1-143](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L1-L143) [etl/hhparser\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/etl/hhparser_vars.py) [dags/dag\_hhpars\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/dags/dag_hhpars_vars.py)

* * *

System Description
------------------

Job Hunter operates as a three-tier system:

1.  **Automated Data Collection**: An Airflow-orchestrated ETL pipeline (`dag_hhpars_vars.py`, `hhparser_vars.py`) runs on weekdays between 8:00-16:00 UTC, fetching job vacancies from HeadHunter's public API based on user-defined search parameters. New vacancies are stored in PostgreSQL and trigger Telegram notifications.
    
2.  **Data Storage**: A PostgreSQL database with the `movie` schema contains five core tables (`t01_jh_vacancies`, `t05_jh_users`, `t06_jh_details`, `t07_jh_hhparsers`, `t02_jh_etl`) that store vacancy data, user accounts, parser configurations, and ETL audit logs.
    
3.  **Interactive Web Application**: A Dash/Flask application (`jh_app.py`) provides authenticated access to browse vacancies, apply filters, mark favorites/banned positions, and generate AI-powered resumes and cover letters via the GigaChat API.
    

**Sources:** [jh\_app.py24-34](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L24-L34) [etl/hhparser\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/etl/hhparser_vars.py) [dags/dag\_hhpars\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/dags/dag_hhpars_vars.py)

* * *

Architecture Overview
---------------------

The following diagram maps the system's major components to their corresponding code modules:

**Component Architecture and Code Module Mapping**

<img width="974" height="396" alt="image" src="https://github.com/user-attachments/assets/88b9b788-9453-45a5-aa8b-35b76edb77ee" />



**Sources:** [jh\_app.py24-71](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L24-L71) [dags/dag\_hhpars\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/dags/dag_hhpars_vars.py) [etl/hhparser\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/etl/hhparser_vars.py) [pages/login.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/login.py) [pages/report.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/report.py) [pages/logout.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/logout.py) [pages/denied.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/denied.py) [utils/appvar.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/utils/appvar.py) [utils/getrole.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/utils/getrole.py) [utils/giga.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/utils/giga.py)

* * *

Data Flow
---------

The following sequence diagram illustrates the complete data lifecycle from automated extraction to interactive user consumption:

**End-to-End Data Flow: ETL to Web UI**

```
<img width="974" height="952" alt="image" src="https://github.com/user-attachments/assets/0c536844-3b9d-4e34-b57e-fa18d84bd9dc" />

```


**Sources:** [dags/dag\_hhpars\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/dags/dag_hhpars_vars.py) [etl/hhparser\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/etl/hhparser_vars.py) [jh\_app.py94-138](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L94-L138) [pages/report.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/report.py) [utils/giga.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/utils/giga.py)

* * *

Core Components
---------------

### ETL Pipeline



* Component: Orchestrator
  * File: dags/dag_hhpars_vars.py
  * Responsibility: Airflow DAG that schedules hhparser_vars.py execution on weekdays 8:00-16:00 UTC
* Component: Parser
  * File: etl/hhparser_vars.py
  * Responsibility: Fetches vacancies from HeadHunter API, performs deduplication, inserts/updates database records, sends Telegram notifications
* Component: Notification
  * File: Telegram Bot API
  * Responsibility: Receives CSV files of new vacancies via pyTelegramBotAPI


**Sources:** [dags/dag\_hhpars\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/dags/dag_hhpars_vars.py) [etl/hhparser\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/etl/hhparser_vars.py)

### Database Layer

The PostgreSQL `movie` schema contains five tables:


|Table           |Purpose                                                        |
|----------------|---------------------------------------------------------------|
|t01_jh_vacancies|Core vacancy data (title, employer, salary, requirements)      |
|t05_jh_users    |User credentials and access rights                             |
|t06_jh_details  |Extended vacancy details (full description, skills, user flags)|
|t07_jh_hhparsers|User-defined search parameters for ETL                         |
|t02_jh_etl      |ETL execution audit logs                                       |


For detailed schema documentation, see [Database Schema](https://deepwiki.com/Aiktor/job_hunter/2.3-database-schema).

**Sources:** [etl/hhparser\_vars.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/etl/hhparser_vars.py) [pages/report.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/report.py)

### Web Application



* Component: Server
  * File: jh_app.py
  * Responsibility: Flask server, Dash app initialization, theme management, authentication routing
* Component: Login
  * File: pages/login.py
  * Responsibility: User authentication and session creation
* Component: Report
  * File: pages/report.py
  * Responsibility: Main vacancy browser with dashAgGrid, filters, details modal, AI content generation
* Component: Logout
  * File: pages/logout.py
  * Responsibility: Session termination
* Component: Access Denied
  * File: pages/denied.py
  * Responsibility: Unauthorized access page


**Sources:** [jh\_app.py24-71](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L24-L71) [pages/login.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/login.py) [pages/report.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/report.py) [pages/logout.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/logout.py) [pages/denied.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/denied.py)

### Utility Modules


|Module             |File            |Functionality                                          |
|-------------------|----------------|-------------------------------------------------------|
|Database Operations|utils/appvar.py |SQLAlchemy engine creation, database update functions  |
|Authentication     |utils/getrole.py|Flask session-based user retrieval                     |
|AI Integration     |utils/giga.py   |GigaChat API wrapper for resume/cover letter generation|


**Sources:** [utils/appvar.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/utils/appvar.py) [utils/getrole.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/utils/getrole.py) [utils/giga.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/utils/giga.py)

### Frontend Assets


|Asset Type  |Files                        |Purpose                                            |
|------------|-----------------------------|---------------------------------------------------|
|Styling     |assets/styles.css            |Light/dark theme CSS variables and component styles|
|JavaScript  |assets/dashAgGridFunctions.js|Custom AG-Grid cell renderers and date formatters  |
|Icons       |assets/icon_*.png            |Navigation icons for theme toggle, menu items      |
|Localization|assets/locale_ru.py          |Russian translations for AG-Grid UI elements       |


**Sources:** [jh\_app.py29-30](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L29-L30) [assets/styles.css](https://github.com/Aiktor/job_hunter/blob/03bd14bd/assets/styles.css) [assets/dashAgGridFunctions.js](https://github.com/Aiktor/job_hunter/blob/03bd14bd/assets/dashAgGridFunctions.js) [assets/locale\_ru.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/assets/locale_ru.py)

* * *

Technology Stack
----------------

Job Hunter is built with the following technologies:


|Category           |Technology               |Version     |Purpose                        |
|-------------------|-------------------------|------------|-------------------------------|
|Web Framework      |Flask                    |3.1.2       |HTTP server                    |
|                   |Dash                     |3.2.0       |Interactive UI framework       |
|                   |dash-bootstrap-components|2.0.4       |Bootstrap styling              |
|Data Processing    |pandas                   |2.2.3       |Data manipulation              |
|                   |SQLAlchemy               |2.0.43      |Database ORM                   |
|UI Components      |dash-ag-grid             |32.3.1      |Data table rendering           |
|                   |dash-daq                 |0.6.0       |Theme toggle switch            |
|External APIs      |requests                 |2.32.5      |HTTP client for HeadHunter API |
|                   |pyTelegramBotAPI         |4.29.1      |Telegram notifications         |
|                   |gigachat                 |0.1.42.post2|AI content generation          |
|Document Generation|python-docx              |1.2.0       |DOCX file creation             |
|Configuration      |python-dotenv            |1.1.1       |Environment variable management|


**Sources:** [requirements.txt1-13](https://github.com/Aiktor/job_hunter/blob/03bd14bd/requirements.txt#L1-L13) [jh\_app.py1-11](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L1-L11)

* * *

Session Management and Authentication Flow
------------------------------------------

The application uses Flask sessions to maintain user state across requests:

**Authentication State Machine**

```
<img width="974" height="1010" alt="image" src="https://github.com/user-attachments/assets/48cc567e-3894-4960-8b13-92d3394f11c4" />

```


Key session variables:

*   `session['user']`: Dictionary containing `username` and authentication data
*   `session['rights']`: Integer access level (5-6 for normal users)
*   `session['oauth_state']`: CSRF protection token

The `get_user()` function in `utils/getrole.py` retrieves the current user from the session, while `jh_app.py` callback [jh\_app.py94-138](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L94-L138) handles authentication routing and navbar updates.

**Sources:** [jh\_app.py94-138](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L94-L138) [utils/getrole.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/utils/getrole.py) [pages/login.py](https://github.com/Aiktor/job_hunter/blob/03bd14bd/pages/login.py)

* * *

Configuration and Security
--------------------------

The application uses environment variables for sensitive configuration:


|Variable            |Location         |Purpose                         |
|--------------------|-----------------|--------------------------------|
|SECRET_KEY          |.env             |Flask session encryption key    |
|jh_bot_token        |Airflow Variables|Telegram bot authentication     |
|chat_id_jhbot       |Airflow Variables|Telegram notification recipient |
|Database credentials|.env             |PostgreSQL connection parameters|
|GigaChat API keys   |.env             |AI service authentication       |


The `.gitignore` file explicitly excludes:

*   `.env` - Environment variables
*   `utils/promts.py` - AI prompt templates
*   `ai_resume/` - Generated documents directory
*   `logs/` - Application log files

For detailed configuration information, see [Configuration and Deployment](https://deepwiki.com/Aiktor/job_hunter/6-configuration-and-deployment).

**Sources:** [jh\_app.py13-34](https://github.com/Aiktor/job_hunter/blob/03bd14bd/jh_app.py#L13-L34) [LICENSE.txt1-22](https://github.com/Aiktor/job_hunter/blob/03bd14bd/LICENSE.txt#L1-L22)

* * *

License
-------

Job Hunter is licensed under the MIT License, permitting free use, modification, and distribution with attribution. See [License](https://deepwiki.com/Aiktor/job_hunter/6.3-license) for full terms.

**Sources:** [LICENSE.txt1-22](https://github.com/Aiktor/job_hunter/blob/03bd14bd/LICENSE.txt#L1-L22)
