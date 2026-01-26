"""
Tests for OrderViewSet and NestedOrderViewSet - Pipeline synchronization in API updates
"""

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from datetime import date

from ..models.order import Order
from ..models.pipeline import Pipeline
from ..models.contact import Contact
from ..models.company import Company
from sea_saw_auth.models import Role

User = get_user_model()


class OrderViewSetPipelineSyncTestCase(TestCase):
    """Test Order API updates automatically sync to Pipeline"""

    def setUp(self):
        """Set up test data"""
        # Create admin role
        self.role = Role.objects.create(
            role_name="Admin Role",
            role_type="ADMIN"
        )

        # Create test user with admin role
        self.user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            role=self.role
        )

        # Create API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create test company
        self.company = Company.objects.create(
            company_name="Test Company",
            created_by=self.user
        )

        # Create test contacts
        self.contact1 = Contact.objects.create(
            name="John Doe",
            company=self.company,
            created_by=self.user
        )
        self.contact2 = Contact.objects.create(
            name="Jane Smith",
            company=self.company,
            created_by=self.user
        )

        # Create test order
        self.order = Order.objects.create_with_user(
            user=self.user,
            order_code="SO2026-000001",
            order_date=date(2026, 1, 15),
            contact=self.contact1
        )

        # Create pipeline linked to order
        self.pipeline = Pipeline.objects.create_with_user(
            user=self.user,
            order=self.order,
            pipeline_code="PL2026-000001",
            contact=self.contact1
        )

    def test_standalone_order_update_syncs_pipeline(self):
        """Test standalone Order API update syncs pipeline"""
        update_data = {
            "contact_id": self.contact2.id,  # Use contact_id instead of contact
            "order_date": "2026-02-01"
        }

        response = self.client.patch(
            f"/api/sea-saw-crm/orders/{self.order.id}/",
            data=update_data,
            format="json"
        )

        self.assertEqual(response.status_code, 200, f"Response: {response.data}")

        # Refresh from database
        self.order.refresh_from_db()
        self.pipeline.refresh_from_db()

        # Verify order was updated
        self.assertEqual(self.order.contact.id, self.contact2.id)
        self.assertEqual(str(self.order.order_date), "2026-02-01")

        # Verify pipeline was synced
        self.assertEqual(self.pipeline.contact.id, self.contact2.id)
        self.assertEqual(str(self.pipeline.order_date), "2026-02-01")

    def test_nested_order_update_syncs_pipeline(self):
        """Test nested Order API update syncs pipeline"""
        update_data = {
            "contact_id": self.contact2.id
        }

        response = self.client.patch(
            f"/api/sea-saw-crm/nested-orders/{self.order.id}/?related_pipeline={self.pipeline.id}",
            data=update_data,
            format="json"
        )

        # Print response for debugging if not 200
        if response.status_code != 200:
            print(f"Status: {response.status_code}, Data: {response.data}")

        self.assertEqual(response.status_code, 200)

        # Refresh from database
        self.order.refresh_from_db()
        self.pipeline.refresh_from_db()

        # Verify order and pipeline were synced
        self.assertEqual(self.order.contact.id, self.contact2.id)
        self.assertEqual(self.pipeline.contact.id, self.contact2.id)

    def test_partial_update_only_syncs_changed_fields(self):
        """Test partial update only syncs fields that changed"""
        # Only update contact, not other fields
        update_data = {
            "contact_id": self.contact2.id  # Use contact_id instead of contact
        }

        response = self.client.patch(
            f"/api/sea-saw-crm/orders/{self.order.id}/",
            data=update_data,
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        # Refresh from database
        self.pipeline.refresh_from_db()

        # Verify only contact was synced, other fields unchanged
        self.assertEqual(self.pipeline.contact.id, self.contact2.id)
        self.assertEqual(self.pipeline.order_date, date(2026, 1, 15))

    def test_update_order_without_pipeline_no_error(self):
        """Test updating order without pipeline doesn't cause errors"""
        # Create order without pipeline
        order_no_pipeline = Order.objects.create_with_user(
            user=self.user,
            order_code="SO2026-000002",
            order_date=date(2026, 1, 16)
        )

        update_data = {
            "contact_id": self.contact1.id  # Use contact_id instead of contact
        }

        response = self.client.patch(
            f"/api/sea-saw-crm/orders/{order_no_pipeline.id}/",
            data=update_data,
            format="json"
        )

        # Should succeed without errors
        self.assertEqual(response.status_code, 200)

        # Verify order was updated
        order_no_pipeline.refresh_from_db()
        self.assertEqual(order_no_pipeline.contact.id, self.contact1.id)

    def test_nested_update_prevents_pipeline_reassignment(self):
        """Test nested endpoint prevents changing related_pipeline"""
        # Create another order and pipeline
        other_order = Order.objects.create_with_user(
            user=self.user,
            order_code="SO2026-000003",
            order_date=date(2026, 1, 17),
            contact=self.contact1
        )

        other_pipeline = Pipeline.objects.create_with_user(
            user=self.user,
            order=other_order,
            pipeline_code="PL2026-000002"
        )

        update_data = {
            "contact_id": self.contact2.id
        }

        # Try to update original order with different pipeline ID
        response = self.client.patch(
            f"/api/sea-saw-crm/nested-orders/{self.order.id}/?related_pipeline={other_pipeline.id}",
            data=update_data,
            format="json"
        )

        # Should return 404 because the order doesn't belong to other_pipeline
        # This is the expected behavior: queryset filtering prevents cross-pipeline updates
        self.assertEqual(response.status_code, 404)
        self.assertIn("No Order matches the given query", str(response.data['detail']))

    def test_full_workflow_order_to_pipeline_sync(self):
        """Test complete workflow: create order, create pipeline, update order, verify sync"""
        # Create new order
        new_order = Order.objects.create_with_user(
            user=self.user,
            order_code="SO2026-999",
            order_date=date(2026, 1, 20),
            contact=self.contact1
        )

        # Create pipeline for the order
        new_pipeline = Pipeline.objects.create_with_user(
            user=self.user,
            order=new_order,
            pipeline_code="PL2026-999",
            contact=self.contact1,
            order_date=date(2026, 1, 20)
        )

        # Update order via API
        update_data = {
            "contact_id": self.contact2.id,  # Use contact_id instead of contact
            "order_date": "2026-01-25"
        }

        response = self.client.patch(
            f"/api/sea-saw-crm/orders/{new_order.id}/",
            data=update_data,
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        # Verify complete sync
        new_order.refresh_from_db()
        new_pipeline.refresh_from_db()

        self.assertEqual(new_pipeline.contact.id, self.contact2.id)
        self.assertEqual(str(new_pipeline.order_date), "2026-01-25")
