from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.serializers import ListSerializer

from sea_saw_auth.models import User
from .models import Contact, Company, Field, Contract, Order, OrderProduct

DATETIME_FORMATS = '%Y-%m-%d %H:%M:%S'
DATE_FORMATS = '%Y-%m-%d'


class BaseSerializer(WritableNestedModelSerializer):
    owner = serializers.CharField(
        source='owner.username',
        read_only=True,
        allow_null=True,
        label=_("Owner"),
        help_text=_("The user who owns this object."),
    )
    created_by = serializers.CharField(
        read_only=True, allow_null=True, label=_("Created By"), help_text=_("The user who created this object.")
    )
    updated_by = serializers.CharField(
        read_only=True, allow_null=True, label=_("Updated By"), help_text=_("The user who last updated this object.")
    )
    created_at = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
        format=DATETIME_FORMATS,
        label=_("Created At"),
        help_text=_("Timestamp when this object was created."),
    )
    updated_at = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
        format=DATETIME_FORMATS,
        label=_("Updated At"),
        help_text=_("Timestamp when this object was last updated."),
    )

    class Meta:
        abstract = True
        fields = ['pk', 'owner', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def get_context_user(self):
        """
        Retrieve the user from request context.
        Used for setting created/updated by fields.
        """
        request = self.context.get('request')
        return request.user if request else None

    def _get_common_kwargs(self, field):
        """
        Helper method to extract common arguments for nested fields
        (such as required, nullability, default values, etc.)
        """
        _kwards = field.__dict__.get("_kwargs")
        return {**_kwards, **{"context": self.context}}

    def _process_nested_field(self, field, field_name):
        """
        Process nested fields to apply context and related arguments.
        Handles both ListSerializer (many=True) and single nested serializer cases.
        """
        if isinstance(field, ListSerializer):  # Handle many=True case
            field = field.child
            child_serializer_class = field.__class__
            field_kwargs = self._get_common_kwargs(field)
            self.fields[field_name] = ListSerializer(child=child_serializer_class(context=self.context), **field_kwargs)
        else:  # Handle single serializer case
            serializer_class = field.__class__
            field_kwargs = self._get_common_kwargs(field)
            self.fields[field_name] = serializer_class(**field_kwargs)

    def forward_context(self):
        """
        Forward context to nested serializers to ensure they have access
        to the correct request and user context.
        """
        for field_name, field in self.fields.items():
            if isinstance(field, BaseSerializer) or (
                hasattr(field, 'child') and isinstance(field.child, BaseSerializer)
            ):
                self._process_nested_field(field, field_name)

    def _filter_fields(self, fields):
        """
        Filter out fields that are not in the allowed list based on the 'fields' parameter.
        This helps to limit the fields that are included in the serialized output.
        """
        if fields:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def __init__(self, *args, **kwargs):
        """
        Initializes the serializer with optional field filtering and context forwarding.

        Args:
            fields (list): Optional list of fields to include in the serializer.
        """
        fields_to_include = kwargs.pop('fields', [])
        super().__init__(*args, **kwargs)

        # Forward context to nested fields
        self.forward_context()

        # Filter out unwanted fields based on the provided list
        if fields_to_include:
            self._filter_fields(fields_to_include)

    def perform_nested_delete_or_update(self, pks_to_delete, model_class, instance, related_field, field_source):
        """
        Custom method for handling nested delete or update actions.
        This prevents accidental removal of other related records during an update.
        """
        if not self.partial:
            super().perform_nested_delete_or_update(pks_to_delete, model_class, instance, related_field, field_source)

    def assign_direct_relation(self, instance, relation_name, relation_model, relation_data=None):
        """
        Assign a direct relation (like owner, contact) to the instance based on input data.

        Args:
            instance (model instance): The instance to update.
            relation_name (str): The name of the related field.
            relation_model (model class): The model class of the related field.
            relation_data (dict, optional): The data used to identify the related instance.

        Returns:
            instance: The updated instance with the assigned relation.
        """
        # If no relation data is provided, exit early
        if (
            not relation_data
            and hasattr(self.initial_data, relation_name)
            and hasattr(self.validated_data, relation_name)
        ):
            return instance

        # Use initial_data or passed relation_data if available
        relation_data = relation_data or self.initial_data.get(relation_name) or self.validated_data.get(relation_name)

        try:
            # Determine the relation instance
            if not relation_data:
                relation_instance = None
            elif isinstance(relation_data, relation_model):
                relation_instance = relation_data  # Direct relation instance provided
            elif isinstance(relation_data, dict) and 'pk' in relation_data:
                # If a dictionary with 'pk' is provided, retrieve the instance by pk
                relation_instance = relation_model.objects.get(pk=relation_data['pk'])
            else:
                # If other data is provided (e.g., direct filters), retrieve instance
                relation_instance = relation_model.objects.get(**relation_data)

            # Set the relation on the instance only if it's different
            current_relation = getattr(instance, relation_name, None)
            if current_relation != relation_instance:
                setattr(instance, relation_name, relation_instance)
                instance.save(update_fields=[relation_name])

        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {relation_name: f'{relation_model.__name__} with the provided identifier does not exist.'}
            )
        except Exception as e:
            raise serializers.ValidationError({relation_name: f'Error assigning {relation_model.__name__}: {str(e)}'})

        return instance

    def assign_owner(self, instance):
        """
        Assign the owner to the instance if provided in the initial data.
        Owner cannot be updated to null if it's been set.
        """
        owner_data = self.initial_data.get('owner')
        if owner_data and isinstance(owner_data, str):
            self.initial_data['owner'] = {'username': owner_data}  # Normalize to dict
        return self.assign_direct_relation(instance, 'owner', User)

    def create(self, validated_data):
        """
        Create a new instance and assign the owner if necessary.

        Args:
            validated_data (dict): The validated data for the new instance.

        Returns:
            instance: The created instance with the owner assigned.
        """
        owner = validated_data.pop('owner', None)
        user = self.get_context_user()
        if owner and 'owner' not in self.initial_data:
            self.initial_data['owner'] = owner
        if user:
            validated_data['created_by'] = user.username
            if not hasattr(self.initial_data, 'owner'):
                self.initial_data['owner'] = user

        instance = super().create(validated_data)
        return self.assign_owner(instance)

    def update(self, instance, validated_data):
        """
        Update an existing instance and assign the owner if necessary.

        Args:
            instance (model instance): The instance to update.
            validated_data (dict): The validated data for updating the instance.

        Returns:
            instance: The updated instance with the owner assigned.
        """
        user = self.get_context_user()
        if user:
            validated_data['updated_by'] = user.username
        instance = super().update(instance, validated_data)
        return self.assign_owner(instance)


