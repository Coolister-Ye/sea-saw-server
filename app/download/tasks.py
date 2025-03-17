import csv
import os
import pandas as pd

from celery import shared_task
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import activate

from download.models import DownloadTask
from download.utilis import dynamic_import_model, flatten, dynamic_import_serializer


def split_class_path(class_path):
    """
    Split the class path (e.g., 'app_name.model_name') into app_name and class_name.
    """
    app_name, class_name = class_path.split(".")
    return app_name, class_name


def create_directory(directory):
    """
    Create the directory if it does not exist.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


@shared_task
def generate_csv_task(model_cls, serializer_cls, filters, ordering, task):
    """
    Generate a CSV file for the filtered data using pandas and return the file path.
    """
    activate("zh-hans")
    # Retrieve the model dynamically
    app_name, model_name = split_class_path(model_cls)
    model = dynamic_import_model(app_name, model_name)

    # Get the queryset with filters and ordering
    queryset = model.objects.filter(**filters).order_by(*ordering)

    # Retrieve the serializer dynamically
    app_name, serializer_name = split_class_path(serializer_cls)
    serializer = dynamic_import_serializer(app_name, serializer_name)

    # Flatten the queryset and get the headers for CSV
    data, headers = flatten(queryset, serializer)

    # Convert data to pandas DataFrame
    df = pd.DataFrame.from_records(data)
    df = df.rename(columns=headers)

    # Ensure the directory exists for the file path
    directory = os.path.dirname(task["file_path"])
    create_directory(directory)

    try:
        # Write DataFrame to CSV with utf-8-sig encoding
        df.to_csv(task["file_path"], index=False, encoding="utf-8-sig")

        # Update the task status to 'completed' after successful file generation
        task_obj = get_object_or_404(DownloadTask, pk=task["pk"])
        task_obj.status = "completed"
        task_obj.completed_at = timezone.now()
        task_obj.download_url = os.path.join(
            settings.MEDIA_URL, "downloads", task_obj.file_name
        )
        task_obj.save()

        return task_obj.pk

    except Exception as e:
        # If an error occurs during the process, set the task status to 'failed'
        task_obj = get_object_or_404(DownloadTask, pk=task["pk"])
        task_obj.status = "failed"
        task_obj.error_message = str(e)  # Optionally, save the error message
        task_obj.save()

        return {"error": str(e)}  # Return the error message for logging or debugging
