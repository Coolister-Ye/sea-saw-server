import json

from sea_saw_crm.models import Field


def load_fields():
    with open("./fixtures/fields.json", "r") as f:
        fields = json.load(f)
        for field in fields:
            content_type = field["content_type"]
            field_name = field["field_name"]
            Field.objects.update_or_create(
                content_type=content_type, field_name=field_name, defaults=field
            )
