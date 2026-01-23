# OrderModelManager Usage Guide

## Overview

The `OrderModelManager` provides automatic synchronization between Order and Pipeline models. When you update an Order using the manager's methods, the related Pipeline fields are automatically updated to maintain data consistency.

## Features

- **Automatic Pipeline Sync**: Updates to Order automatically propagate to its Pipeline
- **Single & Bulk Updates**: Support for both individual and batch updates
- **User Tracking**: Maintains audit trail with `updated_by` field
- **Safe Operations**: No errors if Order doesn't have a Pipeline

## Synced Fields

The following Order fields automatically sync to Pipeline:

| Order Field | Pipeline Field | Description |
|------------|----------------|-------------|
| `contact` | `contact` | Customer contact |
| `order_date` | `order_date` | Order date |
| `total_amount` | `total_amount` | Total amount |

## Usage Examples

### 1. Update Single Order by ID

```python
from sea_saw_crm.models.order import Order

# Update order and sync pipeline
updated_order = Order.objects.update_with_pipeline(
    order_id=5,
    user=request.user,
    contact=new_contact,
    order_date=date(2026, 2, 1),
    total_amount=Decimal("1500.00")
)
```

### 2. Update Single Order by Instance

```python
from sea_saw_crm.models.order import Order

# Get the order
order = Order.objects.get(order_code="SO2026-000001")

# Update and sync
updated_order = Order.objects.update_with_pipeline(
    instance=order,
    user=request.user,
    status='confirmed',
    total_amount=Decimal("2000.00")
)
```

### 3. Bulk Update Multiple Orders

```python
from sea_saw_crm.models.order import Order

# Get orders to update
orders = Order.objects.filter(status='draft')

# Bulk update and sync all pipelines
count = Order.objects.bulk_update_with_pipeline(
    queryset=orders,
    user=request.user,
    status='pending',
    order_date=date(2026, 1, 20)
)

print(f"Updated {count} orders and synced their pipelines")
```

### 4. Update in Django REST Framework ViewSet

```python
from rest_framework.viewsets import ModelViewSet
from sea_saw_crm.models.order import Order

class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()

    def perform_update(self, serializer):
        # Use update_with_pipeline instead of default save
        Order.objects.update_with_pipeline(
            instance=serializer.instance,
            user=self.request.user,
            **serializer.validated_data
        )
```

### 5. Update Without User Tracking (Not Recommended)

```python
# Will still sync pipeline but won't track updated_by
updated_order = Order.objects.update_with_pipeline(
    order_id=5,
    total_amount=Decimal("1500.00")
)
```

## Important Notes

### Required Parameters

- **Either** `order_id` **or** `instance` must be provided
- If neither is provided, `ValueError` will be raised

```python
# ❌ This will raise ValueError
Order.objects.update_with_pipeline(
    user=request.user,
    total_amount=Decimal("1000.00")
)

# ✅ This is correct
Order.objects.update_with_pipeline(
    order_id=5,
    user=request.user,
    total_amount=Decimal("1000.00")
)
```

### Behavior Without Pipeline

If an Order doesn't have a related Pipeline, the update will still work normally without errors:

```python
# Order without pipeline - no error
order_no_pipeline = Order.objects.create(order_code="SO2026-999")
Order.objects.update_with_pipeline(
    instance=order_no_pipeline,
    total_amount=Decimal("500.00")
)
```

### Transaction Safety

All operations are wrapped in `@transaction.atomic`, ensuring that either both Order and Pipeline are updated, or neither is (rollback on error).

### Performance Considerations

For bulk updates:
- The method uses `queryset.update()` for Orders (single query)
- Then iterates through Orders to sync Pipelines individually
- Each Pipeline sync only updates if fields actually changed
- Consider batch size for very large querysets

## Integration with Existing Code

The manager extends `BaseModelManager`, so all existing functionality is preserved:

```python
# Standard create methods still work
order = Order.objects.create(order_code="SO2026-001")
order = Order.objects.create_with_user(user=request.user, order_code="SO2026-002")

# New update_with_pipeline method
Order.objects.update_with_pipeline(instance=order, user=request.user, status='confirmed')
```

## Testing

Run tests to verify the functionality:

```bash
cd sea-saw-server
python manage.py test sea_saw_crm.tests.test_order_manager
```

## Migration Guide

### Before (Manual Sync)

```python
# Old way - manual sync
order.total_amount = Decimal("1500.00")
order.save()

# Manually sync pipeline
if hasattr(order, 'pipeline') and order.pipeline:
    pipeline = order.pipeline
    pipeline.total_amount = order.total_amount
    pipeline.save()
```

### After (Automatic Sync)

```python
# New way - automatic sync
Order.objects.update_with_pipeline(
    instance=order,
    user=request.user,
    total_amount=Decimal("1500.00")
)
```

## Future Enhancements

Potential improvements:
- Signal-based auto-sync on any Order save
- Configurable sync field mapping
- Async bulk update for very large datasets
- Bidirectional sync (Pipeline → Order)
