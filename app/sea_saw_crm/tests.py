# class SerializerTests(APITestCase):
#
#     def setUp(self):
#         # Create sample data for testing
#         self.user = User.objects.create_user(
#             username="coolister",
#             email="coolister@qq.com",
#             password="Ironman@8@"
#         )
#         self.user2 = User.objects.create_user(
#             username="jason",
#             email="jason@qq.com",
#             password="Ironman@8@"
#         )
#         self.contact = Contact.objects.create(
#             first_name="John",
#             last_name="Doe",
#             email="john.doe@example.com"
#         )
#         self.company = Company.objects.create(
#             company_name="Example Corp",
#             email="contact@example.com"
#         )
#         self.product = OrderProduct.objects.create(
#             product_name="Product A",
#             product_code="P001",
#             product_type="Type A"
#         )
#         self.contract = Contract.objects.create(
#             contract_code="Contract_001",
#             contract_date=timezone.now().date(),
#         )
#         self.order = Order.objects.create(
#             order_code="Order_001",
#             contract=self.contract,
#             etd=timezone.now().date()
#         )
#         self.order2 = Order.objects.create(
#             order_code="Order_002",
#             contract=self.contract,
#             etd=timezone.now().date()
#         )
#         self.order_product = OrderProduct.objects.create(product_name="Product A", quantity=2, order=self.order)
#         self.contact_content_type = ContentType.objects.get_for_model(self.contact)
#
#         # Active and inactive custom fields
#         self.active_field = Field.objects.create(
#             field_name="Active Custom Field",
#             field_type="text",
#             content_type=self.contact_content_type,
#             is_active=True
#         )
#         self.inactive_field = Field.objects.create(
#             field_name="Inactive Custom Field",
#             field_type="text",
#             content_type=self.contact_content_type,
#             is_active=False
#         )
#
#     def test_contact_serialization(self):
#         serializer = ContactSerializer(self.contact)
#         print(serializer.data)
#         self.assertEqual(serializer.data['first_name'], "John")
#         self.assertEqual(serializer.data['last_name'], "Doe")
#         self.assertEqual(serializer.data['email'], "john.doe@example.com")
#         custom_fields = serializer.data.get('custom_fields', [])
#         self.assertIn('custom_fields', serializer.data)
#         self.assertEqual(len(custom_fields), 1)  # Only active custom field should be serialized
#         self.assertEqual(custom_fields[0]['value'], "Active Value")
#
#     def test_company_serialization(self):
#         serializer = CompanySerializer(self.company)
#         self.assertEqual(serializer.data['company_name'], "Example Corp")
#         self.assertEqual(serializer.data['email'], "contact@example.com")
#
#     def test_contact_nested_create(self):
#         data = {
#             'first_name': 'Jane',
#             'last_name': 'Smith',
#             'email': 'jane.smith@example.com',
#             'owner': 'coolister'
#         }
#         serializer = ContactSerializer(data=data)
#         self.assertTrue(serializer.is_valid(), serializer.errors)
#         contact = serializer.save()
#         self.assertEqual(contact.first_name, 'Jane')
#         self.assertEqual(contact.owner.username, 'coolister')
#
#         new_data = {
#             'owner': 'jason'
#         }
#         serializer = ContactSerializer(contact, data=new_data, partial=True)
#         self.assertTrue(serializer.is_valid(), serializer.errors)
#         updated_contact = serializer.save()
#         self.assertEqual(updated_contact.first_name, 'Jane')
#         self.assertEqual(updated_contact.owner.username, 'jason')
#
#     def test_custom_fields_create(self):
#         """Test creating a contact with custom fields"""
#         new_data = {
#             'first_name': 'Jane',
#             'last_name': 'Smith',
#             'email': 'jane.smith@example.com',
#             'custom_fields': [
#                 {'field': self.active_field.id, 'value': 'New Custom Value'}
#             ]
#         }
#
#         serializer = ContactSerializer(data=new_data)
#         self.assertTrue(serializer.is_valid(), serializer.errors)
#         contact = serializer.save()
#
#         # Verify the contact is created with the correct custom field value
#         self.assertEqual(contact.first_name, "Jane")
#         self.assertEqual(contact.custom_fields.count(), 1)
#         custom_field_value = contact.custom_fields.first()
#         self.assertEqual(custom_field_value.value, "New Custom Value")
#         self.assertEqual(custom_field_value.field, self.active_field)
#
#     def test_custom_fields_update(self):
#         """Test updating a contact with custom fields"""
#         update_data = {
#             'first_name': 'Updated John',
#             'custom_fields': [
#                 {'field_id': self.active_field.id, 'value': 'Updated Active Value'}
#             ]
#         }
#
#         serializer = ContactSerializer(self.contact, data=update_data, partial=True)
#         self.assertTrue(serializer.is_valid(), serializer.errors)
#         updated_contact = serializer.save()
#
#         # Verify the contact is updated correctly
#         self.assertEqual(updated_contact.first_name, "Updated John")
#
#         # Verify the custom field value has been updated
#         custom_field_value = updated_contact.custom_fields.get(field=self.active_field)
#         self.assertEqual(custom_field_value.value, "Updated Active Value")
#
#     def test_custom_fields_create_and_update(self):
#         """Test workflow create field, create contact with custom field, update contact"""
#         custom_field_data = {
#             "field_name": "bank account",
#             "field_type": "text",
#             "field_tag": "",
#             "is_active": True,
#             "is_mandatory": False,
#             "content_type": "contact",
#             "extra_info": None
#         }
#         field_serializer = FieldSerializer(data=custom_field_data)
#         self.assertTrue(field_serializer.is_valid(), field_serializer.errors)
#         custom_field = field_serializer.save()
#
#         # Verify the custom field is created correctly
#         self.assertEqual(custom_field.field_name, "bank account")
#         self.assertEqual(custom_field.content_type.model, "contact")
#         self.assertEqual(custom_field.extra_info, None)
#
#         contact_data = {
#             "first_name": "Steven",
#             "last_name": "Song",
#             "title": "Sale",
#             "email": "steven.song@gmail.com",
#             "mobile": "",
#             "phone": "",
#             "custom_fields": [
#                 {"field_name": "bank account", "value": "00000001"}
#             ]
#         }
#         contact_serializer = ContactSerializer(data=contact_data)
#         self.assertTrue(contact_serializer.is_valid(), contact_serializer.errors)
#         contact = contact_serializer.save()
#
#         # Verify the contact with custom field is created correctly
#         self.assertEqual(contact.email, "steven.song@gmail.com")
#         self.assertEqual(contact.custom_fields.all()[0].value, "00000001")
#         self.assertEqual(contact.custom_fields.all()[0].field, custom_field)
#
#         contact_data_updated = {
#             "custom_fields": [
#                 {"field_name": "bank account", "value": "00000002"}
#             ]
#         }
#         updated_at = contact.updated_at
#         contact_serializer = ContactSerializer(contact, data=contact_data_updated, partial=True)
#         self.assertTrue(contact_serializer.is_valid(), contact_serializer.errors)
#         contact = contact_serializer.save()
#
#         # Verify the contact with custom field is updated correctly
#         self.assertNotEqual(contact.updated_at, updated_at)
#         self.assertEqual(contact.custom_fields.all()[0].value, "00000002")
#
#     def validate_nested_data(self, data, expected_values):
#         """Helper function to validate nested fields in the response data."""
#         for field, expected in expected_values.items():
#             if isinstance(expected, dict):
#                 self.validate_nested_data(data[field], expected)
#             elif isinstance(expected, list):
#                 self.validate_nested_data(data[field][0], expected[0])
#             else:
#                 self.assertEqual(data.get(field), expected)
#
#     def test_contract_nested_update(self):
#         update_data = {
#             "pk": self.contract.pk,
#             "contract_code": self.contract.contract_code,
#             "contract_date": self.contract.contract_date,
#             "orders": [
#                 {
#                     "order_code": "Order_003",
#                     "etd": "2024-01-01",
#                     "products": [
#                         {"product_name": "Product A Updated", "quantity": 3}
#                     ]
#                 }
#             ]
#         }
#
#         # Use ContractSerializer to process the data
#         serializer = ContractSerializer(self.contract, data=update_data, partial=True)
#         self.assertTrue(serializer.is_valid(), serializer.errors)
#         updated_contract = serializer.save()
#
#         # Check if the new order was added and old ones remain the same, when partial is set to True
#         self.assertEqual(updated_contract.orders.count(), 3)

