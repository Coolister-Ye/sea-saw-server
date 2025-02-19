from django_filters import rest_framework as filters

from .models import Contract, Contact, Company, Order


class ContactFilter(filters.FilterSet):
    # Filters for first_name
    first_name = filters.CharFilter(field_name='first_name', lookup_expr='exact')
    first_name__icontains = filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    first_name__startswith = filters.CharFilter(field_name='first_name', lookup_expr='startswith')

    # Filters for last_name
    last_name = filters.CharFilter(field_name='last_name', lookup_expr='exact')
    last_name__icontains = filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    last_name__startswith = filters.CharFilter(field_name='last_name', lookup_expr='startswith')

    # Filters for full_name
    full_name = filters.CharFilter(field_name='full_name', lookup_expr='exact')
    full_name__icontains = filters.CharFilter(field_name='full_name', lookup_expr='icontains')
    full_name__startswith = filters.CharFilter(field_name='full_name', lookup_expr='startswith')

    # Filters for title
    title = filters.CharFilter(field_name='title', lookup_expr='exact')
    title__icontains = filters.CharFilter(field_name='title', lookup_expr='icontains')
    title__startswith = filters.CharFilter(field_name='title', lookup_expr='startswith')

    # Filters for email
    email = filters.CharFilter(field_name='email', lookup_expr='exact')
    email__icontains = filters.CharFilter(field_name='email', lookup_expr='icontains')
    email__startswith = filters.CharFilter(field_name='email', lookup_expr='startswith')

    # Filters for mobile
    mobile = filters.CharFilter(field_name='mobile', lookup_expr='exact')
    mobile__icontains = filters.CharFilter(field_name='mobile', lookup_expr='icontains')
    mobile__startswith = filters.CharFilter(field_name='mobile', lookup_expr='startswith')

    # Filters for phone
    phone = filters.CharFilter(field_name='phone', lookup_expr='exact')
    phone__icontains = filters.CharFilter(field_name='phone', lookup_expr='icontains')
    phone__startswith = filters.CharFilter(field_name='phone', lookup_expr='startswith')

    class Meta:
        model = Contact
        fields = []  # No need to specify fields here as we define all filters above


class CompanyFilter(filters.FilterSet):
    # Filters for company_name
    company_name = filters.CharFilter(field_name='company_name', lookup_expr='exact')
    company_name__icontains = filters.CharFilter(field_name='company_name', lookup_expr='icontains')
    company_name__startswith = filters.CharFilter(field_name='company_name', lookup_expr='startswith')

    # Filters for email
    email = filters.CharFilter(field_name='email', lookup_expr='exact')
    email__icontains = filters.CharFilter(field_name='email', lookup_expr='icontains')
    email__startswith = filters.CharFilter(field_name='email', lookup_expr='startswith')

    # Filters for mobile
    mobile = filters.CharFilter(field_name='mobile', lookup_expr='exact')
    mobile__icontains = filters.CharFilter(field_name='mobile', lookup_expr='icontains')
    mobile__startswith = filters.CharFilter(field_name='mobile', lookup_expr='startswith')

    # Filters for phone
    phone = filters.CharFilter(field_name='phone', lookup_expr='exact')
    phone__icontains = filters.CharFilter(field_name='phone', lookup_expr='icontains')
    phone__startswith = filters.CharFilter(field_name='phone', lookup_expr='startswith')

    # Filters for home_phone
    home_phone = filters.CharFilter(field_name='home_phone', lookup_expr='exact')
    home_phone__icontains = filters.CharFilter(field_name='home_phone', lookup_expr='icontains')
    home_phone__startswith = filters.CharFilter(field_name='home_phone', lookup_expr='startswith')

    class Meta:
        model = Company
        fields = []  # No need to specify fields here as we define all filters above


