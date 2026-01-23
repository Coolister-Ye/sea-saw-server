"""
Tests for OrderModelManager - Order update with Pipeline synchronization
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date

from ..models.order import Order
from ..models.pipeline import Pipeline
from ..models.contact import Contact
from ..models.company import Company

User = get_user_model()


class OrderModelManagerTestCase(TestCase):
    """Test Order Manager's update_with_pipeline functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

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
            contact=self.contact1,
            total_amount=Decimal("1000.00")
        )

        # Create pipeline linked to order
        self.pipeline = Pipeline.objects.create_with_user(
            user=self.user,
            order=self.order,
            pipeline_code="PL2026-000001",
            contact=self.contact1,
            order_date=date(2026, 1, 15),
            total_amount=Decimal("1000.00")
        )

    def test_update_with_pipeline_by_id(self):
        """Test updating order by ID syncs pipeline"""
        new_date = date(2026, 1, 20)
        new_amount = Decimal("1500.00")

        updated_order = Order.objects.update_with_pipeline(
            order_id=self.order.id,
            user=self.user,
            order_date=new_date,
            total_amount=new_amount
        )

        # Refresh pipeline from database
        self.pipeline.refresh_from_db()

        # Verify order was updated
        self.assertEqual(updated_order.order_date, new_date)
        self.assertEqual(updated_order.total_amount, new_amount)

        # Verify pipeline was synced
        self.assertEqual(self.pipeline.order_date, new_date)
        self.assertEqual(self.pipeline.total_amount, new_amount)

    def test_update_with_pipeline_by_instance(self):
        """Test updating order by instance syncs pipeline"""
        updated_order = Order.objects.update_with_pipeline(
            instance=self.order,
            user=self.user,
            contact=self.contact2
        )

        # Refresh pipeline from database
        self.pipeline.refresh_from_db()

        # Verify order was updated
        self.assertEqual(updated_order.contact, self.contact2)

        # Verify pipeline was synced
        self.assertEqual(self.pipeline.contact, self.contact2)

    def test_update_with_pipeline_multiple_fields(self):
        """Test updating multiple fields syncs all to pipeline"""
        new_date = date(2026, 2, 1)
        new_amount = Decimal("2000.00")

        Order.objects.update_with_pipeline(
            instance=self.order,
            user=self.user,
            contact=self.contact2,
            order_date=new_date,
            total_amount=new_amount
        )

        # Refresh pipeline from database
        self.pipeline.refresh_from_db()

        # Verify all fields were synced
        self.assertEqual(self.pipeline.contact, self.contact2)
        self.assertEqual(self.pipeline.order_date, new_date)
        self.assertEqual(self.pipeline.total_amount, new_amount)

    def test_update_with_pipeline_no_pipeline(self):
        """Test updating order without pipeline doesn't raise error"""
        # Create order without pipeline
        order_no_pipeline = Order.objects.create_with_user(
            user=self.user,
            order_code="SO2026-000002",
            order_date=date(2026, 1, 16)
        )

        # Should not raise error
        updated_order = Order.objects.update_with_pipeline(
            instance=order_no_pipeline,
            user=self.user,
            total_amount=Decimal("500.00")
        )

        self.assertEqual(updated_order.total_amount, Decimal("500.00"))

    def test_update_with_pipeline_no_changes(self):
        """Test updating with same values doesn't trigger unnecessary saves"""
        # Update with same values
        Order.objects.update_with_pipeline(
            instance=self.order,
            user=self.user,
            order_date=self.order.order_date,
            total_amount=self.order.total_amount
        )

        # Pipeline should remain unchanged
        self.pipeline.refresh_from_db()
        self.assertEqual(self.pipeline.order_date, self.order.order_date)
        self.assertEqual(self.pipeline.total_amount, self.order.total_amount)

    def test_update_with_pipeline_raises_without_id_or_instance(self):
        """Test that ValueError is raised if neither order_id nor instance is provided"""
        with self.assertRaises(ValueError) as context:
            Order.objects.update_with_pipeline(
                user=self.user,
                total_amount=Decimal("1000.00")
            )

        self.assertIn("Either order_id or instance must be provided", str(context.exception))

    def test_bulk_update_with_pipeline(self):
        """Test bulk updating orders syncs their pipelines"""
        # Create another order with pipeline
        order2 = Order.objects.create_with_user(
            user=self.user,
            order_code="SO2026-000003",
            order_date=date(2026, 1, 17),
            total_amount=Decimal("800.00")
        )
        pipeline2 = Pipeline.objects.create_with_user(
            user=self.user,
            order=order2,
            pipeline_code="PL2026-000002",
            order_date=date(2026, 1, 17),
            total_amount=Decimal("800.00")
        )

        # Bulk update both orders
        new_date = date(2026, 1, 25)
        queryset = Order.objects.filter(id__in=[self.order.id, order2.id])
        count = Order.objects.bulk_update_with_pipeline(
            queryset=queryset,
            user=self.user,
            order_date=new_date
        )

        # Verify count
        self.assertEqual(count, 2)

        # Refresh pipelines
        self.pipeline.refresh_from_db()
        pipeline2.refresh_from_db()

        # Verify both pipelines were synced
        self.assertEqual(self.pipeline.order_date, new_date)
        self.assertEqual(pipeline2.order_date, new_date)

    def test_user_tracking_in_pipeline_update(self):
        """Test that updated_by is tracked in pipeline when syncing"""
        Order.objects.update_with_pipeline(
            instance=self.order,
            user=self.user,
            total_amount=Decimal("1200.00")
        )

        # Refresh pipeline
        self.pipeline.refresh_from_db()

        # Verify updated_by was set
        self.assertEqual(self.pipeline.updated_by, self.user)
