from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import JSONField
from django.utils.translation import gettext_lazy as _
from safedelete.models import SOFT_DELETE_CASCADE, SOFT_DELETE
from safedelete.models import SafeDeleteModel


class BaseModel(SafeDeleteModel):
    """
    Abstract base model with common audit fields.
    """

    # Allow soft delete
    _safedelete_policy = SOFT_DELETE_CASCADE

    owner = models.ForeignKey(
        "sea_saw_auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s",
        verbose_name=_("Owner"),
        help_text=_("The user who owns this object."),
    )
    created_by = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Created By"),
        help_text=_("The user who created this object."),
    )
    updated_by = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Updated By"),
        help_text=_("The user who last updated this object."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Timestamp when this object was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Timestamp when this object was last updated."),
    )

    class Meta:
        abstract = True
        verbose_name = _("Base Model")
        verbose_name_plural = _("Base Models")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"


class FieldType(models.TextChoices):
    PICKLIST = "picklist", _("Picklist")  # 下拉选择类型
    TEXT = "text", _("Text")  # 文本类型
    NUMERICAL = "numerical", _("Numerical")  # 数值类型
    LOOKUP = "lookup", _("Lookup")  # 查找类型
    DATE = "date", _("Date")  # 日期类型
    CURRENCY = "currency", _("Currency")  # 货币类型
    EMAIL = "email", _("Email")  # 邮件类型
    PHONE = "phone", _("Phone")  # 电话类型
    URL = "url", _("URL")  # URL 类型


class Field(BaseModel):
    """
    Metadata representation of an object/table field.
    Represents attributes of each field, associated with a model instance in the ContentType framework.
    """

    field_name = models.CharField(
        max_length=50,
        verbose_name=_("Field Name"),
        help_text=_("Name of the field (must be unique within the same content type)."),
    )
    field_type = models.CharField(
        max_length=50,
        choices=FieldType.choices,
        default=FieldType.TEXT,
        verbose_name=_("Field Type"),
        help_text=_("Type of the field (e.g., text, picklist)."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Indicates whether the field is active."),
    )
    is_mandatory = models.BooleanField(
        default=False,
        verbose_name=_("Is Mandatory"),
        help_text=_("Indicates whether the field is mandatory."),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        help_text=_("The model associated with this field."),
    )
    extra_info = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Extra Information"),
        help_text=_("Additional metadata or configuration for the field."),
    )

    class Meta:
        unique_together = ("content_type", "field_name")
        ordering = ["id"]
        verbose_name = _("Field")
        verbose_name_plural = _("Fields")
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "field_name"],
                name="unique_field_per_content_type",
            )
        ]

    def __str__(self):
        return self.field_name

    def clean(self):
        """
        Add custom validation logic for the model.
        """
        super().clean()
        if self.field_type == FieldType.PICKLIST and not self.extra_info:
            raise ValidationError(
                {
                    "extra_info": _(
                        "Picklist fields must have extra information (e.g., picklist choices)."
                    )
                }
            )


# 公司模型类 (Company Model Class)
class Company(BaseModel):
    """
    Represents a company entity with basic details and optional custom fields.
    表示公司实体，包含基本信息以及可选的自定义字段。
    """

    # _safedelete_policy = SOFT_DELETE

    company_name = models.CharField(
        max_length=255,
        verbose_name=_("Company Name"),
        help_text=_("The name of the company."),  # 公司名称 (Company Name)
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Email Address"),
        help_text=_(
            "The company's contact email address."
        ),  # 公司联系邮箱 (Company's Contact Email)
    )
    mobile = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Mobile Number"),
        help_text=_(
            "The company's mobile phone number."
        ),  # 公司手机号码 (Company Mobile Number)
    )
    phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_(
            "The company's landline phone number."
        ),  # 公司座机号码 (Company Landline Number)
    )
    home_phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Home Phone"),
        help_text=_(
            "The company's home phone number, if applicable."
        ),  # 公司家庭电话 (Company Home Phone)
    )

    class Meta:
        ordering = ["company_name"]  # 按公司名称排序 (Order by Company Name)
        verbose_name = _("Company")  # 公司 (Company)
        verbose_name_plural = _("Companies")  # 公司列表 (Companies List)

    def __str__(self):
        return self.company_name or _(
            "Unnamed Company"
        )  # 返回公司名称 (Return Company Name)