class ContractFilter(filters.FilterSet):
    # Filters for contract_code
    contract_code = filters.CharFilter(field_name='contract_code', lookup_expr='exact')
    contract_code__icontains = filters.CharFilter(field_name='contract_code', lookup_expr='icontains')
    contract_code__startswith = filters.CharFilter(field_name='contract_code', lookup_expr='startswith')

    # Filters for stage
    stage = filters.CharFilter(field_name='stage', lookup_expr='exact')

    # Filters for contract_date
    contract_date = filters.DateFilter(field_name='contract_date', lookup_expr='exact')
    contract_date__gte = filters.DateFilter(field_name='contract_date', lookup_expr='gte')
    contract_date__lte = filters.DateFilter(field_name='contract_date', lookup_expr='lte')

    # Filters for orders
    orders__order_code = filters.CharFilter(field_name='orders__order_code', lookup_expr='exact', distinct=True)
    orders__order_code__icontains = filters.CharFilter(
        field_name='orders__order_code', lookup_expr='icontains', distinct=True
    )
    orders__order_code__startswith = filters.CharFilter(
        field_name='orders__order_code', lookup_expr='startswith', distinct=True
    )

    orders__destination_port = filters.CharFilter(
        field_name='orders__destination_port', lookup_expr='exact', distinct=True
    )
    orders__destination_port__icontains = filters.CharFilter(
        field_name='orders__destination_port', lookup_expr='icontains', distinct=True
    )
    orders__destination_port__startswith = filters.CharFilter(
        field_name='orders__destination_port', lookup_expr='startswith', distinct=True
    )

    orders__etd = filters.DateFilter(field_name='orders__etd', lookup_expr='exact', distinct=True)
    orders__etd__gte = filters.DateFilter(field_name='orders__etd', lookup_expr='gte', distinct=True)
    orders__etd__lte = filters.DateFilter(field_name='orders__etd', lookup_expr='lte', distinct=True)

    orders__stage = filters.CharFilter(field_name='orders__stage', lookup_expr='exact', distinct=True)

    orders__deliver_date = filters.DateFilter(field_name='orders__deliver_date', lookup_expr='exact', distinct=True)
    orders__deliver_date__gte = filters.DateFilter(field_name='orders__deliver_date', lookup_expr='gte', distinct=True)
    orders__deliver_date__lte = filters.DateFilter(field_name='orders__deliver_date', lookup_expr='lte', distinct=True)

    orders__deposit = filters.NumberFilter(field_name='orders__deposit', lookup_expr='exact', distinct=True)
    orders__deposit__gte = filters.NumberFilter(field_name='orders__deposit', lookup_expr='gte', distinct=True)
    orders__deposit__lte = filters.NumberFilter(field_name='orders__deposit', lookup_expr='lte', distinct=True)

    orders__deposit_date = filters.DateFilter(field_name='orders__deposit_date', lookup_expr='exact', distinct=True)
    orders__deposit_date__gte = filters.DateFilter(field_name='orders__deposit_date', lookup_expr='gte', distinct=True)
    orders__deposit_date__lte = filters.DateFilter(field_name='orders__deposit_date', lookup_expr='lte', distinct=True)
    orders__deposit__isnull = filters.BooleanFilter(field_name='orders__deposit', lookup_expr='isnull', distinct=True)

    orders__balance = filters.NumberFilter(field_name='orders__balance', lookup_expr='exact', distinct=True)
    orders__balance__gte = filters.NumberFilter(field_name='orders__balance', lookup_expr='gte', distinct=True)
    orders__balance__lte = filters.NumberFilter(field_name='orders__balance', lookup_expr='lte', distinct=True)

    orders__balance_date = filters.DateFilter(field_name='orders__balance_date', lookup_expr='exact', distinct=True)
    orders__balance_date__gte = filters.DateFilter(field_name='orders__balance_date', lookup_expr='gte', distinct=True)
    orders__balance_date__lte = filters.DateFilter(field_name='orders__balance_date', lookup_expr='lte', distinct=True)
    orders__balance__isnull = filters.BooleanFilter(field_name='orders__balance', lookup_expr='isnull', distinct=True)

    # Filters for OrderProduct fields
    orders__products__product_name = filters.CharFilter(
        field_name='orders__products__product_name', lookup_expr='exact', distinct=True
    )
    orders__products__product_name__icontains = filters.CharFilter(
        field_name='orders__products__product_name', lookup_expr='icontains', distinct=True
    )

    orders__products__packaging = filters.CharFilter(
        field_name='orders__products__packaging', lookup_expr='exact', distinct=True
    )
    orders__products__packaging__icontains = filters.CharFilter(
        field_name='orders__products__packaging', lookup_expr='icontains', distinct=True
    )

    orders__products__size = filters.CharFilter(field_name='orders__products__size', lookup_expr='exact', distinct=True)
    orders__products__size__icontains = filters.CharFilter(
        field_name='orders__products__size', lookup_expr='icontains', distinct=True
    )

    orders__products__glazing = filters.NumberFilter(
        field_name='orders__products__glazing', lookup_expr='exact', distinct=True
    )
    orders__products__glazing__gte = filters.NumberFilter(
        field_name='orders__products__glazing', lookup_expr='gte', distinct=True
    )
    orders__products__glazing__lte = filters.NumberFilter(
        field_name='orders__products__glazing', lookup_expr='lte', distinct=True
    )

    orders__products__quantity = filters.NumberFilter(
        field_name='orders__products__quantity', lookup_expr='exact', distinct=True
    )
    orders__products__quantity__gte = filters.NumberFilter(
        field_name='orders__products__quantity', lookup_expr='gte', distinct=True
    )
    orders__products__quantity__lte = filters.NumberFilter(
        field_name='orders__products__quantity', lookup_expr='lte', distinct=True
    )

    orders__products__weight = filters.CharFilter(
        field_name='orders__products__weight', lookup_expr='exact', distinct=True
    )
    orders__products__weight__icontains = filters.CharFilter(
        field_name='orders__products__weight', lookup_expr='icontains', distinct=True
    )
    orders__products__weight__startswith = filters.CharFilter(
        field_name='orders__products__weight', lookup_expr='startswith', distinct=True
    )

    orders__products__net_weight = filters.NumberFilter(
        field_name='orders__products__net_weight', lookup_expr='exact', distinct=True
    )
    orders__products__net_weight__gte = filters.NumberFilter(
        field_name='orders__products__net_weight', lookup_expr='gte', distinct=True
    )
    orders__products__net_weight__lte = filters.NumberFilter(
        field_name='orders__products__net_weight', lookup_expr='lte', distinct=True
    )

    orders__products__total_net_weight = filters.NumberFilter(
        field_name='orders__products__total_net_weight', lookup_expr='exact', distinct=True
    )
    orders__products__total_net_weight__gte = filters.NumberFilter(
        field_name='orders__products__total_net_weight', lookup_expr='gte', distinct=True
    )
    orders__products__total_net_weight__lte = filters.NumberFilter(
        field_name='orders__products__total_net_weight', lookup_expr='lte', distinct=True
    )

    orders__products__price = filters.NumberFilter(
        field_name='orders__products__price', lookup_expr='exact', distinct=True
    )
    orders__products__price__gte = filters.NumberFilter(
        field_name='orders__products__price', lookup_expr='gte', distinct=True
    )
    orders__products__price__lte = filters.NumberFilter(
        field_name='orders__products__price', lookup_expr='lte', distinct=True
    )

    orders__products__total_price = filters.NumberFilter(
        field_name='orders__products__total_price', lookup_expr='exact', distinct=True
    )
    orders__products__total_price__gte = filters.NumberFilter(
        field_name='orders__products__total_price', lookup_expr='gte', distinct=True
    )
    orders__products__total_price__lte = filters.NumberFilter(
        field_name='orders__products__total_price', lookup_expr='lte', distinct=True
    )

    orders__products__progress_material = filters.CharFilter(
        field_name='orders__products__progress_material', lookup_expr='exact', distinct=True
    )
    orders__products__progress_quantity = filters.NumberFilter(
        field_name='orders__products__progress_quantity', lookup_expr='exact', distinct=True
    )
    orders__products__progress_quantity__gte = filters.NumberFilter(
        field_name='orders__products__progress_quantity', lookup_expr='gte', distinct=True
    )
    orders__products__progress_quantity__lte = filters.NumberFilter(
        field_name='orders__products__progress_quantity', lookup_expr='lte', distinct=True
    )

    orders__products__progress_weight = filters.NumberFilter(
        field_name='orders__products__progress_weight', lookup_expr='exact', distinct=True
    )
    orders__products__progress_weight__gte = filters.NumberFilter(
        field_name='orders__products__progress_weight', lookup_expr='gte', distinct=True
    )
    orders__products__progress_weight__lte = filters.NumberFilter(
        field_name='orders__products__progress_weight', lookup_expr='lte', distinct=True
    )

    # Filters for contact (if applicable)
    contact__full_name = filters.CharFilter(field_name='contact__full_name', lookup_expr='exact', distinct=True)
    contact__full_name__icontains = filters.CharFilter(
        field_name='contact__full_name', lookup_expr='icontains', distinct=True
    )

    class Meta:
        model = Contract
        fields = []


