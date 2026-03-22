from sea_saw_base.serializers import BaseSerializer
from sea_saw_pipeline.models import Pipeline


class PipelineMinimalSerializer(BaseSerializer):
    """
    Minimal Pipeline serializer for Order list/overview display.
    Only shows essential pipeline status info - for full pipeline data, use Pipeline API.
    """

    class Meta(BaseSerializer.Meta):
        model = Pipeline
        fields = [
            "id",
            "pipeline_code",
            "status",
            "active_entity",
            "pipeline_type",
            "confirmed_at",
            "in_purchase_at",
            "purchase_completed_at",
            "in_production_at",
            "production_completed_at",
            "in_purchase_and_production_at",
            "purchase_and_production_completed_at",
            "in_outbound_at",
            "outbound_completed_at",
            "completed_at",
            "cancelled_at",
        ]
        read_only_fields = fields
