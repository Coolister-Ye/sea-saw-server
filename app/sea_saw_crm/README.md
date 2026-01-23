# Sea-Saw CRM Application

Django-based CRM system for managing companies, contacts, orders, production, and payments.

## 📁 Project Structure

```
sea_saw_crm/
├── __init__.py
├── apps.py                          # App configuration
├── urls.py                          # URL routing
├── pagination.py                    # Pagination settings
├── filters.py                       # Django filters
├── filtersets.py                    # Filter configurations
├── fixtures.py                      # Test fixtures
│
├── admin/                           # Django admin customization
│   ├── __init__.py
│   ├── company.py
│   ├── contact.py
│   ├── order.py
│   ├── payment.py
│   ├── production.py
│   └── ...
│
├── constants/                       # Application constants
│   ├── __init__.py
│   ├── currency.py
│   ├── payment.py
│   └── ...
│
├── docs/                           # Documentation
│   ├── README.md
│   └── FILE_UPLOAD_GUIDE.md       # File upload configuration guide
│
├── fixtures/                       # Database fixtures
│   └── initial_data.json
│
├── manager/                        # Custom model managers
│   ├── __init__.py
│   └── ...
│
├── metadata/                       # DRF metadata classes
│   ├── __init__.py
│   └── base.py
│
├── migrations/                     # Database migrations
│   ├── __init__.py
│   ├── 0001_initial.py
│   ├── 0002_...
│   ├── 0003_...
│   └── 0004_update_file_upload_paths.py
│
├── mixins/                         # Reusable mixins
│   ├── __init__.py
│   ├── multipart_nested.py
│   └── return_related_mixin.py
│
├── models/                         # Database models
│   ├── __init__.py
│   ├── base.py                    # Base model with common fields
│   ├── company.py                 # Company model
│   ├── contact.py                 # Contact model
│   ├── order.py                   # Order and OrderItem models
│   ├── payment.py                 # PaymentRecord model
│   ├── production.py              # ProductionOrder model
│   ├── contract.py                # Contract model
│   ├── product.py                 # Product model
│   └── outbound.py                # Outbound order model
│
├── permissions/                    # Permission classes
│   ├── __init__.py
│   ├── company.py
│   ├── contact.py
│   ├── order.py
│   └── ...
│
├── policy/                         # Access control policies
│   ├── __init__.py
│   └── ...
│
├── serializers/                    # DRF serializers
│   ├── __init__.py
│   ├── base.py                    # Base serializer
│   ├── company.py
│   ├── contact.py
│   ├── payment.py
│   ├── field.py                   # Custom field serializers
│   ├── order/                     # Order-related serializers
│   │   ├── __init__.py
│   │   ├── order.py
│   │   └── order_item.py
│   ├── production/                # Production-related serializers
│   │   ├── __init__.py
│   │   ├── production_order.py
│   │   └── production_item.py
│   └── outbound/                  # Outbound-related serializers
│       ├── __init__.py
│       └── ...
│
├── services/                       # Business logic services
│   ├── __init__.py
│   ├── pipeline_service.py        # Pipeline business logic
│   └── pipeline_state_service.py  # Pipeline state management
│
├── tests/                          # Test suite
│   ├── __init__.py
│   └── test_file_upload.py       # File upload tests
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   └── file_upload.py            # File upload path generators
│
└── views/                          # API views
    ├── __init__.py
    ├── company_view.py
    ├── contact_view.py
    ├── order_view.py
    ├── payment_view.py            # Uses ReturnRelatedMixin
    ├── production_view.py
    └── ...
```

## 🔑 Key Features

### Models
- **Company**: Customer company management
- **Contact**: Contact person management
- **Order**: Sales orders with items
- **Payment**: Payment records with file attachments
- **Production**: Production orders and items
- **Contract**: Contract management
- **Product**: Product catalog
- **Outbound**: Shipping and logistics

### Mixins
- **ReturnRelatedMixin**: Returns related object data after create/update operations
  - Used in `payment_view.py` to return updated order data after payment operations
  - Reduces API calls by returning parent resource data
- **MultipartNestedDataMixin**: Handles multipart form data with nested objects

### Utilities
- **File Upload**: Unique path generation for file uploads
  - Prevents name conflicts with UUID prefixes
  - Organizes files by date (YYYY/MM/DD)
  - See [docs/FILE_UPLOAD_GUIDE.md](./docs/FILE_UPLOAD_GUIDE.md)

### Services
- **PipelineService**: Handles pipeline business logic
- **PipelineStateService**: Manages pipeline state transitions and permissions

## 🚀 Quick Start

### Running Tests

```bash
# Run all tests
python manage.py test sea_saw_crm

# Run specific test module
python manage.py test sea_saw_crm.tests.test_file_upload

# Run with verbose output
python manage.py test sea_saw_crm -v 2
```

### Creating Migrations

```bash
# Create migrations
python manage.py makemigrations sea_saw_crm

# Apply migrations
python manage.py migrate sea_saw_crm
```

### Admin Interface

```bash
# Create superuser
python manage.py createsuperuser

# Access admin at http://localhost:8000/admin
```

## 📚 Documentation

- [File Upload Guide](./docs/FILE_UPLOAD_GUIDE.md) - File upload configuration and best practices

## 🔧 Development Notes

### Adding New Models

1. Create model in `models/` directory
2. Create serializer in `serializers/`
3. Create viewset in `views/`
4. Add permissions in `permissions/`
5. Register in admin (optional) in `admin/`
6. Create migrations: `python manage.py makemigrations`
7. Write tests in `tests/`

### Adding File Upload Fields

See [docs/FILE_UPLOAD_GUIDE.md](./docs/FILE_UPLOAD_GUIDE.md) for detailed instructions.

## 🧪 Testing

Tests are organized in the `tests/` directory:

- `test_file_upload.py` - File upload path generation tests

Run tests before committing changes:

```bash
python manage.py test sea_saw_crm
```

## 📝 Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document complex logic with docstrings
- Keep functions focused and single-purpose

## 🔐 Security Notes

- Never commit sensitive data (API keys, passwords)
- Use environment variables for configuration
- Validate all user input
- Use Django's built-in security features
- Check file uploads for malicious content

## 📞 Contact

For questions or issues, please refer to the main project documentation.
