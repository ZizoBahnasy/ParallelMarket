from celery import Celery
from scraper import scrape_and_calculate

# Initialize Celery with Redis as the broker
app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def scheduled_scrape():
    # Define the task to run the scraper
    scrape_and_calculate()

# Schedule the task to run every 5 minutes
app.conf.beat_schedule = {
    'scrape-every-5-minutes': {
        'task': 'scheduler.scheduled_scrape',
        'schedule': 300.0,  # 5 minutes
    },
}

# Uncomment the following line to run the scraper immediately on startup
# scheduled_scrape.apply_async()