# 联系人模型类 (Contact Model Class)
class Contact(BaseModel):
    """
    Represents a contact entity with personal and communication details.
    Custom fields allow additional flexibility for extending contact attributes.
    表示联系人实体，包含个人信息和联系方式，自定义字段可扩展联系人属性。
    """

    first_name = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("First Name")
    )
    last_name = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Last Name")
    )
    full_name = models.CharField(
        max_length=510, null=True, blank=True, verbose_name=_("Customer Name")
    )
    title = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Job Title")
    )
    email = models.EmailField(null=True, blank=True, verbose_name=_("Email"))
    mobile = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Landline")
    )
    phone = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Phone Number")
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Company"),
    )
    custom_fields = models.JSONField(
        null=True, blank=True, verbose_name=_("Custom Fields")
    )

    class Meta:
        ordering = ["-created_at"]  # 按姓氏排序 (Order by Last Name)
        unique_together = ("email", "deleted")  # 确保邮箱唯一 (Ensure Unique Email)
        verbose_name = _("Contact")  # 联系人 (Contact)
        verbose_name_plural = _("Contacts")  # 联系人列表 (Contact List)

    def __str__(self):
        """
        String representation of a contact, combining first and last name.
        联系人的字符串表示，组合名和姓。
        """
        return (
            f"{self.first_name or ''} {self.last_name or ''}".strip()
        )  # 返回完整姓名 (Return Full Name)

    def clean(self):
        """
        Add custom validation logic for the Contact model.
        为联系人模型添加自定义验证逻辑。
        """
        super().clean()
        # 至少需要提供一个联系方式：邮箱或电话 (At least one contact method is required: email or phone)
        if not self.email and not self.phone:
            raise ValidationError(
                _("At least one contact method is required: email or phone.")
                # 邮箱或电话至少提供一个 (Email or Phone is required)
            )


# 合同阶段枚举类 (Contract Stage Enum Class)
class ContractStageType(models.TextChoices):
    IN_PROGRESS = "进行中", _("In Progress")  # 进行中 (In Progress)
    FINISHED = "已完成", _("Finished")  # 已完成 (Finished)
    CANCELLED = "已取消", _("Cancelled")  # 已取消 (Cancelled)
    DELAYED = "延迟中", _("Delayed")  # 延迟 (Delayed)
    ISSUE_REPORTED = "问题单", _("Issue Reported")  # 已报告问题 (Issue Reported)


# 合同模型类 (Contract Model Class)
class Contract(BaseModel):
    contract_code = models.CharField(
        max_length=100, null=False, blank=True, verbose_name=_("Contract Code")
    )  # 合同编号 (Contract Code)

    stage = models.CharField(
        max_length=25,
        choices=ContractStageType.choices,
        null=True,
        blank=True,
        verbose_name=_("Contract Stage"),
    )  # 合同阶段 (Contract Stage)

    contract_date = models.DateField(
        null=True, blank=True, verbose_name=_("Contract Date")
    )  # 合同日期 (Contract Date)

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Contact"),
    )  # 关联联系人 (Associated Contact)

    def __str__(self):
        return self.contract_code  # 返回合同编号 (Return Contract Code)

    class Meta:
        verbose_name = _("Contract")  # 合同 (Contract)
        verbose_name_plural = _("Contracts")  # 合同列表 (Contracts List)
        ordering = [
            "-created_at"
        ]  # 按创建时间倒序排列 (Order by Creation Time Descending)


# 定义订单状态的枚举类 (Define Order Stage Enum Class)
class OrderStageType(models.TextChoices):
    IN_PRODUCTION = "生产中", _("In Production")  # 生产中 (In Production)
    FINISHED_PRODUCTION = "已完成生产", _(
        "Finished Production"
    )  # 已完成生产 (Finished Production)
    IN_SHIPPMENT = "运输中", _("In Shipment")  # 运输中 (In Shipment)
    IN_PAYMENT = "支付中", _("In Payment")  # 支付中 (In Payment)
    FINISHED = "完成", _("Finished")  # 完成 (Finished)
    CANCELLED = "已取消", _("Cancelled")  # 已取消 (Cancelled)
    DELAYED = "延迟中", _("Delayed")  # 延迟 (Delayed)
    ISSUE_REPORTED = "问题单", _("Issue Reported")  # 已报告问题 (Issue Reported)


