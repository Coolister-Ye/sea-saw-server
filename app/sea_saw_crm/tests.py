from bokeh.palettes import Turbo
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from intake.container.serializer import serializers
from rest_framework.test import APITestCase
from .models import (
    Contact, Company, Product, Pipeline, Stage, Deal,
    CustomFieldValue, Field, Contract, Order, OrderProduct
)
from .serializer_class import (
    ContactSerializer, CompanySerializer,
    PipelineSerializer, StageSerializer, DealSerializer, FieldSerializer, ContractSerializer
)
from sea_saw_auth.models import (
    User
)


class SerializerTests(APITestCase):

    def setUp(self):
        # Create sample data for testing
        self.user = User.objects.create_user(
            username="coolister",
            email="coolister@qq.com",
            password="Ironman@8@"
        )
        self.user2 = User.objects.create_user(
            username="jason",
            email="jason@qq.com",
            password="Ironman@8@"
        )
        self.contact = Contact.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        self.company = Company.objects.create(
            company_name="Example Corp",
            email="contact@example.com"
        )
        self.product = Product.objects.create(
            product_name="Product A",
            product_code="P001",
            product_type="Type A"
        )
        self.pipeline = Pipeline.objects.create(
            pipeline_name="Sales Pipeline"
        )
        self.stage = Stage.objects.create(
            stage_name="Initial Contact",
            pipeline=self.pipeline,
        )
        self.deal = Deal.objects.create(
            deal_name="Deal 1",
            contact=self.contact,
            pipeline=self.pipeline,
            amount=10000,
            expected_revenue=8000,
            closing_date=timezone.now()
        )
        self.contract = Contract.objects.create(
            contract_code="Contract_001",
            contract_date=timezone.now().date(),
            deal=self.deal
        )
        self.order = Order.objects.create(
            order_code="Order_001",
            contract=self.contract,
            etd=timezone.now().date()
        )
        self.order2 = Order.objects.create(
            order_code="Order_002",
            contract=self.contract,
            etd=timezone.now().date()
        )
        self.order_product = OrderProduct.objects.create(product_name="Product A", quantity=2, order=self.order)
        self.contact_content_type = ContentType.objects.get_for_model(self.contact)

        # Active and inactive custom fields
        self.active_field = Field.objects.create(
            field_name="Active Custom Field",
            field_type="text",
            content_type=self.contact_content_type,
            is_active=True
        )
        self.inactive_field = Field.objects.create(
            field_name="Inactive Custom Field",
            field_type="text",
            content_type=self.contact_content_type,
            is_active=False
        )

        # Create CustomFieldValues
        CustomFieldValue.objects.create(
            field=self.active_field,
            value="Active Value",
            content_object=self.contact
        )
        CustomFieldValue.objects.create(
            field=self.inactive_field,
            value="Inactive Value",
            content_object=self.contact
        )

    def test_contact_serialization(self):
        serializer = ContactSerializer(self.contact)
        print(serializer.data)
        self.assertEqual(serializer.data['first_name'], "John")
        self.assertEqual(serializer.data['last_name'], "Doe")
        self.assertEqual(serializer.data['email'], "john.doe@example.com")
        custom_fields = serializer.data.get('custom_fields', [])
        self.assertIn('custom_fields', serializer.data)
        self.assertEqual(len(custom_fields), 1)  # Only active custom field should be serialized
        self.assertEqual(custom_fields[0]['value'], "Active Value")

    def test_company_serialization(self):
        serializer = CompanySerializer(self.company)
        self.assertEqual(serializer.data['company_name'], "Example Corp")
        self.assertEqual(serializer.data['email'], "contact@example.com")

    # def test_product_serialization(self):
    #     serializer = ProductSerializer(self.product)
    #     self.assertEqual(serializer.data['product_name'], "Product A")
    #     self.assertEqual(serializer.data['product_code'], "P001")

    def test_pipeline_serialization(self):
        serializer = PipelineSerializer(self.pipeline)
        self.assertEqual(serializer.data['pipeline_name'], "Sales Pipeline")

    def test_stage_serialization(self):
        serializer = StageSerializer(self.stage)
        self.assertEqual(serializer.data['stage_name'], "Initial Contact")
        self.assertEqual(serializer.data['pipeline'], self.pipeline.id)

    def test_deal_serialization(self):
        serializer = DealSerializer(self.deal)
        print(serializer.data)
        self.assertEqual(serializer.data['deal_name'], "Deal 1")
        self.assertEqual(serializer.data['amount'], "10000.00")
        self.assertEqual(serializer.data['contact']['first_name'], "John")
        self.assertEqual(serializer.data['company']['company_name'], "Example Corp")

    def test_contact_nested_create(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'owner': 'coolister'
        }
        serializer = ContactSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        contact = serializer.save()
        self.assertEqual(contact.first_name, 'Jane')
        self.assertEqual(contact.owner.username, 'coolister')

        new_data = {
            'owner': 'jason'
        }
        serializer = ContactSerializer(contact, data=new_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_contact = serializer.save()
        self.assertEqual(updated_contact.first_name, 'Jane')
        self.assertEqual(updated_contact.owner.username, 'jason')

    def test_custom_fields_create(self):
        """Test creating a contact with custom fields"""
        new_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'custom_fields': [
                {'field': self.active_field.id, 'value': 'New Custom Value'}
            ]
        }

        serializer = ContactSerializer(data=new_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        contact = serializer.save()

        # Verify the contact is created with the correct custom field value
        self.assertEqual(contact.first_name, "Jane")
        self.assertEqual(contact.custom_fields.count(), 1)
        custom_field_value = contact.custom_fields.first()
        self.assertEqual(custom_field_value.value, "New Custom Value")
        self.assertEqual(custom_field_value.field, self.active_field)

    def test_custom_fields_update(self):
        """Test updating a contact with custom fields"""
        update_data = {
            'first_name': 'Updated John',
            'custom_fields': [
                {'field_id': self.active_field.id, 'value': 'Updated Active Value'}
            ]
        }

        serializer = ContactSerializer(self.contact, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_contact = serializer.save()

        # Verify the contact is updated correctly
        self.assertEqual(updated_contact.first_name, "Updated John")

        # Verify the custom field value has been updated
        custom_field_value = updated_contact.custom_fields.get(field=self.active_field)
        self.assertEqual(custom_field_value.value, "Updated Active Value")

    def test_custom_fields_create_and_update(self):
        """Test workflow create field, create contact with custom field, update contact"""
        custom_field_data = {
            "field_name": "bank account",
            "field_type": "text",
            "field_tag": "",
            "is_active": True,
            "is_mandatory": False,
            "content_type": "contact",
            "extra_info": None
        }
        field_serializer = FieldSerializer(data=custom_field_data)
        self.assertTrue(field_serializer.is_valid(), field_serializer.errors)
        custom_field = field_serializer.save()

        # Verify the custom field is created correctly
        self.assertEqual(custom_field.field_name, "bank account")
        self.assertEqual(custom_field.content_type.model, "contact")
        self.assertEqual(custom_field.extra_info, None)

        contact_data = {
            "first_name": "Steven",
            "last_name": "Song",
            "title": "Sale",
            "email": "steven.song@gmail.com",
            "mobile": "",
            "phone": "",
            "custom_fields": [
                {"field_name": "bank account", "value": "00000001"}
            ]
        }
        contact_serializer = ContactSerializer(data=contact_data)
        self.assertTrue(contact_serializer.is_valid(), contact_serializer.errors)
        contact = contact_serializer.save()

        # Verify the contact with custom field is created correctly
        self.assertEqual(contact.email, "steven.song@gmail.com")
        self.assertEqual(contact.custom_fields.all()[0].value, "00000001")
        self.assertEqual(contact.custom_fields.all()[0].field, custom_field)

        contact_data_updated = {
            "custom_fields": [
                {"field_name": "bank account", "value": "00000002"}
            ]
        }
        updated_at = contact.updated_at
        contact_serializer = ContactSerializer(contact, data=contact_data_updated, partial=True)
        self.assertTrue(contact_serializer.is_valid(), contact_serializer.errors)
        contact = contact_serializer.save()

        # Verify the contact with custom field is updated correctly
        self.assertNotEqual(contact.updated_at, updated_at)
        self.assertEqual(contact.custom_fields.all()[0].value, "00000002")

    def validate_nested_data(self, data, expected_values):
        """Helper function to validate nested fields in the response data."""
        for field, expected in expected_values.items():
            if isinstance(expected, dict):
                self.validate_nested_data(data[field], expected)
            elif isinstance(expected, list):
                self.validate_nested_data(data[field][0], expected[0])
            else:
                self.assertEqual(data.get(field), expected)

    def test_deal_nested_serialization(self):
        serializer = DealSerializer(self.deal)
        expected_data = {
            'deal_name': "Deal 1",
            'contact': {'first_name': "John", 'last_name': "Doe", 'email': "john.doe@example.com"},
            'contract': {'contract_code': "Contract_001", 'orders': [{'order_code': "Order_001"}]},
        }
        self.validate_nested_data(serializer.data, expected_data)

    def test_deal_nested_creation(self):
        data = {
            "owner": {"pk": 1},
            "deal_name": "New Deal",
            "closing_date": "2024-10-10",
            "contact": {"pk": 1},
            "contract": {
                "contract_code": "Contract_002",
                "contract_date": "2024-01-01",
                "orders": [
                    {
                        "order_code": "Order_002",
                        "etd": "2024-01-01",
                        "products": [
                            {"product_name": "Product B", "quantity": 5}
                        ]
                    }
                ]
            }
        }
        serializer = DealSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        deal = serializer.save()

        # 验证数据
        self.assertEqual(deal.deal_name, "New Deal")
        self.assertEqual(deal.contact.first_name, "John")
        self.assertEqual(deal.contract.contract_code, "Contract_002")
        self.assertEqual(deal.contract.orders.first().order_code, "Order_002")

    def test_contract_nested_update(self):
        update_data = {
            "pk": self.contract.pk,
            "contract_code": self.contract.contract_code,
            "contract_date": self.contract.contract_date,
            "orders": [
                {
                    "order_code": "Order_003",
                    "etd": "2024-01-01",
                    "products": [
                        {"product_name": "Product A Updated", "quantity": 3}
                    ]
                }
            ]
        }

        # Use ContractSerializer to process the data
        serializer = ContractSerializer(self.contract, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_contract = serializer.save()

        # Check if the new order was added and old ones remain the same, when partial is set to True
        self.assertEqual(updated_contract.orders.count(), 3)

    def test_deal_nested_update(self):
        update_data = {
            "deal_name": "Updated Deal",
            "contact": {"first_name": "Jane Updated"},
            "contract": {
                "orders": [
                    {
                        "etd": "2024-01-01",
                        "order_code": "Order_002",
                        "products": [{"product_name": "Product A Updated", "quantity": 3}]
                    }
                ]
            }
        }

        serializer = DealSerializer(self.deal, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_deal = serializer.save()

        # 验证更新数据
        self.assertEqual(updated_deal.deal_name, "Updated Deal")
        self.assertEqual(updated_deal.contact.first_name, "Jane Updated")
        self.assertEqual(updated_deal.contract.contract_code, "Contract_001")
        self.assertEqual(updated_deal.contract.orders.count(), 3)
        order_product = updated_deal.contract.orders.order_by('-pk').first()
        self.assertEqual(order_product.order_code, "Order_002")

    def test_nested_field_validation_error(self):
        invalid_data = {
            "deal_name": "Invalid Deal",
            "contract": {
                "contract_code": "Contract 003",
                "contract_date": "2024-10-10",
                "orders": [
                    {
                        "order_code": "Order_003",
                        "etd": "2024-01-01",
                        "products": [{"quantity": 1}]}  # 缺少 product_name
                ]
            }
        }
        serializer = DealSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contract', serializer.errors)
        self.assertIn('products', serializer.errors['contract']['orders'][0])
