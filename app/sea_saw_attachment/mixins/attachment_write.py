from sea_saw_attachment.models import Attachment


class ReusableAttachmentWriteMixin:
    """
    Generic mixin for handling nested attachments write logic with GenericForeignKey support.

    Expected serializer attributes:
    - attachment_model: Django model class (required)
    - attachment_field_name: str (default: "attachments") - field name in serializer
    - attachment_file_field: str (default: "file") - file field name in attachment model

    Handles three scenarios:
    1. Existing attachment (has id, no file) - keep unchanged
    2. New attachment (no id, has file) - create new
    3. Update attachment (has id, has file) - create new (replaces old)

    Works with both traditional ForeignKey and GenericForeignKey patterns.
    For GenericForeignKey models, automatically sets content_type and object_id.

    Usage:
        class MySerializer(ReusableAttachmentWriteMixin, BaseSerializer):
            attachment_model = Attachment
            attachment_field_name = "attachments"  # optional, default is "attachments"
            attachments = AttachmentSerializer(many=True, required=False)

            # create() and update() will automatically handle attachments
            # No need to manually pop and call _handle_attachments
    """

    attachment_model = None
    attachment_field_name = "attachments"
    attachment_file_field = "file"
    attachment_model = Attachment

    def create(self, validated_data):
        """
        Override create to automatically handle attachments.
        Subclasses can still override this method - just call super().create()
        """
        # Pop attachments to handle separately (using configurable field name)
        attachments = validated_data.pop(self.attachment_field_name, None)

        # Create instance with remaining data
        instance = super().create(validated_data)

        # Handle attachments
        self._handle_attachments(instance, attachments)

        return instance

    def update(self, instance, validated_data):
        """
        Override update to automatically handle attachments.
        Subclasses can still override this method - just call super().update()
        """
        # Pop attachments to handle separately (using configurable field name)
        attachments = validated_data.pop(self.attachment_field_name, None)

        # Update instance with remaining data
        instance = super().update(instance, validated_data)

        # Handle attachments
        self._handle_attachments(instance, attachments)

        return instance

    def _handle_attachments(self, instance, attachments):
        """
        Process attachments list: delete removed attachments and create new ones.

        Handles three scenarios:
        1. Existing attachment (has id, no new file) - keep unchanged
        2. New attachment (no id, has binary file) - create new
        3. Update attachment (has id, has binary file) - create new (replaces old)

        Any existing attachment whose id is NOT in the submitted list is deleted.
        If attachments is None (not provided in partial update), nothing is done.

        Automatically handles GenericForeignKey by setting content_type and object_id.
        """
        # None means the field was not included in the request (partial update) - skip
        if attachments is None:
            return

        if not self.attachment_model:
            raise AssertionError("attachment_model must be defined")

        # Import here to avoid circular imports
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(instance)

        # Delete attachments that are no longer in the submitted list
        keep_ids = {att.get("id") for att in attachments if att.get("id")}
        self.attachment_model.objects.filter(
            content_type=content_type,
            object_id=instance.pk,
        ).exclude(id__in=keep_ids).delete()

        # Create new attachments
        for att in attachments:
            file_obj = att.get(self.attachment_file_field)
            att_id = att.get("id")

            # Case 1: Existing attachment without new file - keep unchanged
            if att_id and not file_obj:
                continue

            # Case 1b: Existing attachment with URL string in file field - skip
            if att_id and isinstance(file_obj, str):
                continue

            # Case 2 & 3: New binary file present - create new attachment
            if file_obj and hasattr(file_obj, "read"):
                create_data = {
                    self.attachment_file_field: file_obj,
                    "content_type": content_type,
                    "object_id": instance.pk,
                }

                if att.get("description"):
                    create_data["description"] = att["description"]

                # attachment_type will be auto-set by Attachment.save() method
                self.attachment_model.objects.create(**create_data)