# 订单模型类 (Order Model Class)
class Order(BaseModel):
    order_code = models.CharField(
        max_length=100, null=False, blank=True, verbose_name=_("Order Code")
    )  # 订单编号 (Order Code)

    etd = models.DateField(
        null=True, blank=True, verbose_name=_("Estimated Delivery Date")
    )  # 预计交货日期 (Estimated Delivery Date)

    stage = models.CharField(
        max_length=25,
        choices=OrderStageType.choices,
        null=True,
        blank=True,
        verbose_name=_("Order Stage"),
    )  # 订单状态 (Order Stage)

    deliver_date = models.DateField(
        null=True, blank=True, verbose_name=_("Delivery Date")
    )  # 实际交货日期 (Actual Delivery Date)

    deposit = models.DecimalField(
        max_digits=30,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Deposit"),
    )  # 定金 (Deposit)

    deposit_date = models.DateField(
        null=True, blank=True, verbose_name=_("Deposit Date")
    )  # 定金支付日期 (Deposit Payment Date)

    balance = models.DecimalField(
        max_digits=30,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Balance"),
    )  # 余额 (Balance)

    balance_date = models.DateField(
        null=True, blank=True, verbose_name=_("Balance Date")
    )  # 余额支付日期 (Balance Payment Date)

    comment = models.TextField(
        null=True, blank=True, verbose_name=_("Comment")
    )  # 备注 (Comment)

    destination_port = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Destination Port")
    )  # 目的港 (Destination Port)

    shippment_term = models.CharField(
        max_length=10, null=True, blank=True, verbose_name=_("Shippment Term")
    )  # 交易方式 (Shippment Term)

    contract = models.ForeignKey(
        Contract,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Associated Contract"),
    )  # 关联合同 (Associated Contract)

    total_amount = models.DecimalField(
        max_digits=30,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Total Amount"),
    )  # 总金额 (Total Amount)

    def __str__(self):
        return f"Order {self.order_code} - {self.stage}"  # 返回订单编号和状态 (Return Order Code and Stage)

    class Meta:
        verbose_name = _("Order")  # 订单 (Order)
        verbose_name_plural = _("Orders")  # 订单列表 (Orders List)
        indexes = [
            models.Index(
                fields=["order_code"]
            ),  # 创建订单编号索引 (Index by Order Code)
            models.Index(fields=["stage"]),  # 创建订单状态索引 (Index by Order Stage)
        ]
        ordering = ["created_at"]


# 订单产品模型类 (Order Product Model Class)
class OrderProduct(BaseModel):
    product_name = models.CharField(
        max_length=100, null=False, blank=True, verbose_name=_("Product Name")
    )  # 产品名称 (Product Name)

    product_code = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Product Code")
    )  # 产品编号 (Product Code)

    product_type = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Product Type")
    )  # 产品类型 (Product Type)

    packaging = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Packaging Type")
    )  # 包装类型 (Packaging Type)

    interior_packaging = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Interior Packaging Type")
    )  # 内包装类型 (Interior Packaging Type)

    size = models.CharField(
        max_length=50, null=True, blank=True, verbose_name=_("Size")
    )  # 尺寸 (Size)

    unit = models.CharField(
        max_length=50, null=True, blank=True, verbose_name=_("Unit")
    )  # 单位 (Unit)

    glazing = models.FloatField(
        null=True, blank=True, verbose_name=_("Glazing Ratio")
    )  # 冰衣率 (Glazing Ratio)

    quantity = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Quantity")
    )  # 数量 (Quantity)

    weight = models.CharField(
        max_length=50, null=True, blank=True, verbose_name=_("Weight")
    )  # 重量 (Weight)

    net_weight = models.FloatField(
        null=True, blank=True, verbose_name=_("Net Weight")
    )  # 净重 (Net Weight)

    total_net_weight = models.FloatField(
        null=True, blank=True, verbose_name=_("Total Net Weight")
    )  # 总净重 (Total Net Weight)

    price = models.DecimalField(
        max_digits=15, decimal_places=5, null=True, blank=True, verbose_name=_("Price")
    )  # 单价 (Price)

    total_price = models.DecimalField(
        max_digits=30,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Total Price"),
    )  # 总价 (Total Price)

    progress_material = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Material Stage")
    )  # 生产材料进度 (Material Stage)

    progress_quantity = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Production Progress Quantity")
    )  # 生产进度数量 (Production Progress Quantity)

    progress_weight = models.FloatField(
        null=True, blank=True, verbose_name=_("Production Progress Weight")
    )  # 生产进度重量 (Production Progress Weight)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        blank=True,
        related_name="products",
        verbose_name=_("Associated Order"),
    )  # 关联订单 (Associated Order)

    custom_fields = JSONField(
        null=True, blank=True, verbose_name=_("Custom Fields")
    )  # 自定义字段 (Custom Fields)

    class Meta:
        verbose_name = _("Order Product")  # 订单产品 (Order Product)
        verbose_name_plural = _("Order Products")  # 订单产品列表 (Order Products List)
        indexes = [
            models.Index(fields=["product_name"])
        ]  # 创建产品名称索引 (Index by Product Name)
        ordering = ["created_at"]

    def __str__(self):
        return self.product_name  # 返回产品名称 (Return Product Name)
