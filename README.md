# PCR

## Project Overview

This project aims to implement the **Celery** with **Django.**
This project calculate the **Put-Call Ratio (PCR)** values for different financial indices: **NIFTY, FINNIFTY, MIDCPNIFTY, and BANKNIFTY.** The application will be built using **Django** for the web framework and **Celery** for **scheduling** and executing **periodic tasks.**


## Technologies Used

- **Django**: Web framework
- **Celery**: Task queue for scheduling and executing periodic tasks
- **Redis**: Message broker for Celery

## Installation

#### Prerequisites

* Python 3.8 or later
* pip (Python package installer)
* Django
* Redis

## Steps

1. Clone the repository:
    ```bash
    git clone https://github.com/username/repository.git
    cd repository
    ```

2. Create Virtual Environment:

    ```bash
    python -m venv venv
    ```

3. Activate the Virtual Environment:

    * On Windows:

        ```bash
        venv\Scripts\activate
        ```

    * On Mac or Linux:

        ```bash
        source venv/bin/activate
        ```

4. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

5. Add .env file for configuration and add below:

    ```bash
    DEBUG=True
    CELERY_BROKER_URL=redis://127.0.0.1:6379/0
    NEAREST_SRIKE_PRICES=8
    SLEEP_BETWEEN=420
    SYMBOLS=NIFTY,BANKNIFTY,FINNIFTY,MIDCPNIFTY
    ```

    * NEAREST_SRIKE_PRICES is number of strike prices above and below from current srike price. 8 is best sutable for generatng PCR.

    * SLEEP_BETWEEN is time(Seconds) for interval for generating PCR. Here 420 Seconds = 7 Minutes

6. Run the Migrations:

    ```bash
    python manage.py makemigrations

    python manage.py migrate
    ```

7. Start the Django server:

    * Run the Django Server in Development mode:

        ```bash
        python manage.py runserver
        ```

    * For Prodution, Run the Django application using Gunicorn:
        ```bash
        gunicorn pcr.wsgi:application --bind 0.0.0.0:8000
        ```

8. Start Celery worker and beat:

    ```bash
    celery -A pcr.celery worker --pool=solo -l info
    celery -A pcr beat -l info
    ```

    for this project we can use solo pool. It will be enough for the project.

## Data and Reports

After generating the PCR values, the application creates a directory structure in the file system.

Each symbol (e.g., NIFTY, FINNIFTY, MIDCPNIFTY, BANKNIFTY) will have its own folder with date.

Inside each folder, the following files will be generated:

- A CSV file containing all the data used for the calculations.
- Two graphs:
  - A graph showing the PCR values over time.
  - A graph showing the differences in open interest (OI) data over time.


## Acknowledgements

We would like to thank the following resources and libraries that made this project possible:

* **Django**: A high-level Python web framework that encourages rapid development and clean, pragmatic design.
* **Celery**: An asynchronous task queue/job queue based on distributed message passing.
* **Redis**: An in-memory data structure store, used as a message broker by Celery.
* **Python Decouple**: A tool to manage settings and environment variables, enabling easy configuration of the project.
* **Open Source Community**: For providing valuable resources, libraries, and tools that aid in the development of web applications.
