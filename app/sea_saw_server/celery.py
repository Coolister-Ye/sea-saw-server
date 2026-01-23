import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sea_saw_server.settings')

app = Celery('sea_saw_server')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat 定时任务配置
app.conf.beat_schedule = {
    'cleanup-expired-downloads': {
        'task': 'download.tasks.cleanup_expired_downloads',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
        'options': {
            'description': '清理过期的下载文件（超过7天）',
        }
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