# class FlattenContractFunctionTests(APITestCase):
#
#     def setUp(self):
#         # Create sample data for testing
#         self.contract = Contract.objects.create(
#             contract_code="C001",
#             contract_date=timezone.now().date(),
#         )
#
#         self.order1 = Order.objects.create(
#             order_code="O001",
#             etd=timezone.now().date(),
#             contract=self.contract
#         )
#
#         self.order2 = Order.objects.create(
#             order_code="O002",
#             etd=timezone.now().date(),
#             contract=self.contract
#         )
#
#         self.product1 = OrderProduct.objects.create(
#             product_name="Product A",
#             product_code="P001",
#             product_type="Type A",
#             quantity=10,
#             order=self.order1
#         )
#
#         self.product2 = OrderProduct.objects.create(
#             product_name="Product B",
#             product_code="P002",
#             product_type="Type B",
#             quantity=5,
#             order=self.order2
#         )
#
#     def test_flatten_contract(self):
#         """
#         Test the flatten function to ensure it properly flattens nested serialized data for contracts.
#         """
#         queryset = Contract.objects.all()
#         serializer = ContractSerializer
#         flattened_data, flattened_header = flatten(queryset, serializer)
#
#         print("flattened_data", flattened_data)
#         print("flatttened_header", flattened_header)
#
#         # Check if the data is flattened correctly
#         self.assertIsInstance(flattened_data, list)
#         self.assertEqual(len(flattened_data), 1)  # Only one contract in the test data
#
#         # Verify the flattened contract data
#         contract_data = flattened_data[0]
#         self.assertIn('contract_code', contract_data)
#         self.assertIn('contract_date', contract_data)
#         self.assertIn('orders.order_code', contract_data)
#         self.assertIn('orders.products.product_name', contract_data)
#
#         self.assertEqual(contract_data['contract_code'], "C001")
#         self.assertEqual(contract_data['orders.order_code'][0], "O001")
#         self.assertEqual(contract_data['orders.products.product_name'][0][0], "Product A")
#         self.assertEqual(contract_data['orders.products.product_name'][1][0], "Product B")
#
#         # Verify the second order and its products
#         self.assertEqual(contract_data['orders.order_code'][1], "O002")