class OrderFilter(filters.FilterSet):
    """
    FIlter for orders
    """

    order_code = filters.CharFilter(field_name='order_code', lookup_expr='exact')
    order_code__icontains = filters.CharFilter(field_name='order_code', lookup_expr='icontains')
    order_code__startswith = filters.CharFilter(field_name='order_code', lookup_expr='startswith')

    destination_port = filters.CharFilter(field_name='destination_port', lookup_expr='exact')
    destination_port__icontains = filters.CharFilter(field_name='destination_port', lookup_expr='icontains')
    destination_port__startswith = filters.CharFilter(field_name='destination_port', lookup_expr='startswith')

    etd = filters.DateFilter(field_name='etd', lookup_expr='exact', distinct=True)
    etd__gte = filters.DateFilter(field_name='etd', lookup_expr='gte', distinct=True)
    etd__lte = filters.DateFilter(field_name='etd', lookup_expr='lte', distinct=True)

    stage = filters.CharFilter(field_name='stage', lookup_expr='exact', distinct=True)

    deliver_date = filters.DateFilter(field_name='deliver_date', lookup_expr='exact', distinct=True)
    deliver_date__gte = filters.DateFilter(field_name='deliver_date', lookup_expr='gte', distinct=True)
    deliver_date__lte = filters.DateFilter(field_name='deliver_date', lookup_expr='lte', distinct=True)

    deposit = filters.NumberFilter(field_name='deposit', lookup_expr='exact', distinct=True)
    deposit__gte = filters.NumberFilter(field_name='deposit', lookup_expr='gte', distinct=True)
    deposit__lte = filters.NumberFilter(field_name='deposit', lookup_expr='lte', distinct=True)

    deposit_date = filters.DateFilter(field_name='deposit_date', lookup_expr='exact', distinct=True)
    deposit_date__gte = filters.DateFilter(field_name='deposit_date', lookup_expr='gte', distinct=True)
    deposit_date__lte = filters.DateFilter(field_name='deposit_date', lookup_expr='lte', distinct=True)
    deposit__isnull = filters.BooleanFilter(field_name='deposit', lookup_expr='isnull', distinct=True)

    balance = filters.NumberFilter(field_name='balance', lookup_expr='exact', distinct=True)
    balance__gte = filters.NumberFilter(field_name='balance', lookup_expr='gte', distinct=True)
    balance__lte = filters.NumberFilter(field_name='balance', lookup_expr='lte', distinct=True)

    balance_date = filters.DateFilter(field_name='balance_date', lookup_expr='exact', distinct=True)
    balance_date__gte = filters.DateFilter(field_name='balance_date', lookup_expr='gte', distinct=True)
    balance_date__lte = filters.DateFilter(field_name='balance_date', lookup_expr='lte', distinct=True)
    balance__isnull = filters.BooleanFilter(field_name='balance', lookup_expr='isnull', distinct=True)

    # Fiter for product
    products__product_name = filters.CharFilter(field_name='products__product_name', lookup_expr='exact', distinct=True)
    products__product_name__icontains = filters.CharFilter(
        field_name='products__product_name', lookup_expr='icontains', distinct=True
    )

    products__packaging = filters.CharFilter(field_name='products__packaging', lookup_expr='exact', distinct=True)
    products__packaging__icontains = filters.CharFilter(
        field_name='products__packaging', lookup_expr='icontains', distinct=True
    )

    products__size = filters.CharFilter(field_name='products__size', lookup_expr='exact', distinct=True)
    products__size__icontains = filters.CharFilter(field_name='products__size', lookup_expr='icontains', distinct=True)

    products__glazing = filters.NumberFilter(field_name='products__glazing', lookup_expr='exact', distinct=True)
    products__glazing__gte = filters.NumberFilter(field_name='products__glazing', lookup_expr='gte', distinct=True)
    products__glazing__lte = filters.NumberFilter(field_name='products__glazing', lookup_expr='lte', distinct=True)

    products__quantity = filters.NumberFilter(field_name='products__quantity', lookup_expr='exact', distinct=True)
    products__quantity__gte = filters.NumberFilter(field_name='products__quantity', lookup_expr='gte', distinct=True)
    products__quantity__lte = filters.NumberFilter(field_name='products__quantity', lookup_expr='lte', distinct=True)

    products__weight = filters.CharFilter(field_name='products__weight', lookup_expr='exact', distinct=True)
    products__weight__icontains = filters.CharFilter(
        field_name='products__weight', lookup_expr='icontains', distinct=True
    )
    products__weight__startswith = filters.CharFilter(
        field_name='products__weight', lookup_expr='startswith', distinct=True
    )

    products__net_weight = filters.NumberFilter(field_name='products__net_weight', lookup_expr='exact', distinct=True)
    products__net_weight__gte = filters.NumberFilter(
        field_name='products__net_weight', lookup_expr='gte', distinct=True
    )
    products__net_weight__lte = filters.NumberFilter(
        field_name='products__net_weight', lookup_expr='lte', distinct=True
    )

    products__total_net_weight = filters.NumberFilter(
        field_name='products__total_net_weight', lookup_expr='exact', distinct=True
    )
    products__total_net_weight__gte = filters.NumberFilter(
        field_name='products__total_net_weight', lookup_expr='gte', distinct=True
    )
    products__total_net_weight__lte = filters.NumberFilter(
        field_name='products__total_net_weight', lookup_expr='lte', distinct=True
    )

    products__price = filters.NumberFilter(field_name='products__price', lookup_expr='exact', distinct=True)
    products__price__gte = filters.NumberFilter(field_name='products__price', lookup_expr='gte', distinct=True)
    products__price__lte = filters.NumberFilter(field_name='products__price', lookup_expr='lte', distinct=True)

    products__total_price = filters.NumberFilter(field_name='products__total_price', lookup_expr='exact', distinct=True)
    products__total_price__gte = filters.NumberFilter(
        field_name='products__total_price', lookup_expr='gte', distinct=True
    )
    products__total_price__lte = filters.NumberFilter(
        field_name='products__total_price', lookup_expr='lte', distinct=True
    )

    products__progress_material = filters.CharFilter(
        field_name='products__progress_material', lookup_expr='exact', distinct=True
    )
    products__progress_quantity = filters.NumberFilter(
        field_name='products__progress_quantity', lookup_expr='exact', distinct=True
    )
    products__progress_quantity__gte = filters.NumberFilter(
        field_name='products__progress_quantity', lookup_expr='gte', distinct=True
    )
    products__progress_quantity__lte = filters.NumberFilter(
        field_name='products__progress_quantity', lookup_expr='lte', distinct=True
    )

    products__progress_weight = filters.NumberFilter(
        field_name='products__progress_weight', lookup_expr='exact', distinct=True
    )
    products__progress_weight__gte = filters.NumberFilter(
        field_name='products__progress_weight', lookup_expr='gte', distinct=True
    )
    products__progress_weight__lte = filters.NumberFilter(
        field_name='products__progress_weight', lookup_expr='lte', distinct=True
    )

    class Meta:
        model = Order
        fields = []