class FieldSerializer(BaseSerializer):
    """
    Serializer for the Field model.
    - @field_option: The choice of field for picklist type.
    - @content_type: Use the name of the model for serialization/deserialization.
    """

    content_type = serializers.CharField(
        source='content_type.model', label=_("Content Type"), help_text=_("The model associated with this field.")
    )

    class Meta:
        model = Field
        fields = ['pk', 'field_name', 'field_type', 'is_active', 'is_mandatory', 'content_type', 'extra_info', 'owner']

    def validate(self, data):
        """
        Validate the field data:
        - Picklist fields must include a 'picklist' key in `extra_info`.
        """
        if data.get('field_type') == 'picklist' and not data.get('extra_info', {}).get('choices'):
            raise serializers.ValidationError('Picklist field requires a "picklist" key in extra_info.')
        return data

    @staticmethod
    def get_content_model(content_type_data):
        """
        Resolve content_type from the provided model name.
        """
        try:
            return ContentType.objects.get_by_natural_key(app_label='sea_saw_crm', model=content_type_data['model'])
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {"content_type": f"ContentType for model '{content_type_data['model']}' does not exist."}
            )

    def handle_content_type(self, validated_data):
        """
        Convert content_type data to ContentType instance.
        """
        content_type_data = validated_data.pop('content_type', None)
        if content_type_data:
            validated_data['content_type'] = self.get_content_model(content_type_data)
        return validated_data

    def create(self, validated_data):
        """
        Support creating objects using model names for content_type.
        """
        validated_data = self.handle_content_type(validated_data)
        return Field.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Validate immutable fields and update the instance.
        """
        immutable_fields = ['field_name', 'field_type']
        for field in immutable_fields:
            if field in validated_data and validated_data[field] != getattr(instance, field):
                raise serializers.ValidationError({field: f"The field '{field}' cannot be updated."})

        validated_data = self.handle_content_type(validated_data)
        return super().update(instance, validated_data)


class CompanySerializer(BaseSerializer):
    """
    Company serializer
    """

    class Meta(BaseSerializer.Meta):
        model = Company
        fields = ['pk', 'company_name', 'email', 'mobile', 'phone', 'home_phone', 'owner']


class ContactSerializer(BaseSerializer):
    """
    Serializer for the Contact model, automatically updates full_name
    during creation and update operations.
    """

    company = CompanySerializer(fields={"company_name"}, required=False, allow_null=True, label=_("Company"))

    class Meta(BaseSerializer.Meta):
        model = Contact
        fields = [
            'pk',
            'first_name',
            'last_name',
            'full_name',
            'title',
            'email',
            'mobile',
            'phone',
            'company',
            'owner',
            'created_by',
            'updated_by',
            'created_at',
            'updated_at',
        ]

    def assign_company(self, instance, company):
        """
        Assign the company relationship to the instance.
        """
        return self.assign_direct_relation(instance, 'company', Company, company)

    @staticmethod
    def set_full_name(validated_data):
        """
        Set the full_name field based on first_name and last_name.
        """
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        validated_data['full_name'] = f"{first_name} {last_name}".strip()
        return validated_data

    def handle_relations(self, instance, validated_data):
        """
        Handle related fields like company.
        """
        company = validated_data.pop("company", None)
        if instance:
            self.assign_company(instance, company)
        return validated_data

    def create(self, validated_data):
        """
        Override create method to handle full_name and relations.
        """
        validated_data = self.set_full_name(validated_data)
        instance = super().create(validated_data)
        self.handle_relations(instance, validated_data)
        return instance

    def update(self, instance, validated_data):
        """
        Override update method to handle full_name and relations.
        """
        validated_data = self.set_full_name(validated_data)
        validated_data = self.handle_relations(instance, validated_data)
        instance = super().update(instance, validated_data)
        return instance


class OrderProductSerializer(BaseSerializer):
    """
    Production order details serializer for contract view.
    This serializer assume the user can be either sale or admin user.
    """

    class Meta(BaseSerializer.Meta):
        model = OrderProduct
        fields = [
            'pk',
            'product_name',
            'size',
            'packaging',
            'interior_packaging',
            'weight',
            'glazing',
            'net_weight',
            'quantity',
            'total_net_weight',
            'price',
            'total_price',
            'progress_material',
            'progress_quantity',
            'progress_weight',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Retrieve user from context
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return

        user = request.user

        # Admin users: no restrictions
        if user.is_staff:
            return

        # Sale group: set specific fields to read-only
        if user.groups.filter(name="Sale").exists():
            self.fields['progress_quantity'].read_only = True
            self.fields['progress_weight'].read_only = True
            return


class OrderProductSerializer4Prod(BaseSerializer):
    """
    Production order details serializer for contract view.
    This serializer assume the user can be sale, production or admin user.
    """

    class Meta(BaseSerializer.Meta):
        model = OrderProduct
        fields = [
            'pk',
            'product_name',
            'size',
            'packaging',
            'interior_packaging',
            'weight',
            'glazing',
            'net_weight',
            'quantity',
            'total_net_weight',
            'price',
            'total_price',
            'progress_material',
            'progress_quantity',
            'progress_weight',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Retrieve user from context
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return
        user = request.user

        # Admin users: no restrictions
        if user.is_staff:
            return

        # Sale group: set all fields to read-only
        if user.groups.filter(name="Sale").exists():
            for field_name in list(self.fields.keys()):  # 使用 `list(self.fields.keys())` 拷贝键列表
                self.fields[field_name].read_only = True

        # Production group: set all fields to read-only except for progress related fields
        editable_fields = {'progress_quantity', 'progress_weight'}
        hidden_fields = {'price', 'total_price'}
        for field_name in list(self.fields.keys()):  # 使用 `list(self.fields.keys())` 拷贝键列表
            if field_name in hidden_fields:
                self.fields.pop(field_name)
            else:
                self.fields[field_name].read_only = field_name not in editable_fields


class OrderSerializer(BaseSerializer):
    """
    Order serializer for admin users.
    """

    products = OrderProductSerializer(many=True, required=False, allow_null=True)

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = [
            'pk',
            'order_code',
            'destination_port',
            'etd',
            'deliver_date',
            'deposit',
            'deposit_date',
            'balance',
            'balance_date',
            'stage',
            'products',
        ]


class OrderSerializer4Prod(BaseSerializer):
    """
    Order serializer for production users.
    Hides price-related fields.
    """

    products = OrderProductSerializer4Prod(many=True, required=False, allow_null=True)

    class Meta(BaseSerializer.Meta):
        model = Order
        fields = [
            'pk',
            'order_code',
            'etd',
            'destination_port',
            'products',
            'owner',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Retrieve user from context
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return

        user = request.user

        # Admin users: no restrictions
        if user.is_staff:
            return

        # Sale group: set all fields to read-only
        if user.groups.filter(name="Sale").exists():
            for field_name, field in self.fields.items():
                field.read_only = True

        # Sale/Production group: set all fields to read-only, except for products
        for field_name, field in self.fields.items():
            if field_name not in ["products"]:
                field.read_only = True


class ContractSerializer(BaseSerializer):
    """
    Contract serializer for admin and sale user.
    """

    contact = ContactSerializer(fields={'full_name'}, required=False, allow_null=True)
    orders = OrderSerializer(many=True, required=False)

    class Meta(BaseSerializer.Meta):
        model = Contract
        fields = [
            'pk',
            'contract_code',
            'contract_date',
            'stage',
            'contact',
            'orders',
            'owner',
            'created_at',
            'updated_at',
        ]

    def assign_contact(self, instance, contact):
        """
        Assigns or updates the contact for the deal instance.
        Field contact is a picklist, it cannot be created directly through this entry,
        while it can only be selected and join to the contract object
        """
        return self.assign_direct_relation(instance, 'contact', Contact, contact)

    def create_or_update(self, instance, validated_data):
        """
        Handles creation or update of a Deal instance with contact assignment.
        :param instance: Deal instance to update, or None for creation.
        :param validated_data: Data for the Deal instance.
        :return: Updated or newly created Deal instance.
        """
        # Create or update the Deal instance
        contact = validated_data.pop("contact", None)
        instance = super().update(instance, validated_data) if instance else super().create(validated_data)

        # Assign the contact relationship
        if not self.assign_contact(instance, contact):
            raise serializers.ValidationError(_("Failed to assign contact to the deal."))

        return instance

    def create(self, validated_data):
        """
        Creates a new Deal instance.
        """
        return self.create_or_update(None, validated_data)

    def update(self, instance, validated_data):
        """
        Updates an existing Deal instance.
        """
        return self.create_or_update(instance, validated_data)
