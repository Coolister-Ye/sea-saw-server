Sea-Saw CRM 往来单位模型重构方案
一、背景分析
1.1 当前架构现状
现有模型：

Company (客户) - 被用作销售订单的客户、供应商所属公司、Pipeline 的客户
Contact (联系人) - 可关联 Company，与 Supplier 通过中间表多对多关联
Supplier (供应商) - 独立模型，可选关联 Company，通过 SupplierContact 关联多个 Contact
外键引用关系：


Order (销售订单)
├── company: FK(Company)
└── contact: FK(Contact)

PurchaseOrder (采购订单)
└── supplier: FK(Supplier)

Pipeline (业务流程)
├── order: OneToOneField(Order)
├── company: FK(Company) - 从 order.company 同步
└── contact: FK(Contact) - 从 order.contact 同步

ProductionOrder/OutboundOrder
└── pipeline: FK(Pipeline) - 通过 Pipeline 间接关联客户
关键问题：

Company 语义混乱 - 同时表示"客户"、"供应商所属公司"、"联系人所属公司"三种不同含义
无法表达双重角色 - 同一实体既是客户又是供应商时，需要创建 Company + Supplier 两条记录
数据重复 - Supplier 有独立的 phone/email，但又通过 contacts 关联 Contact
缺少往来单位类型 - 无承运商、代工厂、仓库等其他业务伙伴类型
权限代码重复 - CompanyPermission、ContactPermission、SupplierPermission 逻辑完全相同
1.2 业界最佳实践研究
Odoo ERP - res.partner 模型

# Odoo 使用统一的 Partner 模型
class Partner(models.Model):
    name = fields.Char()
    is_company = fields.Boolean()  # 公司 vs 个人
    parent_id = fields.Many2one('res.partner')  # 所属公司（支持层级）

    # 角色标记（可多选）
    customer_rank = fields.Integer()  # >0 表示是客户
    supplier_rank = fields.Integer()  # >0 表示是供应商

    # 联系方式
    email, phone, mobile = ...

    # 地址（支持多地址）
    child_ids = fields.One2many('res.partner', 'parent_id')  # 联系人和地址
核心设计理念：

统一的 Partner 概念（客户、供应商、联系人、地址都是 Partner）
通过 is_company 区分公司和个人
通过 parent_id 实现层级关系（公司 → 联系人、公司 → 分支机构）
通过 customer_rank/supplier_rank 支持多重角色
ERPNext - Customer/Supplier 独立但共享 Party

# ERPNext 使用中间层 Party 模型
class Party:  # 抽象概念，不直接存表
    party_type = Enum('Customer', 'Supplier', 'Employee')
    party_name = str

class Customer(Party):
    customer_type = Enum('Company', 'Individual')
    customer_group = str

class Supplier(Party):
    supplier_type = str

# 联系人和地址通过 Dynamic Link 关联任意 Party
class Contact:
    links = List[{
        'link_doctype': 'Customer' | 'Supplier',
        'link_name': 'CUST-001'
    }]
核心设计理念：

Customer 和 Supplier 保持独立（便于扩展字段）
通过 Dynamic Link (类似 Django GenericForeignKey) 共享联系人和地址
支持一个联系人关联多个 Customer/Supplier
SAP Business One - Business Partner

Business Partner
├── Card Type: Customer / Supplier / Lead
├── Card Code: BP001
├── Card Name: ABC Company
├── Contact Employees: []
└── Addresses: [
    {type: 'Bill To', address: '...'},
    {type: 'Ship To', address: '...'}
]
核心设计理念：

单一的 Business Partner 表
通过 Card Type 标记角色（可多选）
内嵌联系人和地址列表
Salesforce - Account & Contact

Account (组织/公司)
├── Type: Customer / Supplier / Partner
└── Contacts: []  # 一对多

Contact (个人)
├── Account: FK  # 所属组织
└── Reports To: FK(Contact)  # 汇报关系
核心设计理念：

Account 表示组织（公司、机构）
Contact 表示个人（必须属于某个 Account）
Account.Type 字段标记业务关系类型
二、方案对比与选择
2.1 方案 A：保持现状（Company + Supplier 分离）
架构：


Company (客户)
Contact (联系人) → Company
Supplier (供应商) ↔ Contact (M2M)
优点：

✅ 零迁移成本
✅ 业务逻辑不变
✅ 前端无需改动
缺点：

❌ 无法表达"既是客户又是供应商"
❌ Company 语义混乱
❌ 数据重复（Supplier 的 phone/email vs Contact）
❌ 权限代码重复
❌ 无法扩展新角色（承运商、代工厂等）
推荐度： ⭐⭐ - 仅适合短期维持现状

2.2 方案 B：完全重构为 Partner 模型（Odoo 风格）
架构：


class Partner(BaseModel):
    """统一的往来单位模型"""

    # 基础信息
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)  # AUTO: BP2024-000001
    partner_type = models.CharField(
        choices=[('company', 'Company'), ('individual', 'Individual')],
        default='company'
    )

    # 角色标记（多选）
    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)
    is_carrier = models.BooleanField(default=False)
    is_contractor = models.BooleanField(default=False)  # 代工厂

    # 层级关系（支持公司 → 联系人、公司 → 分支机构）
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    # 基础联系方式
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)

    # 地址信息
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # 业务信息
    tax_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    remark = models.TextField(blank=True)


class CustomerProfile(BaseModel):
    """客户扩展信息（一对一）"""
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name='customer_profile')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_terms = models.CharField(max_length=100, blank=True)
    customer_since = models.DateField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)


class SupplierProfile(BaseModel):
    """供应商扩展信息（一对一）"""
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name='supplier_profile')
    payment_terms = models.CharField(max_length=200, blank=True)
    currency = models.CharField(max_length=10, default='CNY')
    credit_limit = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    rating = models.IntegerField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)


class CarrierProfile(BaseModel):
    """承运商扩展信息（一对一）"""
    partner = models.OneToOneField(Partner, on_delete=models.CASCADE, related_name='carrier_profile')
    vehicle_types = models.CharField(max_length=200, blank=True)  # 车辆类型
    service_routes = models.TextField(blank=True)  # 服务路线
    insurance_no = models.CharField(max_length=100, blank=True)
迁移映射：


旧 Company → 新 Partner (is_customer=True, partner_type='company')
旧 Contact → 新 Partner (partner_type='individual', parent → 原 company)
旧 Supplier → 新 Partner (is_supplier=True) + SupplierProfile
外键迁移：


# Order 模型
- company: FK(Company) → customer: FK(Partner, limit_choices_to={'is_customer': True})
- contact: FK(Contact) → contact: FK(Partner, limit_choices_to={'partner_type': 'individual'})

# PurchaseOrder 模型
- supplier: FK(Supplier) → supplier: FK(Partner, limit_choices_to={'is_supplier': True})

# Pipeline 模型
- company: FK(Company) → customer: FK(Partner)
- contact: FK(Contact) → contact: FK(Partner)
优点：

✅ 统一模型，消除语义混乱
✅ 支持"既是客户又是供应商"（同一 Partner 记录）
✅ 易于扩展新角色（添加 is_xxx 字段）
✅ 层级关系支持（公司 → 联系人、公司 → 分支）
✅ 权限逻辑统一（一套 PartnerPermission）
✅ 查询简化（所有往来单位统一列表）
缺点：

❌ 迁移成本高（需要迁移 Company、Contact、Supplier 三张表）
❌ 外键引用多（Order、PurchaseOrder、Pipeline 等至少 8 个模块）
❌ 序列化器复杂（需要动态返回 CustomerProfile/SupplierProfile）
❌ 前端需要大幅改动
❌ 测试覆盖面广
❌ 业务中断风险高
推荐度： ⭐⭐⭐⭐⭐ - 长期最优方案，但需要充分准备

2.3 方案 C：渐进式重构（保留旧模型 + 添加新模型）
架构：


# 阶段 1：创建新模型但不迁移数据
class BusinessEntity(BaseModel):
    """新的统一往来单位模型"""
    # 与方案 B 的 Partner 相同
    ...

# 阶段 2：保留旧模型作为向后兼容层
class Company(BaseModel):
    """旧客户模型 - 标记为 Deprecated"""
    # 保持不变，添加迁移标记
    migrated_to = models.ForeignKey(BusinessEntity, null=True, on_delete=models.SET_NULL)

class Supplier(BaseModel):
    """旧供应商模型 - 标记为 Deprecated"""
    # 保持不变，添加迁移标记
    migrated_to = models.ForeignKey(BusinessEntity, null=True, on_delete=models.SET_NULL)

# 阶段 3：新业务使用 BusinessEntity，旧业务继续用 Company/Supplier
迁移步骤：

创建 BusinessEntity 模型和 Profile 表
写脚本将 Company/Supplier → BusinessEntity（不删除原数据）
新增 Order/PurchaseOrder 字段：business_entity: FK(BusinessEntity, null=True)
逐步迁移引用：先用 business_entity，再废弃 company/supplier
前端逐步适配新 API
最终删除旧模型（6-12 个月后）
优点：

✅ 风险可控（新旧并存）
✅ 可以分阶段迁移
✅ 业务不中断
✅ 有充足测试时间
✅ 可以回滚
缺点：

❌ 过渡期数据冗余
❌ 维护两套代码
❌ 迁移周期长
❌ 开发心智负担
推荐度： ⭐⭐⭐⭐ - 平衡风险和收益的实用方案

2.4 方案 D：优化现有架构（最小改动）
改进点：

统一权限逻辑


# 创建通用权限基类
class BaseEntityPermission(BasePermission):
    """通用往来单位权限基类"""
    entity_name = None  # 子类覆盖

    def has_permission(self, request, view):
        role_type = getattr(request.user.role, 'role_type', None)
        if role_type == 'ADMIN':
            return True
        if role_type == 'SALE':
            return view.action in {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'}
        return False

class CompanyPermission(BaseEntityPermission):
    entity_name = 'Company'

class SupplierPermission(BaseEntityPermission):
    entity_name = 'Supplier'
添加 Company.is_supplier 字段


class Company(BaseModel):
    is_supplier = models.BooleanField(default=False)
    # 如果 is_supplier=True，可以被 PurchaseOrder 引用
重构 Supplier.company 为必填


class Supplier(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)  # 必填
    # Supplier 成为 Company 的"供应商角色配置"
Contact 独立化


class Contact(BaseModel):
    company = models.ForeignKey(Company, null=True)  # 可选
    # 支持独立联系人（不属于任何公司）
优点：

✅ 改动最小
✅ 迁移成本低
✅ 可以逐步优化
缺点:

❌ 治标不治本
❌ 仍然无法完美支持"既是客户又是供应商"
❌ Company 语义仍然混乱
推荐度： ⭐⭐⭐ - 短期快速优化方案

三、推荐方案：方案 C（渐进式重构）
3.1 推荐理由
综合考虑 业务价值、技术风险、实施成本：

维度	方案 A	方案 B	方案 C	方案 D
长期架构优势	⭐	⭐⭐⭐⭐⭐	⭐⭐⭐⭐⭐	⭐⭐
迁移风险	⭐⭐⭐⭐⭐	⭐	⭐⭐⭐⭐	⭐⭐⭐⭐
开发成本	⭐⭐⭐⭐⭐	⭐	⭐⭐⭐	⭐⭐⭐⭐
业务中断风险	⭐⭐⭐⭐⭐	⭐	⭐⭐⭐⭐	⭐⭐⭐⭐⭐
可扩展性	⭐	⭐⭐⭐⭐⭐	⭐⭐⭐⭐⭐	⭐⭐
综合评分	2.2	3.4	4.2	3.4
方案 C 胜出原因：

达到与方案 B 相同的长期架构目标
风险可控，可以分阶段验证
业务不中断，新旧并存
有充足时间测试和优化
可以根据实际情况调整节奏
3.2 详细设计
3.2.1 核心模型设计

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/partner.py

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from sea_saw_base.models import BaseModel


class Partner(BaseModel):
    """
    统一的往来单位模型 - 支持客户、供应商、承运商等多重角色

    设计理念：
    - 一个实体可以同时是客户和供应商（is_customer + is_supplier）
    - 支持公司和个人（partner_type）
    - 支持层级关系（parent: 公司 → 联系人、公司 → 分支机构）
    - 扩展字段通过 Profile 模型（CustomerProfile、SupplierProfile）
    """

    PARTNER_TYPE_COMPANY = 'company'
    PARTNER_TYPE_INDIVIDUAL = 'individual'
    PARTNER_TYPE_CHOICES = [
        (PARTNER_TYPE_COMPANY, _('Company')),
        (PARTNER_TYPE_INDIVIDUAL, _('Individual')),
    ]

    # 基础信息
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Name of the partner (company or individual)"),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("Partner Code"),
        help_text=_("Unique identifier (auto-generated: BP2024-000001)"),
    )

    partner_type = models.CharField(
        max_length=20,
        choices=PARTNER_TYPE_CHOICES,
        default=PARTNER_TYPE_COMPANY,
        verbose_name=_("Partner Type"),
        help_text=_("Whether this is a company or individual"),
    )

    # 角色标记（多选）
    is_customer = models.BooleanField(
        default=False,
        verbose_name=_("Is Customer"),
        help_text=_("This partner can be used as a customer in sales orders"),
    )

    is_supplier = models.BooleanField(
        default=False,
        verbose_name=_("Is Supplier"),
        help_text=_("This partner can be used as a supplier in purchase orders"),
    )

    is_carrier = models.BooleanField(
        default=False,
        verbose_name=_("Is Carrier"),
        help_text=_("This partner can be used as a carrier for shipping"),
    )

    is_contractor = models.BooleanField(
        default=False,
        verbose_name=_("Is Contractor"),
        help_text=_("This partner can be used as a contractor for outsourcing"),
    )

    # 层级关系（支持公司 → 联系人、公司 → 分支机构）
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Parent Partner"),
        help_text=_("Parent partner (e.g., company for a contact person)"),
    )

    # 联系方式
    email = models.EmailField(
        max_length=200,
        blank=True,
        verbose_name=_("Email"),
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Phone"),
    )

    mobile = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Mobile"),
    )

    fax = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Fax"),
    )

    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
    )

    # 地址信息
    address = models.TextField(
        blank=True,
        verbose_name=_("Address"),
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("City"),
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("State/Province"),
    )

    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Country"),
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Postal Code"),
    )

    # 业务信息
    tax_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Tax ID"),
        help_text=_("Tax identification number"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this partner is currently active"),
    )

    remark = models.TextField(
        blank=True,
        verbose_name=_("Remark"),
    )

    # 迁移标记（用于追溯旧数据来源）
    migrated_from_model = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Migrated From Model"),
        help_text=_("Source model if migrated (Company/Contact/Supplier)"),
    )

    migrated_from_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Migrated From ID"),
        help_text=_("Source record ID if migrated"),
    )

    class Meta:
        verbose_name = _("Partner")
        verbose_name_plural = _("Partners")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_customer", "is_active"]),
            models.Index(fields=["is_supplier", "is_active"]),
            models.Index(fields=["partner_type"]),
        ]

    def __str__(self):
        return self.name or self.code or _("Unnamed Partner")

    def clean(self):
        """验证规则"""
        super().clean()

        # 至少选择一个角色
        if not any([self.is_customer, self.is_supplier, self.is_carrier, self.is_contractor]):
            raise ValidationError(_("At least one role must be selected (customer/supplier/carrier/contractor)"))

        # 个人类型不能有子记录
        if self.partner_type == self.PARTNER_TYPE_INDIVIDUAL and self.children.exists():
            raise ValidationError(_("Individual partners cannot have child partners"))

        # 子记录的 parent 必须是 company 类型
        if self.parent and self.parent.partner_type != self.PARTNER_TYPE_COMPANY:
            raise ValidationError(_("Parent partner must be a company"))

    def generate_code(self):
        """自动生成编号"""
        year = timezone.now().year
        count = Partner.objects.filter(created_at__year=year).count() + 1
        return f"BP{year}-{count:06d}"

    def save(self, *args, **kwargs):
        """自动生成 code"""
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def get_contacts(self):
        """获取所有联系人（子记录中的个人）"""
        return self.children.filter(partner_type=self.PARTNER_TYPE_INDIVIDUAL)

    def get_primary_contact(self):
        """获取主联系人（通过 PartnerRelation 标记）"""
        relation = self.partner_relations.filter(is_primary=True).first()
        return relation.related_partner if relation else None


class PartnerRelation(BaseModel):
    """
    Partner 之间的关系

    用于记录更复杂的关系，如：
    - Supplier A 的主联系人是 Contact B
    - Company X 的财务联系人是 Contact Y
    """

    RELATION_TYPE_CONTACT = 'contact'
    RELATION_TYPE_BILLING = 'billing'
    RELATION_TYPE_SHIPPING = 'shipping'
    RELATION_TYPE_TECHNICAL = 'technical'
    RELATION_TYPE_CHOICES = [
        (RELATION_TYPE_CONTACT, _('General Contact')),
        (RELATION_TYPE_BILLING, _('Billing Contact')),
        (RELATION_TYPE_SHIPPING, _('Shipping Contact')),
        (RELATION_TYPE_TECHNICAL, _('Technical Contact')),
    ]

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name='partner_relations',
        verbose_name=_("Partner"),
    )

    related_partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name='reverse_relations',
        verbose_name=_("Related Partner"),
    )

    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_TYPE_CHOICES,
        default=RELATION_TYPE_CONTACT,
        verbose_name=_("Relation Type"),
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Is Primary"),
        help_text=_("Primary contact for this partner"),
    )

    role = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Role"),
        help_text=_("Role of the related partner (e.g., Sales Manager)"),
    )

    remark = models.TextField(
        blank=True,
        verbose_name=_("Remark"),
    )

    class Meta:
        verbose_name = _("Partner Relation")
        verbose_name_plural = _("Partner Relations")
        unique_together = [("partner", "related_partner", "relation_type", "deleted")]
        ordering = ["-is_primary", "relation_type"]

    def __str__(self):
        return f"{self.partner.name} → {self.related_partner.name} ({self.get_relation_type_display()})"

    def save(self, *args, **kwargs):
        """确保每个 partner 只有一个主联系人"""
        if self.is_primary:
            PartnerRelation.objects.filter(
                partner=self.partner,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class CustomerProfile(BaseModel):
    """客户扩展信息"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        verbose_name=_("Partner"),
    )

    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Credit Limit"),
    )

    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Payment Terms"),
    )

    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Payment Method"),
    )

    customer_since = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Customer Since"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Customer rating (1-5 stars)"),
    )

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")

    def __str__(self):
        return f"Customer Profile: {self.partner.name}"


class SupplierProfile(BaseModel):
    """供应商扩展信息"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='supplier_profile',
        verbose_name=_("Partner"),
    )

    payment_terms = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Payment Terms"),
    )

    currency = models.CharField(
        max_length=10,
        default='CNY',
        verbose_name=_("Currency"),
    )

    credit_limit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Credit Limit"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Supplier rating (1-5 stars)"),
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Is Approved"),
        help_text=_("Whether this supplier has been approved"),
    )

    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Name"),
    )

    bank_account = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Account"),
    )

    class Meta:
        verbose_name = _("Supplier Profile")
        verbose_name_plural = _("Supplier Profiles")

    def __str__(self):
        return f"Supplier Profile: {self.partner.name}"


class CarrierProfile(BaseModel):
    """承运商扩展信息"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='carrier_profile',
        verbose_name=_("Partner"),
    )

    vehicle_types = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Vehicle Types"),
        help_text=_("Types of vehicles available (e.g., Truck, Van, Container)"),
    )

    service_routes = models.TextField(
        blank=True,
        verbose_name=_("Service Routes"),
        help_text=_("Geographic routes serviced"),
    )

    insurance_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Insurance Number"),
    )

    license_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("License Number"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Carrier rating (1-5 stars)"),
    )

    class Meta:
        verbose_name = _("Carrier Profile")
        verbose_name_plural = _("Carrier Profiles")

    def __str__(self):
        return f"Carrier Profile: {self.partner.name}"
3.2.2 向后兼容层（保留旧模型）

# 在旧模型中添加迁移标记字段

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/company.py
class Company(BaseModel):
    # ... 保持现有字段不变 ...

    # 新增：迁移标记
    migrated_to_partner = models.ForeignKey(
        'Partner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='migrated_companies',
        verbose_name=_("Migrated To Partner"),
        help_text=_("If migrated, points to the new Partner record"),
    )

    class Meta:
        # ... 保持不变 ...
        # 添加警告注释
        # WARNING: This model is deprecated. Use Partner model instead.
        # Will be removed in version 2.0


# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/supplier.py
class Supplier(BaseModel):
    # ... 保持现有字段不变 ...

    # 新增：迁移标记
    migrated_to_partner = models.ForeignKey(
        'Partner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='migrated_suppliers',
        verbose_name=_("Migrated To Partner"),
        help_text=_("If migrated, points to the new Partner record"),
    )


# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/contact.py
class Contact(BaseModel):
    # ... 保持现有字段不变 ...

    # 新增：迁移标记
    migrated_to_partner = models.ForeignKey(
        'Partner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='migrated_contacts',
        verbose_name=_("Migrated To Partner"),
        help_text=_("If migrated, points to the new Partner record"),
    )
3.2.3 业务模型扩展（新旧并存）

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_sales/models/order.py

class Order(AbstractOrderBase):
    # ... 保持现有字段 ...

    # 旧字段（保留）
    company = models.ForeignKey(
        "sea_saw_crm.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Company (Deprecated)"),
    )

    contact = models.ForeignKey(
        "sea_saw_crm.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Contact (Deprecated)"),
    )

    # 新字段（添加）
    customer = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_orders",
        limit_choices_to={'is_customer': True},
        verbose_name=_("Customer"),
        help_text=_("Customer partner for this order"),
    )

    contact_person = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_orders",
        limit_choices_to={'partner_type': 'individual'},
        verbose_name=_("Contact Person"),
        help_text=_("Contact person for this order"),
    )

    def save(self, *args, **kwargs):
        # 自动同步：如果 customer 存在但 company 为空，从 customer.migrated_companies 反向填充
        if self.customer and not self.company:
            migrated_company = self.customer.migrated_companies.first()
            if migrated_company:
                self.company = migrated_company

        # 反向同步：如果 company 存在且已迁移，自动填充 customer
        if self.company and self.company.migrated_to_partner and not self.customer:
            self.customer = self.company.migrated_to_partner

        super().save(*args, **kwargs)


# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_procurement/models/purchase_order.py

class PurchaseOrder(AbstractOrderBase):
    # ... 保持现有字段 ...

    # 旧字段（保留）
    supplier = models.ForeignKey(
        "sea_saw_crm.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_orders",
        verbose_name=_("Supplier (Deprecated)"),
    )

    # 新字段（添加）
    supplier_partner = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supplier_purchase_orders",
        limit_choices_to={'is_supplier': True},
        verbose_name=_("Supplier Partner"),
        help_text=_("Supplier partner for this purchase order"),
    )

    def save(self, *args, **kwargs):
        # 自动同步逻辑（同 Order）
        if self.supplier_partner and not self.supplier:
            migrated_supplier = self.supplier_partner.migrated_suppliers.first()
            if migrated_supplier:
                self.supplier = migrated_supplier

        if self.supplier and self.supplier.migrated_to_partner and not self.supplier_partner:
            self.supplier_partner = self.supplier.migrated_to_partner

        super().save(*args, **kwargs)
3.3 数据迁移脚本

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/migrations/XXXX_migrate_to_partner.py

from django.db import migrations
from django.utils import timezone


def migrate_companies_to_partners(apps, schema_editor):
    """将 Company 迁移到 Partner"""
    Company = apps.get_model('sea_saw_crm', 'Company')
    Partner = apps.get_model('sea_saw_crm', 'Partner')
    CustomerProfile = apps.get_model('sea_saw_crm', 'CustomerProfile')

    for company in Company.objects.filter(deleted__isnull=True):
        # 创建 Partner
        partner = Partner.objects.create(
            name=company.company_name,
            partner_type='company',
            is_customer=True,
            email=company.email or '',
            phone=company.phone or '',
            mobile=company.mobile or '',
            address=company.address or '',
            is_active=True,
            owner=company.owner,
            created_by=company.created_by,
            updated_by=company.updated_by,
            created_at=company.created_at,
            updated_at=company.updated_at,
            migrated_from_model='Company',
            migrated_from_id=company.id,
        )

        # 创建 CustomerProfile（如果需要）
        CustomerProfile.objects.create(
            partner=partner,
            customer_since=company.created_at.date() if company.created_at else timezone.now().date(),
            owner=company.owner,
        )

        # 反向标记
        company.migrated_to_partner = partner
        company.save(update_fields=['migrated_to_partner'])

        print(f"Migrated Company {company.id} → Partner {partner.id}")


def migrate_contacts_to_partners(apps, schema_editor):
    """将 Contact 迁移到 Partner"""
    Contact = apps.get_model('sea_saw_crm', 'Contact')
    Partner = apps.get_model('sea_saw_crm', 'Partner')

    for contact in Contact.objects.filter(deleted__isnull=True):
        # 确定父级 Partner（如果 contact.company 已迁移）
        parent_partner = None
        if contact.company and contact.company.migrated_to_partner:
            parent_partner = contact.company.migrated_to_partner

        # 创建 Partner
        partner = Partner.objects.create(
            name=contact.name or '',
            partner_type='individual',
            is_customer=False,  # 联系人默认不是客户
            parent=parent_partner,
            email=contact.email or '',
            phone=contact.phone or '',
            mobile=contact.mobile or '',
            is_active=True,
            owner=contact.owner,
            created_by=contact.created_by,
            updated_by=contact.updated_by,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
            migrated_from_model='Contact',
            migrated_from_id=contact.id,
        )

        # 反向标记
        contact.migrated_to_partner = partner
        contact.save(update_fields=['migrated_to_partner'])

        print(f"Migrated Contact {contact.id} → Partner {partner.id}")


def migrate_suppliers_to_partners(apps, schema_editor):
    """将 Supplier 迁移到 Partner"""
    Supplier = apps.get_model('sea_saw_crm', 'Supplier')
    Partner = apps.get_model('sea_saw_crm', 'Partner')
    SupplierProfile = apps.get_model('sea_saw_crm', 'SupplierProfile')
    SupplierContact = apps.get_model('sea_saw_crm', 'SupplierContact')
    PartnerRelation = apps.get_model('sea_saw_crm', 'PartnerRelation')

    for supplier in Supplier.objects.filter(deleted__isnull=True):
        # 检查是否已迁移（通过 supplier.company 的 migrated_to_partner）
        existing_partner = None
        if supplier.company and supplier.company.migrated_to_partner:
            # 同一个公司既是客户又是供应商
            existing_partner = supplier.company.migrated_to_partner
            existing_partner.is_supplier = True
            existing_partner.save(update_fields=['is_supplier'])
        else:
            # 创建新 Partner
            existing_partner = Partner.objects.create(
                name=supplier.name,
                partner_type='company',
                is_supplier=True,
                email=supplier.email or '',
                phone=supplier.phone or '',
                fax=supplier.fax or '',
                address=supplier.address or '',
                city=supplier.city or '',
                state=supplier.state or '',
                country=supplier.country or '',
                postal_code=supplier.postal_code or '',
                tax_id=supplier.tax_id or '',
                website=supplier.website or '',
                is_active=supplier.is_active,
                owner=supplier.owner,
                created_by=supplier.created_by,
                updated_by=supplier.updated_by,
                created_at=supplier.created_at,
                updated_at=supplier.updated_at,
                migrated_from_model='Supplier',
                migrated_from_id=supplier.id,
            )

        # 创建 SupplierProfile
        SupplierProfile.objects.create(
            partner=existing_partner,
            payment_terms=supplier.payment_terms or '',
            currency=supplier.currency,
            credit_limit=supplier.credit_limit,
            rating=supplier.rating,
            is_approved=supplier.is_approved,
            owner=supplier.owner,
        )

        # 迁移 SupplierContact → PartnerRelation
        for sc in SupplierContact.objects.filter(supplier=supplier, deleted__isnull=True):
            if sc.contact.migrated_to_partner:
                PartnerRelation.objects.create(
                    partner=existing_partner,
                    related_partner=sc.contact.migrated_to_partner,
                    relation_type='contact',
                    is_primary=sc.is_primary,
                    role=sc.role or '',
                    remark=sc.remark or '',
                    owner=sc.owner,
                )

        # 反向标记
        supplier.migrated_to_partner = existing_partner
        supplier.save(update_fields=['migrated_to_partner'])

        print(f"Migrated Supplier {supplier.id} → Partner {existing_partner.id}")


def migrate_order_references(apps, schema_editor):
    """迁移 Order 的 company/contact 引用到 customer/contact_person"""
    Order = apps.get_model('sea_saw_sales', 'Order')

    for order in Order.objects.filter(deleted__isnull=True):
        if order.company and order.company.migrated_to_partner:
            order.customer = order.company.migrated_to_partner

        if order.contact and order.contact.migrated_to_partner:
            order.contact_person = order.contact.migrated_to_partner

        if order.customer or order.contact_person:
            order.save(update_fields=['customer', 'contact_person'])
            print(f"Migrated Order {order.id} references")


def migrate_purchase_order_references(apps, schema_editor):
    """迁移 PurchaseOrder 的 supplier 引用到 supplier_partner"""
    PurchaseOrder = apps.get_model('sea_saw_procurement', 'PurchaseOrder')

    for po in PurchaseOrder.objects.filter(deleted__isnull=True):
        if po.supplier and po.supplier.migrated_to_partner:
            po.supplier_partner = po.supplier.migrated_to_partner
            po.save(update_fields=['supplier_partner'])
            print(f"Migrated PurchaseOrder {po.id} references")


class Migration(migrations.Migration):

    dependencies = [
        ('sea_saw_crm', 'XXXX_add_partner_models'),  # 前一个创建 Partner 表的迁移
    ]

    operations = [
        migrations.RunPython(migrate_companies_to_partners, migrations.RunPython.noop),
        migrations.RunPython(migrate_contacts_to_partners, migrations.RunPython.noop),
        migrations.RunPython(migrate_suppliers_to_partners, migrations.RunPython.noop),
        migrations.RunPython(migrate_order_references, migrations.RunPython.noop),
        migrations.RunPython(migrate_purchase_order_references, migrations.RunPython.noop),
    ]
3.4 序列化器设计

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/serializers/partner.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models import (
    Partner,
    PartnerRelation,
    CustomerProfile,
    SupplierProfile,
    CarrierProfile
)
from sea_saw_base.serializers import BaseSerializer


class CustomerProfileSerializer(BaseSerializer):
    """客户扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = CustomerProfile
        fields = [
            'id',
            'credit_limit',
            'payment_terms',
            'payment_method',
            'customer_since',
            'rating',
            'created_at',
            'updated_at',
        ]


class SupplierProfileSerializer(BaseSerializer):
    """供应商扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = SupplierProfile
        fields = [
            'id',
            'payment_terms',
            'currency',
            'credit_limit',
            'rating',
            'is_approved',
            'bank_name',
            'bank_account',
            'created_at',
            'updated_at',
        ]


class CarrierProfileSerializer(BaseSerializer):
    """承运商扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = CarrierProfile
        fields = [
            'id',
            'vehicle_types',
            'service_routes',
            'insurance_no',
            'license_no',
            'rating',
            'created_at',
            'updated_at',
        ]


class PartnerRelationSerializer(BaseSerializer):
    """Partner 关系序列化器"""

    related_partner = serializers.SerializerMethodField(read_only=True, label=_("Related Partner"))
    related_partner_id = serializers.PrimaryKeyRelatedField(
        queryset=Partner.objects.all(),
        source='related_partner',
        write_only=True,
        label=_("Related Partner ID"),
    )

    class Meta(BaseSerializer.Meta):
        model = PartnerRelation
        fields = [
            'id',
            'related_partner',
            'related_partner_id',
            'relation_type',
            'is_primary',
            'role',
            'remark',
            'created_at',
            'updated_at',
        ]

    def get_related_partner(self, obj):
        """返回简化的 partner 信息"""
        return {
            'id': obj.related_partner.id,
            'name': obj.related_partner.name,
            'email': obj.related_partner.email,
            'phone': obj.related_partner.phone,
            'mobile': obj.related_partner.mobile,
        }


class PartnerSerializer(BaseSerializer):
    """Partner 主序列化器 - 支持动态嵌套 Profile"""

    # 嵌套 Profile（只读）
    customer_profile = CustomerProfileSerializer(read_only=True, label=_("Customer Profile"))
    supplier_profile = SupplierProfileSerializer(read_only=True, label=_("Supplier Profile"))
    carrier_profile = CarrierProfileSerializer(read_only=True, label=_("Carrier Profile"))

    # 关系
    partner_relations = PartnerRelationSerializer(many=True, read_only=True, label=_("Partner Relations"))

    # 写入字段
    customer_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Customer Profile Data"),
    )

    supplier_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Supplier Profile Data"),
    )

    carrier_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Carrier Profile Data"),
    )

    relations_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        label=_("Relations Data"),
    )

    class Meta(BaseSerializer.Meta):
        model = Partner
        fields = [
            'id',
            'name',
            'code',
            'partner_type',
            'is_customer',
            'is_supplier',
            'is_carrier',
            'is_contractor',
            'parent',
            'email',
            'phone',
            'mobile',
            'fax',
            'website',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'tax_id',
            'is_active',
            'remark',
            'customer_profile',
            'supplier_profile',
            'carrier_profile',
            'partner_relations',
            'customer_profile_data',
            'supplier_profile_data',
            'carrier_profile_data',
            'relations_data',
            'owner',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['code']

    def create(self, validated_data):
        """创建 Partner 并处理嵌套 Profile"""
        customer_profile_data = validated_data.pop('customer_profile_data', None)
        supplier_profile_data = validated_data.pop('supplier_profile_data', None)
        carrier_profile_data = validated_data.pop('carrier_profile_data', None)
        relations_data = validated_data.pop('relations_data', [])

        partner = super().create(validated_data)

        # 创建 Profile
        if customer_profile_data and partner.is_customer:
            CustomerProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **customer_profile_data
            )

        if supplier_profile_data and partner.is_supplier:
            SupplierProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **supplier_profile_data
            )

        if carrier_profile_data and partner.is_carrier:
            CarrierProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **carrier_profile_data
            )

        # 创建关系
        for relation in relations_data:
            PartnerRelation.objects.create(
                partner=partner,
                owner=partner.owner,
                **relation
            )

        return partner

    def update(self, instance, validated_data):
        """更新 Partner 并处理嵌套 Profile"""
        customer_profile_data = validated_data.pop('customer_profile_data', None)
        supplier_profile_data = validated_data.pop('supplier_profile_data', None)
        carrier_profile_data = validated_data.pop('carrier_profile_data', None)
        relations_data = validated_data.pop('relations_data', None)

        partner = super().update(instance, validated_data)

        # 更新或创建 Profile
        if customer_profile_data is not None:
            CustomerProfile.objects.update_or_create(
                partner=partner,
                defaults={**customer_profile_data, 'owner': partner.owner}
            )

        if supplier_profile_data is not None:
            SupplierProfile.objects.update_or_create(
                partner=partner,
                defaults={**supplier_profile_data, 'owner': partner.owner}
            )

        if carrier_profile_data is not None:
            CarrierProfile.objects.update_or_create(
                partner=partner,
                defaults={**carrier_profile_data, 'owner': partner.owner}
            )

        # 更新关系（删除旧的，创建新的）
        if relations_data is not None:
            PartnerRelation.objects.filter(partner=partner).delete()
            for relation in relations_data:
                PartnerRelation.objects.create(
                    partner=partner,
                    owner=partner.owner,
                    **relation
                )

        return partner
3.5 权限控制统一化

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/permissions/partner_permission.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class PartnerAdminPermission(BasePermission):
    """Partner Admin 权限（与 Company/Supplier 相同逻辑）"""

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "ADMIN"

    def has_object_permission(self, request, view, obj):
        return True


class PartnerSalePermission(BasePermission):
    """Partner Sale 权限（与 Company/Supplier 相同逻辑）"""

    def has_permission(self, request, view):
        role_type = getattr(request.user.role, "role_type", None)
        if role_type != "SALE":
            return False

        return view.action in {
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        }

    def has_object_permission(self, request, view, obj):
        user = request.user
        owner = getattr(obj, "owner", None)

        if request.method in SAFE_METHODS:
            # 读取权限
            if owner == user:
                return True

            get_visible_users = getattr(owner, "get_all_visible_users", None)
            if callable(get_visible_users):
                return user in get_visible_users()

            return False
        else:
            # 修改/删除权限
            return owner == user
3.6 ViewSet 和路由

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/views/partner_view.py

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from ..models import Partner
from ..serializers import PartnerSerializer
from sea_saw_base.metadata import BaseMetadata
from ..permissions import PartnerAdminPermission, PartnerSalePermission


class PartnerViewSet(ModelViewSet):
    """Partner ViewSet - 统一的往来单位 API"""

    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [
        IsAuthenticated,
        PartnerAdminPermission | PartnerSalePermission,
    ]
    metadata_class = BaseMetadata

    search_fields = ["^name", "^code", "email", "phone"]
    filterset_fields = ["is_customer", "is_supplier", "is_carrier", "is_contractor", "partner_type", "is_active"]

    def get_queryset(self):
        """权限过滤"""
        user = self.request.user
        role_type = getattr(user.role, "role_type", None)

        base_queryset = self.queryset.filter(deleted__isnull=True)

        if role_type == "ADMIN":
            return base_queryset

        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return base_queryset.none()

        return base_queryset.filter(owner__in=get_users())

    @action(detail=False, methods=['get'], url_path='customers')
    def customers(self, request):
        """客户列表（is_customer=True）"""
        queryset = self.get_queryset().filter(is_customer=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='suppliers')
    def suppliers(self, request):
        """供应商列表（is_supplier=True）"""
        queryset = self.get_queryset().filter(is_supplier=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='carriers')
    def carriers(self, request):
        """承运商列表（is_carrier=True）"""
        queryset = self.get_queryset().filter(is_carrier=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='contacts')
    def contacts(self, request):
        """联系人列表（partner_type='individual'）"""
        queryset = self.get_queryset().filter(partner_type='individual')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# 路由配置
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/urls.py
router.register(r"partners", PartnerViewSet)

# API 端点：
# GET  /api/sea-saw-crm/partners/                    # 所有 Partner
# GET  /api/sea-saw-crm/partners/customers/          # 客户
# GET  /api/sea-saw-crm/partners/suppliers/          # 供应商
# GET  /api/sea-saw-crm/partners/carriers/           # 承运商
# GET  /api/sea-saw-crm/partners/contacts/           # 联系人
# POST /api/sea-saw-crm/partners/                    # 创建
# GET  /api/sea-saw-crm/partners/{id}/               # 详情
# PATCH /api/sea-saw-crm/partners/{id}/              # 更新
# DELETE /api/sea-saw-crm/partners/{id}/             # 删除
四、分阶段实施路线图
阶段 0：准备与规划（1-2 周）
任务：

 完整代码审查，确认所有外键引用点
 设计评审会议，团队对齐方案
 创建详细的测试计划
 准备测试环境和数据备份
 制定回滚方案
验收标准：

所有相关模块外键引用清单完成
团队一致同意实施方案
测试环境就绪
风险点：

遗漏外键引用点 → 缓解：使用自动化工具扫描
团队认知不一致 → 缓解：充分讨论和文档化
阶段 1：创建 Partner 模型（2-3 周）
任务：

 创建 Partner、PartnerRelation、CustomerProfile、SupplierProfile、CarrierProfile 模型
 编写模型单元测试（100% 覆盖率）
 创建 Django Migration
 在旧模型添加 migrated_to_partner 字段
 创建 PartnerSerializer、PartnerViewSet、PartnerPermission
 编写 API 单元测试
 在开发环境部署和测试
文件路径：

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/partner.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/serializers/partner.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/views/partner_view.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/permissions/partner_permission.py
验收标准：

所有模型测试通过
API 端点正常工作（CRUD + 自定义端点）
权限逻辑验证通过
代码审查通过
风险点：

模型验证逻辑不完善 → 缓解：全面的单元测试
性能问题 → 缓解：添加合适的索引
阶段 2：数据迁移（2-3 周）
任务：

 编写数据迁移脚本（Company → Partner）
 编写数据迁移脚本（Contact → Partner）
 编写数据迁移脚本（Supplier → Partner + SupplierProfile）
 编写数据迁移脚本（SupplierContact → PartnerRelation）
 在测试环境执行迁移并验证
 编写数据一致性检查脚本
 准备回滚脚本
关键代码：


# migration 文件见 3.3 节
验收标准：

100% 数据迁移成功（0 条数据丢失）
数据一致性验证通过
迁移性能可接受（<10 分钟）
回滚脚本验证通过
风险点：

数据量大导致迁移超时 → 缓解：分批迁移
数据不一致 → 缓解：全面的验证脚本
迁移失败无法回滚 → 缓解：事务保护 + 备份
阶段 3：扩展业务模型（3-4 周）
任务：

 Order 模型添加 customer 和 contact_person 字段
 PurchaseOrder 模型添加 supplier_partner 字段
 Pipeline 模型添加新字段（可选）
 更新模型 save() 方法实现自动同步
 编写 Migration 迁移 Order/PurchaseOrder 的外键引用
 编写单元测试验证新旧字段同步逻辑
 在测试环境验证
关键文件：

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_sales/models/order.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_procurement/models/purchase_order.py
验收标准：

新字段添加成功
外键迁移完成（Order.customer、PurchaseOrder.supplier_partner 填充正确）
新旧字段同步逻辑验证通过
所有测试通过
风险点：

外键数据迁移不完整 → 缓解：详细的验证脚本
save() 同步逻辑冲突 → 缓解：单元测试覆盖边缘情况
阶段 4：API 和序列化器适配（2-3 周）
任务：

 更新 OrderSerializer 支持 customer 和 contact_person
 更新 PurchaseOrderSerializer 支持 supplier_partner
 保持旧字段（company, contact, supplier）向后兼容
 更新 API 文档
 编写集成测试
 前端适配指南编写
验收标准：

API 同时支持新旧字段（向后兼容）
序列化器测试通过
API 文档更新完成
前端团队确认适配方案
风险点：

前端破坏性变更 → 缓解：保持向后兼容
API 响应过大 → 缓解：优化序列化器嵌套深度
阶段 5：前端适配和测试（4-6 周）
任务：

 前端更新客户选择组件使用 Partner API
 前端更新供应商选择组件使用 Partner API
 前端更新联系人选择组件使用 Partner API
 前端 UI 适配（支持多重角色显示）
 端到端测试（创建订单、采购订单等）
 用户验收测试（UAT）
验收标准：

所有前端页面正常工作
端到端测试通过
UAT 通过
性能测试通过
风险点：

前端开发延期 → 缓解：并行开发 + 提前对齐
用户体验下降 → 缓解：充分的 UAT
阶段 6：生产部署和监控（1-2 周）
任务：

 生产环境数据备份
 部署 Partner 模型和迁移脚本
 执行数据迁移
 部署新版本后端 API
 部署新版本前端
 监控系统运行状态
 处理生产问题
验收标准：

生产迁移成功（0 数据丢失）
系统稳定运行（无重大 bug）
性能指标正常
风险点：

生产迁移失败 → 缓解：充分测试 + 回滚方案
性能下降 → 缓解：性能测试 + 监控告警
阶段 7：废弃旧模型（6-12 个月后）
任务：

 确认所有业务已切换到 Partner
 标记旧模型和 API 为 Deprecated
 通知前端团队移除旧 API 调用
 删除旧模型字段（company, contact, supplier）
 删除旧模型（Company, Contact, Supplier）
 更新文档
验收标准：

旧 API 无调用
旧模型删除成功
系统正常运行
风险点：

遗漏旧 API 调用 → 缓解：日志分析 + API 监控
五、风险评估与缓解
5.1 技术风险
风险	影响	概率	缓解措施
数据迁移失败	高	中	充分测试、事务保护、备份、回滚脚本
外键引用遗漏	高	中	自动化扫描、代码审查、全面测试
性能下降	中	中	性能测试、索引优化、查询优化
并发问题	中	低	并发测试、数据库锁机制
软删除冲突	低	低	单元测试覆盖
5.2 业务风险
风险	影响	概率	缓解措施
业务中断	高	低	渐进式迁移、新旧并存、充分测试
用户体验下降	中	中	UAT、前端优化、培训
数据丢失	高	低	备份、验证脚本、回滚方案
前端开发延期	中	中	提前对齐、并行开发、向后兼容
5.3 组织风险
风险	影响	概率	缓解措施
团队认知不一致	中	中	充分讨论、文档化、培训
资源不足	中	中	合理排期、优先级管理
沟通不畅	低	低	定期会议、文档共享
六、成本估算
6.1 开发成本
阶段	工作量（人天）	说明
阶段 0：准备	5-10	规划、评审、测试环境准备
阶段 1：模型创建	10-15	模型、序列化器、ViewSet、测试
阶段 2：数据迁移	10-15	迁移脚本、验证、回滚方案
阶段 3：业务模型扩展	15-20	Order/PurchaseOrder 扩展、测试
阶段 4：API 适配	10-15	序列化器更新、文档、测试
阶段 5：前端适配	20-30	UI 更新、组件、端到端测试
阶段 6：生产部署	5-10	部署、监控、问题处理
总计	75-115 人天	约 3-5 个月（1-2 人团队）
6.2 测试成本
类型	工作量（人天）
单元测试	15-20
集成测试	10-15
端到端测试	10-15
UAT	5-10
总计	40-60 人天
6.3 总成本
开发 + 测试 = 115-175 人天 ≈ 6-9 个月（1 人全职）或 3-5 个月（2 人团队）

七、验证计划
7.1 单元测试
测试覆盖率目标：90%+

关键测试用例：

Partner 模型验证逻辑
自动生成 code
层级关系（parent-child）
PartnerRelation 的 is_primary 唯一性
Profile 创建和更新
权限逻辑
序列化器嵌套处理
7.2 集成测试
Partner API 完整 CRUD 流程
Order 创建时自动同步 customer/contact_person
PurchaseOrder 创建时自动同步 supplier_partner
数据迁移脚本完整性
7.3 端到端测试
创建客户 → 创建订单 → 查看订单详情
创建供应商 → 创建采购订单 → 查看采购订单详情
既是客户又是供应商的场景
前端完整业务流程
7.4 性能测试
Partner 列表查询（10000+ 记录）
嵌套 Profile 序列化性能
数据迁移性能（100000+ 记录）
八、关键文件路径清单
新增文件

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/
├── models/
│   └── partner.py (Partner, PartnerRelation, CustomerProfile, SupplierProfile, CarrierProfile)
├── serializers/
│   └── partner.py (PartnerSerializer, ProfileSerializers)
├── views/
│   └── partner_view.py (PartnerViewSet)
├── permissions/
│   └── partner_permission.py (PartnerAdminPermission, PartnerSalePermission)
└── migrations/
    ├── XXXX_add_partner_models.py
    ├── XXXX_migrate_to_partner.py
    └── XXXX_add_order_partner_fields.py
修改文件

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/
├── sea_saw_crm/
│   ├── models/
│   │   ├── company.py (添加 migrated_to_partner 字段)
│   │   ├── contact.py (添加 migrated_to_partner 字段)
│   │   └── supplier.py (添加 migrated_to_partner 字段)
│   └── urls.py (注册 PartnerViewSet)
├── sea_saw_sales/models/
│   └── order.py (添加 customer, contact_person 字段)
└── sea_saw_procurement/models/
    └── purchase_order.py (添加 supplier_partner 字段)
九、总结与建议
推荐采用方案 C（渐进式重构）的核心原因：
风险可控 - 新旧模型并存，业务不中断，可随时回滚
架构优势 - 达到与 Odoo/ERPNext 相同的统一 Partner 模型
扩展性强 - 易于添加新角色（承运商、代工厂等）
代码复用 - 统一权限、序列化器、ViewSet
符合业界最佳实践 - Partner 概念被主流 ERP 广泛采用
实施建议：
优先级：如果当前业务稳定，可以开始阶段 1（不影响现有系统）
并行开发：阶段 1-3 可以与现有功能开发并行
充分测试：每个阶段都必须有完整的测试覆盖
文档先行：在实施前完成详细的技术文档和迁移方案
团队培训：确保团队理解新架构和迁移策略
关键成功因素：
✅ 团队一致同意方案
✅ 充分的测试覆盖
✅ 详细的回滚方案
✅ 前后端充分对齐
✅ 分阶段验证和部署
Stayed in plan mode
明白了！既然项目还在开发阶段，可以直接采用方案 B 全新实现，那我帮你优化计划文件，移除所有迁移相关内容，专注于干净的 Partner 模型架构实现。

Write starry-snuggling-horizon.md
2364 lines
# Sea-Saw CRM Partner 模型重构方案（开发阶段 - 全新实现）

## 一、方案概述

### 1.1 选择方案 B：完全重构为 Partner 模型（Odoo 风格）

**核心理念：**
- 采用业界成熟的 **Partner（往来单位）** 统一模型
- 参考 Odoo ERP 的 `res.partner` 设计模式
- 通过角色标记（`is_customer`, `is_supplier`, `is_carrier` 等）支持多重身份
- 通过 Profile 模型（CustomerProfile, SupplierProfile）扩展特定角色字段
- 支持层级关系（公司 → 联系人、公司 → 分支机构）

**项目状态：**
- ✅ 开发阶段，可以删库重建
- ✅ 无历史数据迁移负担
- ✅ 可以直接实现最优架构

### 1.2 业界最佳实践参考

#### Odoo ERP - res.partner 模型
```python
class Partner(models.Model):
    name = fields.Char()
    is_company = fields.Boolean()  # 公司 vs 个人
    parent_id = fields.Many2one('res.partner')  # 层级关系

    # 角色标记（可多选）
    customer_rank = fields.Integer()  # >0 表示是客户
    supplier_rank = fields.Integer()  # >0 表示是供应商

    # 联系方式
    email, phone, mobile, website = ...

    # 地址（支持多地址）
    child_ids = fields.One2many('res.partner', 'parent_id')
```

**核心优势：**
- 统一模型，消除重复
- 支持"既是客户又是供应商"
- 层级关系灵活
- 易于扩展新角色

#### ERPNext - Customer/Supplier + Dynamic Link
```python
# 联系人通过 Dynamic Link 关联任意实体
class Contact:
    links = List[{
        'link_doctype': 'Customer' | 'Supplier',
        'link_name': 'CUST-001'
    }]
```

#### SAP Business One - Business Partner
```
Business Partner
├── Card Type: Customer / Supplier / Lead（可多选）
├── Contact Employees: []
└── Addresses: []
```

---

## 二、核心模型设计

### 2.1 Partner 模型（统一往来单位）

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/partner.py

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from sea_saw_base.models import BaseModel


class Partner(BaseModel):
    """
    统一的往来单位模型 - 支持客户、供应商、承运商、代工厂等多重角色

    设计理念（参考 Odoo res.partner）：
    - 一个实体可以同时是客户和供应商（is_customer + is_supplier）
    - 支持公司和个人（partner_type）
    - 支持层级关系（parent: 公司 → 联系人、公司 → 分支机构）
    - 扩展字段通过 Profile 模型分离
    """

    PARTNER_TYPE_COMPANY = 'company'
    PARTNER_TYPE_INDIVIDUAL = 'individual'
    PARTNER_TYPE_CHOICES = [
        (PARTNER_TYPE_COMPANY, _('Company')),
        (PARTNER_TYPE_INDIVIDUAL, _('Individual')),
    ]

    # === 基础信息 ===
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Name of the partner (company or individual)"),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("Partner Code"),
        help_text=_("Unique identifier (auto-generated: BP2024-000001)"),
    )

    partner_type = models.CharField(
        max_length=20,
        choices=PARTNER_TYPE_CHOICES,
        default=PARTNER_TYPE_COMPANY,
        verbose_name=_("Partner Type"),
        help_text=_("Company or Individual"),
    )

    # === 角色标记（多选，核心设计）===
    is_customer = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Is Customer"),
        help_text=_("Can be used as customer in sales orders"),
    )

    is_supplier = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Is Supplier"),
        help_text=_("Can be used as supplier in purchase orders"),
    )

    is_carrier = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Is Carrier"),
        help_text=_("Can be used as carrier for shipping"),
    )

    is_contractor = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Is Contractor"),
        help_text=_("Can be used as contractor for outsourcing"),
    )

    # === 层级关系（支持公司 → 联系人、公司 → 分支）===
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Parent Partner"),
        help_text=_("Parent partner (e.g., company for a contact person)"),
    )

    # === 联系方式 ===
    email = models.EmailField(
        max_length=200,
        blank=True,
        verbose_name=_("Email"),
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Phone"),
    )

    mobile = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Mobile"),
    )

    fax = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Fax"),
    )

    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
    )

    # === 地址信息 ===
    address = models.TextField(
        blank=True,
        verbose_name=_("Address"),
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("City"),
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("State/Province"),
    )

    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Country"),
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Postal Code"),
    )

    # === 业务信息 ===
    tax_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Tax ID"),
        help_text=_("Tax identification number"),
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("Is Active"),
    )

    remark = models.TextField(
        blank=True,
        verbose_name=_("Remark"),
    )

    class Meta:
        verbose_name = _("Partner")
        verbose_name_plural = _("Partners")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_customer", "is_active"]),
            models.Index(fields=["is_supplier", "is_active"]),
            models.Index(fields=["is_carrier", "is_active"]),
            models.Index(fields=["partner_type"]),
            models.Index(fields=["parent"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(is_customer=True) | models.Q(is_supplier=True) |
                      models.Q(is_carrier=True) | models.Q(is_contractor=True),
                name='partner_has_at_least_one_role'
            ),
        ]

    def __str__(self):
        return self.name or self.code or _("Unnamed Partner")

    def clean(self):
        """验证规则"""
        super().clean()

        # 至少选择一个角色
        if not any([self.is_customer, self.is_supplier, self.is_carrier, self.is_contractor]):
            raise ValidationError(
                _("At least one role must be selected (customer/supplier/carrier/contractor)")
            )

        # 个人类型不能有子记录
        if self.partner_type == self.PARTNER_TYPE_INDIVIDUAL:
            if self.children.exists():
                raise ValidationError(_("Individual partners cannot have child partners"))

        # 子记录的 parent 必须是 company 类型
        if self.parent and self.parent.partner_type != self.PARTNER_TYPE_COMPANY:
            raise ValidationError(_("Parent partner must be a company"))

        # 防止循环引用
        if self.parent:
            current = self.parent
            visited = {self.id}
            while current:
                if current.id in visited:
                    raise ValidationError(_("Circular parent relationship detected"))
                visited.add(current.id)
                current = current.parent

    def generate_code(self):
        """自动生成编号 BP2024-000001"""
        year = timezone.now().year
        count = Partner.objects.filter(created_at__year=year).count() + 1
        return f"BP{year}-{count:06d}"

    def save(self, *args, **kwargs):
        """自动生成 code"""
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    # === 便捷方法 ===
    def get_contacts(self):
        """获取所有联系人（子记录中的个人）"""
        return self.children.filter(
            partner_type=self.PARTNER_TYPE_INDIVIDUAL,
            deleted__isnull=True
        )

    def get_primary_contact(self):
        """获取主联系人"""
        relation = self.partner_relations.filter(
            is_primary=True,
            deleted__isnull=True
        ).first()
        return relation.related_partner if relation else None

    def get_role_display_list(self):
        """获取角色列表（用于显示）"""
        roles = []
        if self.is_customer:
            roles.append(_("Customer"))
        if self.is_supplier:
            roles.append(_("Supplier"))
        if self.is_carrier:
            roles.append(_("Carrier"))
        if self.is_contractor:
            roles.append(_("Contractor"))
        return roles
```

### 2.2 PartnerRelation 模型（关系管理）

```python
class PartnerRelation(BaseModel):
    """
    Partner 之间的关系

    用途：
    - 记录 Supplier 的主联系人
    - 记录 Company 的财务联系人、技术联系人
    - 支持更复杂的业务关系
    """

    RELATION_TYPE_CONTACT = 'contact'
    RELATION_TYPE_BILLING = 'billing'
    RELATION_TYPE_SHIPPING = 'shipping'
    RELATION_TYPE_TECHNICAL = 'technical'
    RELATION_TYPE_CHOICES = [
        (RELATION_TYPE_CONTACT, _('General Contact')),
        (RELATION_TYPE_BILLING, _('Billing Contact')),
        (RELATION_TYPE_SHIPPING, _('Shipping Contact')),
        (RELATION_TYPE_TECHNICAL, _('Technical Contact')),
    ]

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name='partner_relations',
        verbose_name=_("Partner"),
        help_text=_("The main partner (e.g., Company, Supplier)"),
    )

    related_partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name='reverse_relations',
        verbose_name=_("Related Partner"),
        help_text=_("The related partner (usually a contact person)"),
    )

    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_TYPE_CHOICES,
        default=RELATION_TYPE_CONTACT,
        verbose_name=_("Relation Type"),
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Is Primary"),
        help_text=_("Primary contact for this partner"),
    )

    role = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Role"),
        help_text=_("Role title (e.g., Sales Manager, CFO)"),
    )

    remark = models.TextField(
        blank=True,
        verbose_name=_("Remark"),
    )

    class Meta:
        verbose_name = _("Partner Relation")
        verbose_name_plural = _("Partner Relations")
        unique_together = [("partner", "related_partner", "relation_type", "deleted")]
        ordering = ["-is_primary", "relation_type"]
        indexes = [
            models.Index(fields=["partner", "is_primary"]),
            models.Index(fields=["related_partner"]),
        ]

    def __str__(self):
        primary_tag = " (Primary)" if self.is_primary else ""
        return f"{self.partner.name} → {self.related_partner.name}{primary_tag}"

    def save(self, *args, **kwargs):
        """确保每个 partner 只有一个主联系人"""
        if self.is_primary:
            # 移除同一 partner 的其他主联系人标记
            PartnerRelation.objects.filter(
                partner=self.partner,
                is_primary=True,
                deleted__isnull=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
```

### 2.3 Profile 模型（角色扩展信息）

```python
class CustomerProfile(BaseModel):
    """客户扩展信息（一对一）"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        limit_choices_to={'is_customer': True},
        verbose_name=_("Partner"),
    )

    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Credit Limit"),
    )

    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Payment Terms"),
        help_text=_("e.g., Net 30, Net 60"),
    )

    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Preferred Payment Method"),
        help_text=_("e.g., Wire Transfer, Credit Card"),
    )

    customer_since = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Customer Since"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Customer rating (1-5 stars)"),
    )

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")

    def __str__(self):
        return f"Customer Profile: {self.partner.name}"


class SupplierProfile(BaseModel):
    """供应商扩展信息（一对一）"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='supplier_profile',
        limit_choices_to={'is_supplier': True},
        verbose_name=_("Partner"),
    )

    payment_terms = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Payment Terms"),
    )

    currency = models.CharField(
        max_length=10,
        default='CNY',
        verbose_name=_("Preferred Currency"),
    )

    credit_limit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Credit Limit"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Supplier rating (1-5 stars)"),
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Is Approved"),
        help_text=_("Whether this supplier has been approved"),
    )

    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Name"),
    )

    bank_account = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Account Number"),
    )

    swift_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("SWIFT Code"),
    )

    class Meta:
        verbose_name = _("Supplier Profile")
        verbose_name_plural = _("Supplier Profiles")

    def __str__(self):
        return f"Supplier Profile: {self.partner.name}"


class CarrierProfile(BaseModel):
    """承运商扩展信息（一对一）"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='carrier_profile',
        limit_choices_to={'is_carrier': True},
        verbose_name=_("Partner"),
    )

    vehicle_types = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Vehicle Types"),
        help_text=_("Comma-separated (e.g., Truck, Van, Container)"),
    )

    service_routes = models.TextField(
        blank=True,
        verbose_name=_("Service Routes"),
        help_text=_("Geographic routes serviced"),
    )

    insurance_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Insurance Number"),
    )

    license_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Business License Number"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Carrier rating (1-5 stars)"),
    )

    class Meta:
        verbose_name = _("Carrier Profile")
        verbose_name_plural = _("Carrier Profiles")

    def __str__(self):
        return f"Carrier Profile: {self.partner.name}"
```

### 2.4 模型注册

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/__init__.py

from sea_saw_base.models import BaseModel, Field
from .partner import (
    Partner,
    PartnerRelation,
    CustomerProfile,
    SupplierProfile,
    CarrierProfile,
)

# 废弃旧模型（完全删除）
# - Company (已删除)
# - Contact (已删除)
# - Supplier (已删除)
# - SupplierContact (已删除)

__all__ = [
    "BaseModel",
    "Field",
    "Partner",
    "PartnerRelation",
    "CustomerProfile",
    "SupplierProfile",
    "CarrierProfile",
]
```

---

## 三、业务模型适配

### 3.1 Order 模型更新

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_sales/models/order.py

class Order(AbstractOrderBase):
    """
    销售订单

    变更：
    - company: FK(Company) → customer: FK(Partner)
    - contact: FK(Contact) → contact_person: FK(Partner)
    """

    order_code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Order Code"),
    )

    order_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Order Date"),
    )

    # === 新字段：使用 Partner ===
    customer = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_customer': True, 'partner_type': 'company'},
        related_name="customer_orders",
        verbose_name=_("Customer"),
        help_text=_("Customer partner (must be company and is_customer=True)"),
    )

    contact_person = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'partner_type': 'individual'},
        related_name="contact_orders",
        verbose_name=_("Contact Person"),
        help_text=_("Contact person for this order"),
    )

    status = models.CharField(
        max_length=32,
        choices=OrderStatusType.choices,
        default=OrderStatusType.DRAFT,
        verbose_name=_("Order Status"),
    )

    # ... 其他字段保持不变 ...

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["customer"]),
        ]

    def clean(self):
        """验证逻辑"""
        super().clean()

        # 验证 customer 必须是 company 类型且 is_customer=True
        if self.customer:
            if self.customer.partner_type != 'company':
                raise ValidationError({'customer': _("Customer must be a company")})
            if not self.customer.is_customer:
                raise ValidationError({'customer': _("Selected partner is not marked as customer")})

        # 验证 contact_person 必须是 individual 类型
        if self.contact_person and self.contact_person.partner_type != 'individual':
            raise ValidationError({'contact_person': _("Contact person must be an individual")})

        # 可选：验证 contact_person.parent == customer
        if self.contact_person and self.customer:
            if self.contact_person.parent != self.customer:
                # 警告但不阻止（允许使用其他公司的联系人）
                pass

    # ... 其他方法保持不变 ...
```

### 3.2 PurchaseOrder 模型更新

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_procurement/models/purchase_order.py

class PurchaseOrder(AbstractOrderBase):
    """
    采购订单

    变更：
    - supplier: FK(Supplier) → supplier: FK(Partner)
    """

    purchase_code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Purchase Code"),
    )

    pipeline = models.ForeignKey(
        "sea_saw_pipeline.Pipeline",
        on_delete=models.CASCADE,
        related_name="purchase_orders",
        verbose_name=_("Pipeline"),
    )

    purchase_order_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Purchase Order Date"),
    )

    # === 新字段：使用 Partner ===
    supplier = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_supplier': True},
        related_name="supplier_purchase_orders",
        verbose_name=_("Supplier"),
        help_text=_("Supplier partner (must have is_supplier=True)"),
    )

    status = models.CharField(
        max_length=32,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.DRAFT,
        verbose_name=_("Purchase Status"),
    )

    # ... 其他字段保持不变 ...

    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["purchase_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["supplier"]),
        ]

    def clean(self):
        """验证逻辑"""
        super().clean()

        # 验证 supplier 必须 is_supplier=True
        if self.supplier and not self.supplier.is_supplier:
            raise ValidationError({
                'supplier': _("Selected partner is not marked as supplier")
            })

    # ... 其他方法保持不变 ...
```

### 3.3 Pipeline 模型更新

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_pipeline/models/pipeline/pipeline.py

class Pipeline(BaseModel):
    """
    业务流程编排

    变更：
    - company: FK(Company) → customer: FK(Partner)
    - contact: FK(Contact) → contact_person: FK(Partner)
    """

    pipeline_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Pipeline Code"),
    )

    pipeline_type = models.CharField(
        max_length=50,
        choices=PipelineType.choices,
        default=PipelineType.PRODUCTION_FLOW,
        verbose_name=_("Pipeline Type"),
    )

    status = models.CharField(
        max_length=50,
        choices=PipelineStatusType.choices,
        default=PipelineStatusType.DRAFT,
        verbose_name=_("Pipeline Status"),
    )

    order = models.OneToOneField(
        "sea_saw_sales.Order",
        on_delete=models.CASCADE,
        related_name="pipeline",
        verbose_name=_("Sales Order"),
    )

    # === 新字段：使用 Partner ===
    customer = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_customer': True},
        related_name="pipelines",
        verbose_name=_("Customer"),
    )

    contact_person = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'partner_type': 'individual'},
        related_name="contact_pipelines",
        verbose_name=_("Contact Person"),
    )

    # ... 其他字段保持不变 ...

    def save(self, *args, **kwargs):
        # 自动生成 code
        if not self.pipeline_code:
            self.pipeline_code = self.generate_code()

        # 从 Order 同步 customer 和 contact_person
        if not self.customer and self.order and self.order.customer:
            self.customer = self.order.customer

        if not self.contact_person and self.order and self.order.contact_person:
            self.contact_person = self.order.contact_person

        super().save(*args, **kwargs)

    # ... 其他方法保持不变 ...
```

---

## 四、序列化器设计

### 4.1 Profile 序列化器

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/serializers/partner.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models import (
    Partner,
    PartnerRelation,
    CustomerProfile,
    SupplierProfile,
    CarrierProfile,
)
from sea_saw_base.serializers import BaseSerializer


class CustomerProfileSerializer(BaseSerializer):
    """客户扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = CustomerProfile
        fields = [
            'id',
            'credit_limit',
            'payment_terms',
            'payment_method',
            'customer_since',
            'rating',
            'created_at',
            'updated_at',
        ]


class SupplierProfileSerializer(BaseSerializer):
    """供应商扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = SupplierProfile
        fields = [
            'id',
            'payment_terms',
            'currency',
            'credit_limit',
            'rating',
            'is_approved',
            'bank_name',
            'bank_account',
            'swift_code',
            'created_at',
            'updated_at',
        ]


class CarrierProfileSerializer(BaseSerializer):
    """承运商扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = CarrierProfile
        fields = [
            'id',
            'vehicle_types',
            'service_routes',
            'insurance_no',
            'license_no',
            'rating',
            'created_at',
            'updated_at',
        ]
```

### 4.2 PartnerRelation 序列化器

```python
class PartnerRelationSerializer(BaseSerializer):
    """Partner 关系序列化器"""

    # 读取：返回嵌套对象
    related_partner = serializers.SerializerMethodField(
        read_only=True,
        label=_("Related Partner")
    )

    # 写入：只需 ID
    related_partner_id = serializers.PrimaryKeyRelatedField(
        queryset=Partner.objects.filter(deleted__isnull=True),
        source='related_partner',
        write_only=True,
        required=True,
        label=_("Related Partner ID"),
    )

    class Meta(BaseSerializer.Meta):
        model = PartnerRelation
        fields = [
            'id',
            'related_partner',
            'related_partner_id',
            'relation_type',
            'is_primary',
            'role',
            'remark',
            'created_at',
            'updated_at',
        ]

    def get_related_partner(self, obj):
        """返回简化的 partner 信息（避免循环引用）"""
        return {
            'id': obj.related_partner.id,
            'code': obj.related_partner.code,
            'name': obj.related_partner.name,
            'partner_type': obj.related_partner.partner_type,
            'email': obj.related_partner.email,
            'phone': obj.related_partner.phone,
            'mobile': obj.related_partner.mobile,
        }
```

### 4.3 Partner 主序列化器

```python
class PartnerSerializer(BaseSerializer):
    """
    Partner 主序列化器

    支持：
    - 动态嵌套 Profile（customer_profile, supplier_profile, carrier_profile）
    - 嵌套 PartnerRelation
    - 写入时自动创建/更新 Profile
    """

    # === 读取字段（嵌套对象）===
    customer_profile = CustomerProfileSerializer(
        read_only=True,
        label=_("Customer Profile")
    )

    supplier_profile = SupplierProfileSerializer(
        read_only=True,
        label=_("Supplier Profile")
    )

    carrier_profile = CarrierProfileSerializer(
        read_only=True,
        label=_("Carrier Profile")
    )

    partner_relations = PartnerRelationSerializer(
        many=True,
        read_only=True,
        label=_("Partner Relations")
    )

    # 父级 Partner（嵌套显示）
    parent_info = serializers.SerializerMethodField(
        read_only=True,
        label=_("Parent Info")
    )

    # 角色列表（便于前端显示）
    roles = serializers.SerializerMethodField(
        read_only=True,
        label=_("Roles")
    )

    # === 写入字段（简化输入）===
    customer_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Customer Profile Data"),
        help_text=_("Customer-specific fields (credit_limit, payment_terms, etc.)"),
    )

    supplier_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Supplier Profile Data"),
        help_text=_("Supplier-specific fields (rating, is_approved, bank info, etc.)"),
    )

    carrier_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Carrier Profile Data"),
        help_text=_("Carrier-specific fields (vehicle_types, service_routes, etc.)"),
    )

    relations_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        label=_("Relations Data"),
        help_text=_("List of partner relations (contact persons)"),
    )

    class Meta(BaseSerializer.Meta):
        model = Partner
        fields = [
            'id',
            'code',
            'name',
            'partner_type',
            'is_customer',
            'is_supplier',
            'is_carrier',
            'is_contractor',
            'parent',
            'parent_info',
            'roles',
            'email',
            'phone',
            'mobile',
            'fax',
            'website',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'tax_id',
            'is_active',
            'remark',
            'customer_profile',
            'supplier_profile',
            'carrier_profile',
            'partner_relations',
            'customer_profile_data',
            'supplier_profile_data',
            'carrier_profile_data',
            'relations_data',
            'owner',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['code']

    def get_parent_info(self, obj):
        """返回父级 Partner 简化信息"""
        if not obj.parent:
            return None
        return {
            'id': obj.parent.id,
            'code': obj.parent.code,
            'name': obj.parent.name,
        }

    def get_roles(self, obj):
        """返回角色列表"""
        return obj.get_role_display_list()

    def create(self, validated_data):
        """创建 Partner 并处理嵌套 Profile 和 Relations"""
        customer_profile_data = validated_data.pop('customer_profile_data', None)
        supplier_profile_data = validated_data.pop('supplier_profile_data', None)
        carrier_profile_data = validated_data.pop('carrier_profile_data', None)
        relations_data = validated_data.pop('relations_data', [])

        # 创建 Partner
        partner = super().create(validated_data)

        # 创建 Profile（根据角色）
        if customer_profile_data and partner.is_customer:
            CustomerProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **customer_profile_data
            )

        if supplier_profile_data and partner.is_supplier:
            SupplierProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **supplier_profile_data
            )

        if carrier_profile_data and partner.is_carrier:
            CarrierProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **carrier_profile_data
            )

        # 创建关系
        for relation in relations_data:
            PartnerRelation.objects.create(
                partner=partner,
                owner=partner.owner,
                **relation
            )

        return partner

    def update(self, instance, validated_data):
        """更新 Partner 并处理嵌套 Profile 和 Relations"""
        customer_profile_data = validated_data.pop('customer_profile_data', None)
        supplier_profile_data = validated_data.pop('supplier_profile_data', None)
        carrier_profile_data = validated_data.pop('carrier_profile_data', None)
        relations_data = validated_data.pop('relations_data', None)

        # 更新 Partner
        partner = super().update(instance, validated_data)

        # 更新或创建 Profile
        if customer_profile_data is not None:
            if partner.is_customer:
                CustomerProfile.objects.update_or_create(
                    partner=partner,
                    defaults={**customer_profile_data, 'owner': partner.owner}
                )
            else:
                # 如果角色被移除，删除 Profile
                CustomerProfile.objects.filter(partner=partner).delete()

        if supplier_profile_data is not None:
            if partner.is_supplier:
                SupplierProfile.objects.update_or_create(
                    partner=partner,
                    defaults={**supplier_profile_data, 'owner': partner.owner}
                )
            else:
                SupplierProfile.objects.filter(partner=partner).delete()

        if carrier_profile_data is not None:
            if partner.is_carrier:
                CarrierProfile.objects.update_or_create(
                    partner=partner,
                    defaults={**carrier_profile_data, 'owner': partner.owner}
                )
            else:
                CarrierProfile.objects.filter(partner=partner).delete()

        # 更新关系（删除旧的，创建新的）
        if relations_data is not None:
            PartnerRelation.objects.filter(partner=partner).delete()
            for relation in relations_data:
                PartnerRelation.objects.create(
                    partner=partner,
                    owner=partner.owner,
                    **relation
                )

        return partner
```

---

## 五、权限控制

### 5.1 统一权限类

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/permissions/partner_permission.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class PartnerAdminPermission(BasePermission):
    """Partner Admin 权限 - Admin 可以访问所有 Partner"""

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "ADMIN"

    def has_object_permission(self, request, view, obj):
        return True


class PartnerSalePermission(BasePermission):
    """Partner Sale 权限 - Sale 基于 owner 访问控制"""

    def has_permission(self, request, view):
        role_type = getattr(request.user.role, "role_type", None)
        if role_type != "SALE":
            return False

        return view.action in {
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        }

    def has_object_permission(self, request, view, obj):
        user = request.user
        owner = getattr(obj, "owner", None)

        if request.method in SAFE_METHODS:
            # 读取权限：自己或可见用户
            if owner == user:
                return True

            get_visible_users = getattr(owner, "get_all_visible_users", None)
            if callable(get_visible_users):
                return user in get_visible_users()

            return False
        else:
            # 修改/删除权限：仅 owner
            return owner == user
```

### 5.2 权限注册

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/permissions/__init__.py

from .partner_permission import PartnerAdminPermission, PartnerSalePermission

# 移除旧权限类
# - CompanyAdminPermission (已删除)
# - ContactAdminPermission (已删除)
# - SupplierAdminPermission (已删除)

__all__ = [
    "PartnerAdminPermission",
    "PartnerSalePermission",
]
```

---

## 六、ViewSet 和 API 端点

### 6.1 PartnerViewSet

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/views/partner_view.py

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from ..models import Partner
from ..serializers import PartnerSerializer
from sea_saw_base.metadata import BaseMetadata
from ..permissions import PartnerAdminPermission, PartnerSalePermission


class PartnerViewSet(ModelViewSet):
    """Partner ViewSet - 统一的往来单位 API"""

    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [
        IsAuthenticated,
        PartnerAdminPermission | PartnerSalePermission,
    ]
    metadata_class = BaseMetadata

    search_fields = ["^name", "^code", "email", "phone", "mobile"]
    filterset_fields = [
        "is_customer",
        "is_supplier",
        "is_carrier",
        "is_contractor",
        "partner_type",
        "is_active",
        "parent",
    ]

    def get_queryset(self):
        """权限过滤"""
        user = self.request.user
        role_type = getattr(user.role, "role_type", None)

        # 软删除过滤
        base_queryset = self.queryset.filter(deleted__isnull=True)

        # Admin 看所有
        if role_type == "ADMIN":
            return base_queryset

        # Sale 看自己和可见用户的
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return base_queryset.none()

        return base_queryset.filter(owner__in=get_users())

    @action(detail=False, methods=['get'], url_path='customers')
    def customers(self, request):
        """
        客户列表（is_customer=True）

        GET /api/sea-saw-crm/partners/customers/
        """
        queryset = self.get_queryset().filter(
            is_customer=True,
            partner_type='company'
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='suppliers')
    def suppliers(self, request):
        """
        供应商列表（is_supplier=True）

        GET /api/sea-saw-crm/partners/suppliers/
        """
        queryset = self.get_queryset().filter(is_supplier=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='carriers')
    def carriers(self, request):
        """
        承运商列表（is_carrier=True）

        GET /api/sea-saw-crm/partners/carriers/
        """
        queryset = self.get_queryset().filter(is_carrier=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='contacts')
    def contacts(self, request):
        """
        联系人列表（partner_type='individual'）

        GET /api/sea-saw-crm/partners/contacts/
        """
        queryset = self.get_queryset().filter(partner_type='individual')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='children')
    def get_children(self, request, pk=None):
        """
        获取子 Partner（联系人、分支机构）

        GET /api/sea-saw-crm/partners/{id}/children/
        """
        partner = self.get_object()
        queryset = partner.get_contacts()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

### 6.2 URL 配置

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PartnerViewSet

router = DefaultRouter()
router.register(r"partners", PartnerViewSet)

# 移除旧路由
# - companies (已删除)
# - contacts (已删除)
# - suppliers (已删除)

app_name = "sea-saw-crm"
urlpatterns = [
    path("", include(router.urls)),
]
```

### 6.3 API 端点清单

```
# Partner CRUD
GET    /api/sea-saw-crm/partners/                    # 所有 Partner（支持过滤）
POST   /api/sea-saw-crm/partners/                    # 创建 Partner
GET    /api/sea-saw-crm/partners/{id}/               # Partner 详情
PATCH  /api/sea-saw-crm/partners/{id}/               # 更新 Partner
PUT    /api/sea-saw-crm/partners/{id}/               # 完整更新 Partner
DELETE /api/sea-saw-crm/partners/{id}/               # 删除 Partner（软删除）

# 自定义端点
GET    /api/sea-saw-crm/partners/customers/          # 客户列表（is_customer=True）
GET    /api/sea-saw-crm/partners/suppliers/          # 供应商列表（is_supplier=True）
GET    /api/sea-saw-crm/partners/carriers/           # 承运商列表（is_carrier=True）
GET    /api/sea-saw-crm/partners/contacts/           # 联系人列表（partner_type='individual'）
GET    /api/sea-saw-crm/partners/{id}/children/      # 子 Partner（联系人、分支）

# 查询参数示例
GET /api/sea-saw-crm/partners/?is_customer=true&is_active=true
GET /api/sea-saw-crm/partners/?partner_type=company&is_supplier=true
GET /api/sea-saw-crm/partners/?search=ABC
```

---

## 七、Django Admin 配置

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/admin/partner.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..models import (
    Partner,
    PartnerRelation,
    CustomerProfile,
    SupplierProfile,
    CarrierProfile,
)


class PartnerRelationInline(admin.TabularInline):
    """内联显示 Partner 关系"""
    model = PartnerRelation
    fk_name = 'partner'
    extra = 1
    fields = ['related_partner', 'relation_type', 'is_primary', 'role', 'remark']
    autocomplete_fields = ['related_partner']


class CustomerProfileInline(admin.StackedInline):
    """内联显示客户扩展信息"""
    model = CustomerProfile
    can_delete = False
    fields = ['credit_limit', 'payment_terms', 'payment_method', 'customer_since', 'rating']


class SupplierProfileInline(admin.StackedInline):
    """内联显示供应商扩展信息"""
    model = SupplierProfile
    can_delete = False
    fields = [
        'payment_terms',
        'currency',
        'credit_limit',
        'rating',
        'is_approved',
        'bank_name',
        'bank_account',
        'swift_code',
    ]


class CarrierProfileInline(admin.StackedInline):
    """内联显示承运商扩展信息"""
    model = CarrierProfile
    can_delete = False
    fields = ['vehicle_types', 'service_routes', 'insurance_no', 'license_no', 'rating']


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    """Partner Admin"""

    list_display = [
        'code',
        'name',
        'partner_type',
        'get_roles_display',
        'email',
        'phone',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'partner_type',
        'is_customer',
        'is_supplier',
        'is_carrier',
        'is_contractor',
        'is_active',
        'created_at',
    ]

    search_fields = [
        'code',
        'name',
        'email',
        'phone',
        'mobile',
        'tax_id',
    ]

    readonly_fields = ['code', 'created_at', 'updated_at']

    autocomplete_fields = ['parent']

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    'code',
                    'name',
                    'partner_type',
                    'parent',
                )
            },
        ),
        (
            _("Roles"),
            {
                "fields": (
                    'is_customer',
                    'is_supplier',
                    'is_carrier',
                    'is_contractor',
                )
            },
        ),
        (
            _("Contact Information"),
            {
                "fields": (
                    'email',
                    'phone',
                    'mobile',
                    'fax',
                    'website',
                )
            },
        ),
        (
            _("Address Information"),
            {
                "fields": (
                    'address',
                    'city',
                    'state',
                    'country',
                    'postal_code',
                )
            },
        ),
        (
            _("Business Information"),
            {
                "fields": (
                    'tax_id',
                    'is_active',
                    'remark',
                )
            },
        ),
        (
            _("System Information"),
            {
                "fields": (
                    'owner',
                    'created_by',
                    'updated_by',
                    'created_at',
                    'updated_at',
                )
            },
        ),
    )

    def get_inlines(self, request, obj=None):
        """动态显示 Profile Inline"""
        inlines = [PartnerRelationInline]

        if obj:
            if obj.is_customer:
                inlines.append(CustomerProfileInline)
            if obj.is_supplier:
                inlines.append(SupplierProfileInline)
            if obj.is_carrier:
                inlines.append(CarrierProfileInline)

        return inlines

    def get_roles_display(self, obj):
        """显示角色列表"""
        roles = obj.get_role_display_list()
        return ", ".join(roles) if roles else "-"
    get_roles_display.short_description = _("Roles")


@admin.register(PartnerRelation)
class PartnerRelationAdmin(admin.ModelAdmin):
    """PartnerRelation Admin"""

    list_display = [
        'partner',
        'related_partner',
        'relation_type',
        'is_primary',
        'role',
    ]

    list_filter = ['relation_type', 'is_primary']

    search_fields = [
        'partner__name',
        'related_partner__name',
        'role',
    ]

    autocomplete_fields = ['partner', 'related_partner']
```

### 7.2 Admin 注册

```python
# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/admin/__init__.py

from .partner import PartnerAdmin, PartnerRelationAdmin

# 移除旧 Admin
# - CompanyAdmin (已删除)
# - ContactAdmin (已删除)
# - SupplierAdmin (已删除)

__all__ = [
    "PartnerAdmin",
    "PartnerRelationAdmin",
]
```

---

## 八、实施步骤

### 阶段 1：删除旧模型（1 天）

**任务清单：**
- [ ] 备份当前数据库（如有测试数据）
- [ ] 删除旧模型文件：
  - `sea_saw_crm/models/company.py`
  - `sea_saw_crm/models/contact.py`
  - `sea_saw_crm/models/supplier.py`
- [ ] 删除旧序列化器：
  - `sea_saw_crm/serializers/company.py`
  - `sea_saw_crm/serializers/contact.py`
  - `sea_saw_crm/serializers/supplier.py`
- [ ] 删除旧视图：
  - `sea_saw_crm/views/company_view.py`
  - `sea_saw_crm/views/contact_view.py`
  - `sea_saw_crm/views/supplier_view.py`
- [ ] 删除旧权限：
  - `sea_saw_crm/permissions/company_permission.py`
  - `sea_saw_crm/permissions/contact_permission.py`
  - `sea_saw_crm/permissions/supplier_permission.py`
- [ ] 删除旧 Admin：
  - `sea_saw_crm/admin/company.py`
  - `sea_saw_crm/admin/contact.py`
  - `sea_saw_crm/admin/supplier.py`

**验收标准：**
- 旧模型文件全部删除
- 导入语句无错误

---

### 阶段 2：创建 Partner 模型（2-3 天）

**任务清单：**
- [ ] 创建 `partner.py` 模型文件（Partner, PartnerRelation, Profiles）
- [ ] 更新 `models/__init__.py` 导出 Partner 模型
- [ ] 创建 Django Migration
- [ ] 运行 Migration 创建数据库表
- [ ] 编写模型单元测试（覆盖率 90%+）
- [ ] 测试验证逻辑（clean() 方法）

**关键文件：**
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/partner.py`
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/__init__.py`

**验收标准：**
- Migration 成功执行
- 所有模型测试通过
- 数据库表创建成功
- clean() 验证逻辑正确

---

### 阶段 3：更新业务模型（2-3 天）

**任务清单：**
- [ ] 更新 `Order` 模型（company → customer, contact → contact_person）
- [ ] 更新 `PurchaseOrder` 模型（supplier → supplier:Partner）
- [ ] 更新 `Pipeline` 模型（company → customer, contact → contact_person）
- [ ] 创建 Migration
- [ ] 运行 Migration
- [ ] 编写单元测试

**关键文件：**
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_sales/models/order.py`
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_procurement/models/purchase_order.py`
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_pipeline/models/pipeline/pipeline.py`

**验收标准：**
- 外键引用更新成功
- Migration 无错误
- 测试覆盖所有场景

---

### 阶段 4：创建序列化器和 ViewSet（2-3 天）

**任务清单：**
- [ ] 创建 `partner.py` 序列化器（PartnerSerializer, ProfileSerializers）
- [ ] 创建 `partner_view.py` ViewSet
- [ ] 创建 `partner_permission.py` 权限类
- [ ] 更新 `urls.py` 注册路由
- [ ] 编写 API 单元测试
- [ ] 测试自定义端点（customers, suppliers, carriers, contacts）

**关键文件：**
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/serializers/partner.py`
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/views/partner_view.py`
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/permissions/partner_permission.py`
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/urls.py`

**验收标准：**
- API 端点正常工作
- CRUD 操作成功
- 权限逻辑正确
- 嵌套 Profile 创建/更新成功

---

### 阶段 5：创建 Django Admin（1 天）

**任务清单：**
- [ ] 创建 `partner.py` Admin 配置
- [ ] 配置 Inline（PartnerRelation, Profiles）
- [ ] 更新 `admin/__init__.py`
- [ ] 测试 Admin 界面

**关键文件：**
- `/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/admin/partner.py`

**验收标准：**
- Admin 界面正常显示
- Inline 正常工作
- 创建/编辑 Partner 成功

---

### 阶段 6：集成测试（2-3 天）

**任务清单：**
- [ ] 端到端测试：创建客户 → 创建订单 → 查看订单详情
- [ ] 端到端测试：创建供应商 → 创建采购订单 → 查看采购详情
- [ ] 测试"既是客户又是供应商"场景
- [ ] 测试层级关系（公司 → 联系人）
- [ ] 测试 PartnerRelation（主联系人）
- [ ] 性能测试（Partner 列表查询）

**验收标准：**
- 所有端到端测试通过
- 性能测试达标
- 无重大 bug

---

### 阶段 7：文档和前端对接（1-2 天）

**任务清单：**
- [ ] 编写 API 文档
- [ ] 编写前端对接指南
- [ ] 提供前端示例代码
- [ ] 与前端团队对齐

**交付物：**
- API 文档（Swagger/OpenAPI）
- 前端对接指南（Markdown）
- 示例代码（TypeScript）

---

## 九、测试计划

### 9.1 单元测试（覆盖率目标：90%+）

#### Partner 模型测试
```python
# tests/test_partner_model.py

class PartnerModelTest(TestCase):
    def test_create_customer(self):
        """测试创建客户"""
        partner = Partner.objects.create(
            name="ABC Company",
            partner_type='company',
            is_customer=True,
        )
        self.assertTrue(partner.is_customer)
        self.assertIsNotNone(partner.code)

    def test_create_supplier(self):
        """测试创建供应商"""
        partner = Partner.objects.create(
            name="XYZ Supplier",
            partner_type='company',
            is_supplier=True,
        )
        self.assertTrue(partner.is_supplier)

    def test_dual_role(self):
        """测试既是客户又是供应商"""
        partner = Partner.objects.create(
            name="Dual Role Company",
            partner_type='company',
            is_customer=True,
            is_supplier=True,
        )
        self.assertTrue(partner.is_customer)
        self.assertTrue(partner.is_supplier)

    def test_contact_person(self):
        """测试联系人（个人类型）"""
        company = Partner.objects.create(
            name="Company A",
            partner_type='company',
            is_customer=True,
        )
        contact = Partner.objects.create(
            name="John Doe",
            partner_type='individual',
            parent=company,
            is_customer=False,
        )
        self.assertEqual(contact.parent, company)

    def test_validation_at_least_one_role(self):
        """测试必须至少选择一个角色"""
        partner = Partner(
            name="Invalid Partner",
            partner_type='company',
            is_customer=False,
            is_supplier=False,
            is_carrier=False,
            is_contractor=False,
        )
        with self.assertRaises(ValidationError):
            partner.full_clean()

    def test_circular_parent_prevention(self):
        """测试防止循环引用"""
        # 待实现
        pass
```

#### PartnerRelation 测试
```python
class PartnerRelationTest(TestCase):
    def test_primary_contact_uniqueness(self):
        """测试主联系人唯一性"""
        company = Partner.objects.create(
            name="Company",
            partner_type='company',
            is_customer=True,
        )
        contact1 = Partner.objects.create(
            name="Contact 1",
            partner_type='individual',
            parent=company,
        )
        contact2 = Partner.objects.create(
            name="Contact 2",
            partner_type='individual',
            parent=company,
        )

        # 创建第一个主联系人
        rel1 = PartnerRelation.objects.create(
            partner=company,
            related_partner=contact1,
            is_primary=True,
        )

        # 创建第二个主联系人（应该自动移除第一个的主标记）
        rel2 = PartnerRelation.objects.create(
            partner=company,
            related_partner=contact2,
            is_primary=True,
        )

        rel1.refresh_from_db()
        self.assertFalse(rel1.is_primary)
        self.assertTrue(rel2.is_primary)
```

### 9.2 API 集成测试

```python
class PartnerAPITest(APITestCase):
    def test_create_partner(self):
        """测试创建 Partner API"""
        data = {
            'name': 'New Customer',
            'partner_type': 'company',
            'is_customer': True,
            'email': 'customer@example.com',
            'customer_profile_data': {
                'credit_limit': '10000.00',
                'payment_terms': 'Net 30',
            }
        }
        response = self.client.post('/api/sea-saw-crm/partners/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['customer_profile'])

    def test_list_customers(self):
        """测试客户列表端点"""
        response = self.client.get('/api/sea-saw-crm/partners/customers/')
        self.assertEqual(response.status_code, 200)

    def test_list_suppliers(self):
        """测试供应商列表端点"""
        response = self.client.get('/api/sea-saw-crm/partners/suppliers/')
        self.assertEqual(response.status_code, 200)
```

### 9.3 端到端测试

```python
class E2EOrderTest(TestCase):
    def test_create_order_with_partner(self):
        """端到端：创建客户 → 创建订单 → 查看订单"""
        # 1. 创建客户
        customer = Partner.objects.create(
            name="Customer A",
            partner_type='company',
            is_customer=True,
        )

        # 2. 创建联系人
        contact = Partner.objects.create(
            name="Contact Person",
            partner_type='individual',
            parent=customer,
        )

        # 3. 创建订单
        order = Order.objects.create(
            customer=customer,
            contact_person=contact,
            order_date=timezone.now().date(),
        )

        # 4. 验证
        self.assertEqual(order.customer, customer)
        self.assertEqual(order.contact_person, contact)
```

---

## 十、API 使用示例

### 10.1 创建客户

```http
POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "ABC Company Ltd.",
  "partner_type": "company",
  "is_customer": true,
  "email": "sales@abc.com",
  "phone": "+86-10-12345678",
  "address": "123 Main St, Beijing",
  "city": "Beijing",
  "country": "China",
  "tax_id": "91110000XXXXXXXX",
  "customer_profile_data": {
    "credit_limit": "100000.00",
    "payment_terms": "Net 30",
    "payment_method": "Wire Transfer"
  }
}
```

### 10.2 创建供应商

```http
POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "XYZ Supplier Inc.",
  "partner_type": "company",
  "is_supplier": true,
  "email": "procurement@xyz.com",
  "phone": "+1-555-1234",
  "supplier_profile_data": {
    "payment_terms": "COD",
    "currency": "USD",
    "rating": 4,
    "is_approved": true,
    "bank_name": "Bank of America",
    "bank_account": "1234567890",
    "swift_code": "BOFAUS3N"
  }
}
```

### 10.3 创建既是客户又是供应商的 Partner

```http
POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "Dual Role Company",
  "partner_type": "company",
  "is_customer": true,
  "is_supplier": true,
  "email": "contact@dual.com",
  "customer_profile_data": {
    "credit_limit": "50000.00",
    "payment_terms": "Net 60"
  },
  "supplier_profile_data": {
    "payment_terms": "Net 30",
    "currency": "CNY",
    "is_approved": true
  }
}
```

### 10.4 创建联系人

```http
POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "John Doe",
  "partner_type": "individual",
  "parent": 5,  # 父级 Partner ID（公司）
  "email": "john.doe@abc.com",
  "mobile": "+86-138-1234-5678",
  "is_customer": false  # 联系人通常不直接作为客户
}
```

### 10.5 为供应商添加联系人关系

```http
POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "Supplier X",
  "partner_type": "company",
  "is_supplier": true,
  "relations_data": [
    {
      "related_partner_id": 10,  # 联系人 Partner ID
      "relation_type": "contact",
      "is_primary": true,
      "role": "Sales Manager"
    },
    {
      "related_partner_id": 11,
      "relation_type": "technical",
      "is_primary": false,
      "role": "Technical Support"
    }
  ],
  "supplier_profile_data": {
    "is_approved": true
  }
}
```

### 10.6 查询客户列表

```http
GET /api/sea-saw-crm/partners/customers/
```

### 10.7 查询供应商列表

```http
GET /api/sea-saw-crm/partners/suppliers/
```

### 10.8 查询联系人列表

```http
GET /api/sea-saw-crm/partners/contacts/
```

### 10.9 复杂查询（既是客户又是供应商）

```http
GET /api/sea-saw-crm/partners/?is_customer=true&is_supplier=true
```

---

## 十一、关键文件路径清单

### 新增文件

```
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/
├── models/
│   └── partner.py (Partner, PartnerRelation, CustomerProfile, SupplierProfile, CarrierProfile)
├── serializers/
│   └── partner.py (PartnerSerializer, ProfileSerializers, PartnerRelationSerializer)
├── views/
│   └── partner_view.py (PartnerViewSet)
├── permissions/
│   └── partner_permission.py (PartnerAdminPermission, PartnerSalePermission)
├── admin/
│   └── partner.py (PartnerAdmin, PartnerRelationAdmin)
└── migrations/
    └── XXXX_create_partner_models.py
```

### 修改文件

```
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/
├── sea_saw_crm/
│   ├── models/__init__.py (更新导出)
│   ├── serializers/__init__.py (更新导出)
│   ├── views/__init__.py (更新导出)
│   ├── permissions/__init__.py (更新导出)
│   ├── admin/__init__.py (更新导出)
│   └── urls.py (注册 PartnerViewSet)
├── sea_saw_sales/models/
│   └── order.py (company → customer, contact → contact_person)
├── sea_saw_procurement/models/
│   └── purchase_order.py (supplier → supplier:Partner)
└── sea_saw_pipeline/models/pipeline/
    └── pipeline.py (company → customer, contact → contact_person)
```

### 删除文件

```
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/
├── models/
│   ├── company.py (删除)
│   ├── contact.py (删除)
│   └── supplier.py (删除)
├── serializers/
│   ├── company.py (删除)
│   ├── contact.py (删除)
│   └── supplier.py (删除)
├── views/
│   ├── company_view.py (删除)
│   ├── contact_view.py (删除)
│   └── supplier_view.py (删除)
├── permissions/
│   ├── company_permission.py (删除)
│   ├── contact_permission.py (删除)
│   └── supplier_permission.py (删除)
└── admin/
    ├── company.py (删除)
    ├── contact.py (删除)
    └── supplier.py (删除)
```

---

## 十二、验证清单

### 12.1 功能验证

- [ ] Partner CRUD 操作正常
- [ ] 创建客户并添加 CustomerProfile 成功
- [ ] 创建供应商并添加 SupplierProfile 成功
- [ ] 创建承运商并添加 CarrierProfile 成功
- [ ] 创建"既是客户又是供应商"的 Partner 成功
- [ ] 创建联系人（individual）并关联公司成功
- [ ] PartnerRelation 创建和管理正常
- [ ] 主联系人唯一性验证正确
- [ ] Order 使用 customer/contact_person 创建成功
- [ ] PurchaseOrder 使用 supplier:Partner 创建成功
- [ ] Pipeline 同步 customer/contact_person 正常

### 12.2 权限验证

- [ ] Admin 可以查看所有 Partner
- [ ] Sale 只能查看自己和可见用户的 Partner
- [ ] Sale 只能修改/删除自己创建的 Partner
- [ ] 权限逻辑与旧模型一致

### 12.3 API 验证

- [ ] `/api/sea-saw-crm/partners/` 端点正常
- [ ] `/api/sea-saw-crm/partners/customers/` 返回正确
- [ ] `/api/sea-saw-crm/partners/suppliers/` 返回正确
- [ ] `/api/sea-saw-crm/partners/carriers/` 返回正确
- [ ] `/api/sea-saw-crm/partners/contacts/` 返回正确
- [ ] `/api/sea-saw-crm/partners/{id}/children/` 返回正确
- [ ] 查询参数过滤正常（is_customer, is_supplier 等）
- [ ] 搜索功能正常

### 12.4 性能验证

- [ ] Partner 列表查询性能可接受（<500ms for 10000 records）
- [ ] 嵌套 Profile 序列化性能可接受
- [ ] 数据库索引正确创建

---

## 十三、总结与建议

### 推荐采用方案 B 的核心优势

1. **统一模型** - Partner 统一客户、供应商、联系人、承运商
2. **多重角色** - 同一 Partner 可以是客户+供应商（is_customer + is_supplier）
3. **层级关系** - 支持公司 → 联系人、公司 → 分支机构
4. **扩展性强** - 通过 Profile 模型扩展特定角色字段
5. **符合业界最佳实践** - Odoo、SAP、ERPNext 都采用类似设计
6. **简化权限** - 一套 PartnerPermission 替代三套权限类
7. **代码复用** - 统一序列化器、ViewSet、Admin

### 实施时间估算

| 阶段 | 任务 | 工作量 |
|------|------|--------|
| 阶段 1 | 删除旧模型 | 0.5 天 |
| 阶段 2 | 创建 Partner 模型 | 2-3 天 |
| 阶段 3 | 更新业务模型 | 2-3 天 |
| 阶段 4 | 序列化器和 ViewSet | 2-3 天 |
| 阶段 5 | Django Admin | 1 天 |
| 阶段 6 | 集成测试 | 2-3 天 |
| 阶段 7 | 文档和对接 | 1-2 天 |
| **总计** | - | **11-16 天** |

**团队配置建议：**
- 1 名后端开发（全职）：10-15 天
- 或 2 名后端开发（并行）：5-8 天

### 关键成功因素

- ✅ 开发阶段，无历史数据包袱
- ✅ 可以直接实现最优架构
- ✅ 充分的单元测试和集成测试
- ✅ 与前端团队充分对齐
- ✅ 详细的 API 文档

### 后续优化建议

1. **地址模型独立** - 未来可以创建 Address 模型支持多地址
2. **标签系统** - 添加 Tag/Label 模型支持灵活分类
3. **版本控制** - 使用 django-simple-history 追踪修改历史
4. **全文搜索** - 使用 PostgreSQL Full-Text Search 或 Elasticsearch
5. **图片支持** - 添加 logo/avatar 字段使用 django-storages

---

**方案 B 是开发阶段的最佳选择，建议立即实施！**
完成！我已经优化了计划文件，专注于方案 B：完全重构为 Partner 模型（Odoo 风格），适配开发阶段的实际情况。

主要优化点
移除所有迁移相关内容 - 无历史数据包袱，直接删除旧模型
简化实施步骤 - 从 7 个阶段减少到实际需要的步骤
完整代码示例 - Partner、PartnerRelation、Profile 模型的完整实现
业务模型适配 - Order、PurchaseOrder、Pipeline 直接使用 Partner
API 使用示例 - 详细的请求/响应示例
测试计划 - 单元测试、集成测试、端到端测试
工期估算 - 11-16 天（1-2 人团队）
核心设计：

Partner 统一模型（is_customer, is_supplier, is_carrier, is_contractor）
PartnerRelation 关系管理（主联系人、财务联系人等）
Profile 模型（CustomerProfile, SupplierProfile, CarrierProfile）扩展特定字段
层级关系（parent: 公司 → 联系人、公司 → 分支机构）
Claude’s Plan
Sea-Saw CRM Partner 模型重构方案（开发阶段 - 全新实现）
一、方案概述
1.1 选择方案 B：完全重构为 Partner 模型（Odoo 风格）
核心理念：

采用业界成熟的 Partner（往来单位） 统一模型
参考 Odoo ERP 的 res.partner 设计模式
通过角色标记（is_customer, is_supplier, is_carrier 等）支持多重身份
通过 Profile 模型（CustomerProfile, SupplierProfile）扩展特定角色字段
支持层级关系（公司 → 联系人、公司 → 分支机构）
项目状态：

✅ 开发阶段，可以删库重建
✅ 无历史数据迁移负担
✅ 可以直接实现最优架构
1.2 业界最佳实践参考
Odoo ERP - res.partner 模型

class Partner(models.Model):
    name = fields.Char()
    is_company = fields.Boolean()  # 公司 vs 个人
    parent_id = fields.Many2one('res.partner')  # 层级关系

    # 角色标记（可多选）
    customer_rank = fields.Integer()  # >0 表示是客户
    supplier_rank = fields.Integer()  # >0 表示是供应商

    # 联系方式
    email, phone, mobile, website = ...

    # 地址（支持多地址）
    child_ids = fields.One2many('res.partner', 'parent_id')
核心优势：

统一模型，消除重复
支持"既是客户又是供应商"
层级关系灵活
易于扩展新角色
ERPNext - Customer/Supplier + Dynamic Link

# 联系人通过 Dynamic Link 关联任意实体
class Contact:
    links = List[{
        'link_doctype': 'Customer' | 'Supplier',
        'link_name': 'CUST-001'
    }]
SAP Business One - Business Partner

Business Partner
├── Card Type: Customer / Supplier / Lead（可多选）
├── Contact Employees: []
└── Addresses: []
二、核心模型设计
2.1 Partner 模型（统一往来单位）

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/partner.py

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from sea_saw_base.models import BaseModel


class Partner(BaseModel):
    """
    统一的往来单位模型 - 支持客户、供应商、承运商、代工厂等多重角色

    设计理念（参考 Odoo res.partner）：
    - 一个实体可以同时是客户和供应商（is_customer + is_supplier）
    - 支持公司和个人（partner_type）
    - 支持层级关系（parent: 公司 → 联系人、公司 → 分支机构）
    - 扩展字段通过 Profile 模型分离
    """

    PARTNER_TYPE_COMPANY = 'company'
    PARTNER_TYPE_INDIVIDUAL = 'individual'
    PARTNER_TYPE_CHOICES = [
        (PARTNER_TYPE_COMPANY, _('Company')),
        (PARTNER_TYPE_INDIVIDUAL, _('Individual')),
    ]

    # === 基础信息 ===
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Name of the partner (company or individual)"),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("Partner Code"),
        help_text=_("Unique identifier (auto-generated: BP2024-000001)"),
    )

    partner_type = models.CharField(
        max_length=20,
        choices=PARTNER_TYPE_CHOICES,
        default=PARTNER_TYPE_COMPANY,
        verbose_name=_("Partner Type"),
        help_text=_("Company or Individual"),
    )

    # === 角色标记（多选，核心设计）===
    is_customer = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Is Customer"),
        help_text=_("Can be used as customer in sales orders"),
    )

    is_supplier = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Is Supplier"),
        help_text=_("Can be used as supplier in purchase orders"),
    )

    is_carrier = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Is Carrier"),
        help_text=_("Can be used as carrier for shipping"),
    )

    is_contractor = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Is Contractor"),
        help_text=_("Can be used as contractor for outsourcing"),
    )

    # === 层级关系（支持公司 → 联系人、公司 → 分支）===
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Parent Partner"),
        help_text=_("Parent partner (e.g., company for a contact person)"),
    )

    # === 联系方式 ===
    email = models.EmailField(
        max_length=200,
        blank=True,
        verbose_name=_("Email"),
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Phone"),
    )

    mobile = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Mobile"),
    )

    fax = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Fax"),
    )

    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
    )

    # === 地址信息 ===
    address = models.TextField(
        blank=True,
        verbose_name=_("Address"),
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("City"),
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("State/Province"),
    )

    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Country"),
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Postal Code"),
    )

    # === 业务信息 ===
    tax_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Tax ID"),
        help_text=_("Tax identification number"),
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("Is Active"),
    )

    remark = models.TextField(
        blank=True,
        verbose_name=_("Remark"),
    )

    class Meta:
        verbose_name = _("Partner")
        verbose_name_plural = _("Partners")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_customer", "is_active"]),
            models.Index(fields=["is_supplier", "is_active"]),
            models.Index(fields=["is_carrier", "is_active"]),
            models.Index(fields=["partner_type"]),
            models.Index(fields=["parent"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(is_customer=True) | models.Q(is_supplier=True) |
                      models.Q(is_carrier=True) | models.Q(is_contractor=True),
                name='partner_has_at_least_one_role'
            ),
        ]

    def __str__(self):
        return self.name or self.code or _("Unnamed Partner")

    def clean(self):
        """验证规则"""
        super().clean()

        # 至少选择一个角色
        if not any([self.is_customer, self.is_supplier, self.is_carrier, self.is_contractor]):
            raise ValidationError(
                _("At least one role must be selected (customer/supplier/carrier/contractor)")
            )

        # 个人类型不能有子记录
        if self.partner_type == self.PARTNER_TYPE_INDIVIDUAL:
            if self.children.exists():
                raise ValidationError(_("Individual partners cannot have child partners"))

        # 子记录的 parent 必须是 company 类型
        if self.parent and self.parent.partner_type != self.PARTNER_TYPE_COMPANY:
            raise ValidationError(_("Parent partner must be a company"))

        # 防止循环引用
        if self.parent:
            current = self.parent
            visited = {self.id}
            while current:
                if current.id in visited:
                    raise ValidationError(_("Circular parent relationship detected"))
                visited.add(current.id)
                current = current.parent

    def generate_code(self):
        """自动生成编号 BP2024-000001"""
        year = timezone.now().year
        count = Partner.objects.filter(created_at__year=year).count() + 1
        return f"BP{year}-{count:06d}"

    def save(self, *args, **kwargs):
        """自动生成 code"""
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    # === 便捷方法 ===
    def get_contacts(self):
        """获取所有联系人（子记录中的个人）"""
        return self.children.filter(
            partner_type=self.PARTNER_TYPE_INDIVIDUAL,
            deleted__isnull=True
        )

    def get_primary_contact(self):
        """获取主联系人"""
        relation = self.partner_relations.filter(
            is_primary=True,
            deleted__isnull=True
        ).first()
        return relation.related_partner if relation else None

    def get_role_display_list(self):
        """获取角色列表（用于显示）"""
        roles = []
        if self.is_customer:
            roles.append(_("Customer"))
        if self.is_supplier:
            roles.append(_("Supplier"))
        if self.is_carrier:
            roles.append(_("Carrier"))
        if self.is_contractor:
            roles.append(_("Contractor"))
        return roles
2.2 PartnerRelation 模型（关系管理）

class PartnerRelation(BaseModel):
    """
    Partner 之间的关系

    用途：
    - 记录 Supplier 的主联系人
    - 记录 Company 的财务联系人、技术联系人
    - 支持更复杂的业务关系
    """

    RELATION_TYPE_CONTACT = 'contact'
    RELATION_TYPE_BILLING = 'billing'
    RELATION_TYPE_SHIPPING = 'shipping'
    RELATION_TYPE_TECHNICAL = 'technical'
    RELATION_TYPE_CHOICES = [
        (RELATION_TYPE_CONTACT, _('General Contact')),
        (RELATION_TYPE_BILLING, _('Billing Contact')),
        (RELATION_TYPE_SHIPPING, _('Shipping Contact')),
        (RELATION_TYPE_TECHNICAL, _('Technical Contact')),
    ]

    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name='partner_relations',
        verbose_name=_("Partner"),
        help_text=_("The main partner (e.g., Company, Supplier)"),
    )

    related_partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name='reverse_relations',
        verbose_name=_("Related Partner"),
        help_text=_("The related partner (usually a contact person)"),
    )

    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_TYPE_CHOICES,
        default=RELATION_TYPE_CONTACT,
        verbose_name=_("Relation Type"),
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Is Primary"),
        help_text=_("Primary contact for this partner"),
    )

    role = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Role"),
        help_text=_("Role title (e.g., Sales Manager, CFO)"),
    )

    remark = models.TextField(
        blank=True,
        verbose_name=_("Remark"),
    )

    class Meta:
        verbose_name = _("Partner Relation")
        verbose_name_plural = _("Partner Relations")
        unique_together = [("partner", "related_partner", "relation_type", "deleted")]
        ordering = ["-is_primary", "relation_type"]
        indexes = [
            models.Index(fields=["partner", "is_primary"]),
            models.Index(fields=["related_partner"]),
        ]

    def __str__(self):
        primary_tag = " (Primary)" if self.is_primary else ""
        return f"{self.partner.name} → {self.related_partner.name}{primary_tag}"

    def save(self, *args, **kwargs):
        """确保每个 partner 只有一个主联系人"""
        if self.is_primary:
            # 移除同一 partner 的其他主联系人标记
            PartnerRelation.objects.filter(
                partner=self.partner,
                is_primary=True,
                deleted__isnull=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
2.3 Profile 模型（角色扩展信息）

class CustomerProfile(BaseModel):
    """客户扩展信息（一对一）"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        limit_choices_to={'is_customer': True},
        verbose_name=_("Partner"),
    )

    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Credit Limit"),
    )

    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Payment Terms"),
        help_text=_("e.g., Net 30, Net 60"),
    )

    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Preferred Payment Method"),
        help_text=_("e.g., Wire Transfer, Credit Card"),
    )

    customer_since = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Customer Since"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Customer rating (1-5 stars)"),
    )

    class Meta:
        verbose_name = _("Customer Profile")
        verbose_name_plural = _("Customer Profiles")

    def __str__(self):
        return f"Customer Profile: {self.partner.name}"


class SupplierProfile(BaseModel):
    """供应商扩展信息（一对一）"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='supplier_profile',
        limit_choices_to={'is_supplier': True},
        verbose_name=_("Partner"),
    )

    payment_terms = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Payment Terms"),
    )

    currency = models.CharField(
        max_length=10,
        default='CNY',
        verbose_name=_("Preferred Currency"),
    )

    credit_limit = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Credit Limit"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Supplier rating (1-5 stars)"),
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Is Approved"),
        help_text=_("Whether this supplier has been approved"),
    )

    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Name"),
    )

    bank_account = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Account Number"),
    )

    swift_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("SWIFT Code"),
    )

    class Meta:
        verbose_name = _("Supplier Profile")
        verbose_name_plural = _("Supplier Profiles")

    def __str__(self):
        return f"Supplier Profile: {self.partner.name}"


class CarrierProfile(BaseModel):
    """承运商扩展信息（一对一）"""

    partner = models.OneToOneField(
        Partner,
        on_delete=models.CASCADE,
        related_name='carrier_profile',
        limit_choices_to={'is_carrier': True},
        verbose_name=_("Partner"),
    )

    vehicle_types = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Vehicle Types"),
        help_text=_("Comma-separated (e.g., Truck, Van, Container)"),
    )

    service_routes = models.TextField(
        blank=True,
        verbose_name=_("Service Routes"),
        help_text=_("Geographic routes serviced"),
    )

    insurance_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Insurance Number"),
    )

    license_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Business License Number"),
    )

    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Carrier rating (1-5 stars)"),
    )

    class Meta:
        verbose_name = _("Carrier Profile")
        verbose_name_plural = _("Carrier Profiles")

    def __str__(self):
        return f"Carrier Profile: {self.partner.name}"
2.4 模型注册

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/__init__.py

from sea_saw_base.models import BaseModel, Field
from .partner import (
    Partner,
    PartnerRelation,
    CustomerProfile,
    SupplierProfile,
    CarrierProfile,
)

# 废弃旧模型（完全删除）
# - Company (已删除)
# - Contact (已删除)
# - Supplier (已删除)
# - SupplierContact (已删除)

__all__ = [
    "BaseModel",
    "Field",
    "Partner",
    "PartnerRelation",
    "CustomerProfile",
    "SupplierProfile",
    "CarrierProfile",
]
三、业务模型适配
3.1 Order 模型更新

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_sales/models/order.py

class Order(AbstractOrderBase):
    """
    销售订单

    变更：
    - company: FK(Company) → customer: FK(Partner)
    - contact: FK(Contact) → contact_person: FK(Partner)
    """

    order_code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Order Code"),
    )

    order_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Order Date"),
    )

    # === 新字段：使用 Partner ===
    customer = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_customer': True, 'partner_type': 'company'},
        related_name="customer_orders",
        verbose_name=_("Customer"),
        help_text=_("Customer partner (must be company and is_customer=True)"),
    )

    contact_person = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'partner_type': 'individual'},
        related_name="contact_orders",
        verbose_name=_("Contact Person"),
        help_text=_("Contact person for this order"),
    )

    status = models.CharField(
        max_length=32,
        choices=OrderStatusType.choices,
        default=OrderStatusType.DRAFT,
        verbose_name=_("Order Status"),
    )

    # ... 其他字段保持不变 ...

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["customer"]),
        ]

    def clean(self):
        """验证逻辑"""
        super().clean()

        # 验证 customer 必须是 company 类型且 is_customer=True
        if self.customer:
            if self.customer.partner_type != 'company':
                raise ValidationError({'customer': _("Customer must be a company")})
            if not self.customer.is_customer:
                raise ValidationError({'customer': _("Selected partner is not marked as customer")})

        # 验证 contact_person 必须是 individual 类型
        if self.contact_person and self.contact_person.partner_type != 'individual':
            raise ValidationError({'contact_person': _("Contact person must be an individual")})

        # 可选：验证 contact_person.parent == customer
        if self.contact_person and self.customer:
            if self.contact_person.parent != self.customer:
                # 警告但不阻止（允许使用其他公司的联系人）
                pass

    # ... 其他方法保持不变 ...
3.2 PurchaseOrder 模型更新

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_procurement/models/purchase_order.py

class PurchaseOrder(AbstractOrderBase):
    """
    采购订单

    变更：
    - supplier: FK(Supplier) → supplier: FK(Partner)
    """

    purchase_code = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Purchase Code"),
    )

    pipeline = models.ForeignKey(
        "sea_saw_pipeline.Pipeline",
        on_delete=models.CASCADE,
        related_name="purchase_orders",
        verbose_name=_("Pipeline"),
    )

    purchase_order_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Purchase Order Date"),
    )

    # === 新字段：使用 Partner ===
    supplier = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_supplier': True},
        related_name="supplier_purchase_orders",
        verbose_name=_("Supplier"),
        help_text=_("Supplier partner (must have is_supplier=True)"),
    )

    status = models.CharField(
        max_length=32,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.DRAFT,
        verbose_name=_("Purchase Status"),
    )

    # ... 其他字段保持不变 ...

    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["purchase_code"]),
            models.Index(fields=["status"]),
            models.Index(fields=["supplier"]),
        ]

    def clean(self):
        """验证逻辑"""
        super().clean()

        # 验证 supplier 必须 is_supplier=True
        if self.supplier and not self.supplier.is_supplier:
            raise ValidationError({
                'supplier': _("Selected partner is not marked as supplier")
            })

    # ... 其他方法保持不变 ...
3.3 Pipeline 模型更新

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_pipeline/models/pipeline/pipeline.py

class Pipeline(BaseModel):
    """
    业务流程编排

    变更：
    - company: FK(Company) → customer: FK(Partner)
    - contact: FK(Contact) → contact_person: FK(Partner)
    """

    pipeline_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Pipeline Code"),
    )

    pipeline_type = models.CharField(
        max_length=50,
        choices=PipelineType.choices,
        default=PipelineType.PRODUCTION_FLOW,
        verbose_name=_("Pipeline Type"),
    )

    status = models.CharField(
        max_length=50,
        choices=PipelineStatusType.choices,
        default=PipelineStatusType.DRAFT,
        verbose_name=_("Pipeline Status"),
    )

    order = models.OneToOneField(
        "sea_saw_sales.Order",
        on_delete=models.CASCADE,
        related_name="pipeline",
        verbose_name=_("Sales Order"),
    )

    # === 新字段：使用 Partner ===
    customer = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_customer': True},
        related_name="pipelines",
        verbose_name=_("Customer"),
    )

    contact_person = models.ForeignKey(
        "sea_saw_crm.Partner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'partner_type': 'individual'},
        related_name="contact_pipelines",
        verbose_name=_("Contact Person"),
    )

    # ... 其他字段保持不变 ...

    def save(self, *args, **kwargs):
        # 自动生成 code
        if not self.pipeline_code:
            self.pipeline_code = self.generate_code()

        # 从 Order 同步 customer 和 contact_person
        if not self.customer and self.order and self.order.customer:
            self.customer = self.order.customer

        if not self.contact_person and self.order and self.order.contact_person:
            self.contact_person = self.order.contact_person

        super().save(*args, **kwargs)

    # ... 其他方法保持不变 ...
四、序列化器设计
4.1 Profile 序列化器

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/serializers/partner.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models import (
    Partner,
    PartnerRelation,
    CustomerProfile,
    SupplierProfile,
    CarrierProfile,
)
from sea_saw_base.serializers import BaseSerializer


class CustomerProfileSerializer(BaseSerializer):
    """客户扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = CustomerProfile
        fields = [
            'id',
            'credit_limit',
            'payment_terms',
            'payment_method',
            'customer_since',
            'rating',
            'created_at',
            'updated_at',
        ]


class SupplierProfileSerializer(BaseSerializer):
    """供应商扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = SupplierProfile
        fields = [
            'id',
            'payment_terms',
            'currency',
            'credit_limit',
            'rating',
            'is_approved',
            'bank_name',
            'bank_account',
            'swift_code',
            'created_at',
            'updated_at',
        ]


class CarrierProfileSerializer(BaseSerializer):
    """承运商扩展信息序列化器"""

    class Meta(BaseSerializer.Meta):
        model = CarrierProfile
        fields = [
            'id',
            'vehicle_types',
            'service_routes',
            'insurance_no',
            'license_no',
            'rating',
            'created_at',
            'updated_at',
        ]
4.2 PartnerRelation 序列化器

class PartnerRelationSerializer(BaseSerializer):
    """Partner 关系序列化器"""

    # 读取：返回嵌套对象
    related_partner = serializers.SerializerMethodField(
        read_only=True,
        label=_("Related Partner")
    )

    # 写入：只需 ID
    related_partner_id = serializers.PrimaryKeyRelatedField(
        queryset=Partner.objects.filter(deleted__isnull=True),
        source='related_partner',
        write_only=True,
        required=True,
        label=_("Related Partner ID"),
    )

    class Meta(BaseSerializer.Meta):
        model = PartnerRelation
        fields = [
            'id',
            'related_partner',
            'related_partner_id',
            'relation_type',
            'is_primary',
            'role',
            'remark',
            'created_at',
            'updated_at',
        ]

    def get_related_partner(self, obj):
        """返回简化的 partner 信息（避免循环引用）"""
        return {
            'id': obj.related_partner.id,
            'code': obj.related_partner.code,
            'name': obj.related_partner.name,
            'partner_type': obj.related_partner.partner_type,
            'email': obj.related_partner.email,
            'phone': obj.related_partner.phone,
            'mobile': obj.related_partner.mobile,
        }
4.3 Partner 主序列化器

class PartnerSerializer(BaseSerializer):
    """
    Partner 主序列化器

    支持：
    - 动态嵌套 Profile（customer_profile, supplier_profile, carrier_profile）
    - 嵌套 PartnerRelation
    - 写入时自动创建/更新 Profile
    """

    # === 读取字段（嵌套对象）===
    customer_profile = CustomerProfileSerializer(
        read_only=True,
        label=_("Customer Profile")
    )

    supplier_profile = SupplierProfileSerializer(
        read_only=True,
        label=_("Supplier Profile")
    )

    carrier_profile = CarrierProfileSerializer(
        read_only=True,
        label=_("Carrier Profile")
    )

    partner_relations = PartnerRelationSerializer(
        many=True,
        read_only=True,
        label=_("Partner Relations")
    )

    # 父级 Partner（嵌套显示）
    parent_info = serializers.SerializerMethodField(
        read_only=True,
        label=_("Parent Info")
    )

    # 角色列表（便于前端显示）
    roles = serializers.SerializerMethodField(
        read_only=True,
        label=_("Roles")
    )

    # === 写入字段（简化输入）===
    customer_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Customer Profile Data"),
        help_text=_("Customer-specific fields (credit_limit, payment_terms, etc.)"),
    )

    supplier_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Supplier Profile Data"),
        help_text=_("Supplier-specific fields (rating, is_approved, bank info, etc.)"),
    )

    carrier_profile_data = serializers.DictField(
        write_only=True,
        required=False,
        label=_("Carrier Profile Data"),
        help_text=_("Carrier-specific fields (vehicle_types, service_routes, etc.)"),
    )

    relations_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        label=_("Relations Data"),
        help_text=_("List of partner relations (contact persons)"),
    )

    class Meta(BaseSerializer.Meta):
        model = Partner
        fields = [
            'id',
            'code',
            'name',
            'partner_type',
            'is_customer',
            'is_supplier',
            'is_carrier',
            'is_contractor',
            'parent',
            'parent_info',
            'roles',
            'email',
            'phone',
            'mobile',
            'fax',
            'website',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'tax_id',
            'is_active',
            'remark',
            'customer_profile',
            'supplier_profile',
            'carrier_profile',
            'partner_relations',
            'customer_profile_data',
            'supplier_profile_data',
            'carrier_profile_data',
            'relations_data',
            'owner',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['code']

    def get_parent_info(self, obj):
        """返回父级 Partner 简化信息"""
        if not obj.parent:
            return None
        return {
            'id': obj.parent.id,
            'code': obj.parent.code,
            'name': obj.parent.name,
        }

    def get_roles(self, obj):
        """返回角色列表"""
        return obj.get_role_display_list()

    def create(self, validated_data):
        """创建 Partner 并处理嵌套 Profile 和 Relations"""
        customer_profile_data = validated_data.pop('customer_profile_data', None)
        supplier_profile_data = validated_data.pop('supplier_profile_data', None)
        carrier_profile_data = validated_data.pop('carrier_profile_data', None)
        relations_data = validated_data.pop('relations_data', [])

        # 创建 Partner
        partner = super().create(validated_data)

        # 创建 Profile（根据角色）
        if customer_profile_data and partner.is_customer:
            CustomerProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **customer_profile_data
            )

        if supplier_profile_data and partner.is_supplier:
            SupplierProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **supplier_profile_data
            )

        if carrier_profile_data and partner.is_carrier:
            CarrierProfile.objects.create(
                partner=partner,
                owner=partner.owner,
                **carrier_profile_data
            )

        # 创建关系
        for relation in relations_data:
            PartnerRelation.objects.create(
                partner=partner,
                owner=partner.owner,
                **relation
            )

        return partner

    def update(self, instance, validated_data):
        """更新 Partner 并处理嵌套 Profile 和 Relations"""
        customer_profile_data = validated_data.pop('customer_profile_data', None)
        supplier_profile_data = validated_data.pop('supplier_profile_data', None)
        carrier_profile_data = validated_data.pop('carrier_profile_data', None)
        relations_data = validated_data.pop('relations_data', None)

        # 更新 Partner
        partner = super().update(instance, validated_data)

        # 更新或创建 Profile
        if customer_profile_data is not None:
            if partner.is_customer:
                CustomerProfile.objects.update_or_create(
                    partner=partner,
                    defaults={**customer_profile_data, 'owner': partner.owner}
                )
            else:
                # 如果角色被移除，删除 Profile
                CustomerProfile.objects.filter(partner=partner).delete()

        if supplier_profile_data is not None:
            if partner.is_supplier:
                SupplierProfile.objects.update_or_create(
                    partner=partner,
                    defaults={**supplier_profile_data, 'owner': partner.owner}
                )
            else:
                SupplierProfile.objects.filter(partner=partner).delete()

        if carrier_profile_data is not None:
            if partner.is_carrier:
                CarrierProfile.objects.update_or_create(
                    partner=partner,
                    defaults={**carrier_profile_data, 'owner': partner.owner}
                )
            else:
                CarrierProfile.objects.filter(partner=partner).delete()

        # 更新关系（删除旧的，创建新的）
        if relations_data is not None:
            PartnerRelation.objects.filter(partner=partner).delete()
            for relation in relations_data:
                PartnerRelation.objects.create(
                    partner=partner,
                    owner=partner.owner,
                    **relation
                )

        return partner
五、权限控制
5.1 统一权限类

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/permissions/partner_permission.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class PartnerAdminPermission(BasePermission):
    """Partner Admin 权限 - Admin 可以访问所有 Partner"""

    def has_permission(self, request, view):
        return getattr(request.user.role, "role_type", None) == "ADMIN"

    def has_object_permission(self, request, view, obj):
        return True


class PartnerSalePermission(BasePermission):
    """Partner Sale 权限 - Sale 基于 owner 访问控制"""

    def has_permission(self, request, view):
        role_type = getattr(request.user.role, "role_type", None)
        if role_type != "SALE":
            return False

        return view.action in {
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        }

    def has_object_permission(self, request, view, obj):
        user = request.user
        owner = getattr(obj, "owner", None)

        if request.method in SAFE_METHODS:
            # 读取权限：自己或可见用户
            if owner == user:
                return True

            get_visible_users = getattr(owner, "get_all_visible_users", None)
            if callable(get_visible_users):
                return user in get_visible_users()

            return False
        else:
            # 修改/删除权限：仅 owner
            return owner == user
5.2 权限注册

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/permissions/__init__.py

from .partner_permission import PartnerAdminPermission, PartnerSalePermission

# 移除旧权限类
# - CompanyAdminPermission (已删除)
# - ContactAdminPermission (已删除)
# - SupplierAdminPermission (已删除)

__all__ = [
    "PartnerAdminPermission",
    "PartnerSalePermission",
]
六、ViewSet 和 API 端点
6.1 PartnerViewSet

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/views/partner_view.py

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from ..models import Partner
from ..serializers import PartnerSerializer
from sea_saw_base.metadata import BaseMetadata
from ..permissions import PartnerAdminPermission, PartnerSalePermission


class PartnerViewSet(ModelViewSet):
    """Partner ViewSet - 统一的往来单位 API"""

    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [
        IsAuthenticated,
        PartnerAdminPermission | PartnerSalePermission,
    ]
    metadata_class = BaseMetadata

    search_fields = ["^name", "^code", "email", "phone", "mobile"]
    filterset_fields = [
        "is_customer",
        "is_supplier",
        "is_carrier",
        "is_contractor",
        "partner_type",
        "is_active",
        "parent",
    ]

    def get_queryset(self):
        """权限过滤"""
        user = self.request.user
        role_type = getattr(user.role, "role_type", None)

        # 软删除过滤
        base_queryset = self.queryset.filter(deleted__isnull=True)

        # Admin 看所有
        if role_type == "ADMIN":
            return base_queryset

        # Sale 看自己和可见用户的
        get_users = getattr(user, "get_all_visible_users", None)
        if not callable(get_users):
            return base_queryset.none()

        return base_queryset.filter(owner__in=get_users())

    @action(detail=False, methods=['get'], url_path='customers')
    def customers(self, request):
        """
        客户列表（is_customer=True）

        GET /api/sea-saw-crm/partners/customers/
        """
        queryset = self.get_queryset().filter(
            is_customer=True,
            partner_type='company'
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='suppliers')
    def suppliers(self, request):
        """
        供应商列表（is_supplier=True）

        GET /api/sea-saw-crm/partners/suppliers/
        """
        queryset = self.get_queryset().filter(is_supplier=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='carriers')
    def carriers(self, request):
        """
        承运商列表（is_carrier=True）

        GET /api/sea-saw-crm/partners/carriers/
        """
        queryset = self.get_queryset().filter(is_carrier=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='contacts')
    def contacts(self, request):
        """
        联系人列表（partner_type='individual'）

        GET /api/sea-saw-crm/partners/contacts/
        """
        queryset = self.get_queryset().filter(partner_type='individual')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='children')
    def get_children(self, request, pk=None):
        """
        获取子 Partner（联系人、分支机构）

        GET /api/sea-saw-crm/partners/{id}/children/
        """
        partner = self.get_object()
        queryset = partner.get_contacts()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
6.2 URL 配置

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PartnerViewSet

router = DefaultRouter()
router.register(r"partners", PartnerViewSet)

# 移除旧路由
# - companies (已删除)
# - contacts (已删除)
# - suppliers (已删除)

app_name = "sea-saw-crm"
urlpatterns = [
    path("", include(router.urls)),
]
6.3 API 端点清单

# Partner CRUD
GET    /api/sea-saw-crm/partners/                    # 所有 Partner（支持过滤）
POST   /api/sea-saw-crm/partners/                    # 创建 Partner
GET    /api/sea-saw-crm/partners/{id}/               # Partner 详情
PATCH  /api/sea-saw-crm/partners/{id}/               # 更新 Partner
PUT    /api/sea-saw-crm/partners/{id}/               # 完整更新 Partner
DELETE /api/sea-saw-crm/partners/{id}/               # 删除 Partner（软删除）

# 自定义端点
GET    /api/sea-saw-crm/partners/customers/          # 客户列表（is_customer=True）
GET    /api/sea-saw-crm/partners/suppliers/          # 供应商列表（is_supplier=True）
GET    /api/sea-saw-crm/partners/carriers/           # 承运商列表（is_carrier=True）
GET    /api/sea-saw-crm/partners/contacts/           # 联系人列表（partner_type='individual'）
GET    /api/sea-saw-crm/partners/{id}/children/      # 子 Partner（联系人、分支）

# 查询参数示例
GET /api/sea-saw-crm/partners/?is_customer=true&is_active=true
GET /api/sea-saw-crm/partners/?partner_type=company&is_supplier=true
GET /api/sea-saw-crm/partners/?search=ABC
七、Django Admin 配置

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/admin/partner.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..models import (
    Partner,
    PartnerRelation,
    CustomerProfile,
    SupplierProfile,
    CarrierProfile,
)


class PartnerRelationInline(admin.TabularInline):
    """内联显示 Partner 关系"""
    model = PartnerRelation
    fk_name = 'partner'
    extra = 1
    fields = ['related_partner', 'relation_type', 'is_primary', 'role', 'remark']
    autocomplete_fields = ['related_partner']


class CustomerProfileInline(admin.StackedInline):
    """内联显示客户扩展信息"""
    model = CustomerProfile
    can_delete = False
    fields = ['credit_limit', 'payment_terms', 'payment_method', 'customer_since', 'rating']


class SupplierProfileInline(admin.StackedInline):
    """内联显示供应商扩展信息"""
    model = SupplierProfile
    can_delete = False
    fields = [
        'payment_terms',
        'currency',
        'credit_limit',
        'rating',
        'is_approved',
        'bank_name',
        'bank_account',
        'swift_code',
    ]


class CarrierProfileInline(admin.StackedInline):
    """内联显示承运商扩展信息"""
    model = CarrierProfile
    can_delete = False
    fields = ['vehicle_types', 'service_routes', 'insurance_no', 'license_no', 'rating']


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    """Partner Admin"""

    list_display = [
        'code',
        'name',
        'partner_type',
        'get_roles_display',
        'email',
        'phone',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'partner_type',
        'is_customer',
        'is_supplier',
        'is_carrier',
        'is_contractor',
        'is_active',
        'created_at',
    ]

    search_fields = [
        'code',
        'name',
        'email',
        'phone',
        'mobile',
        'tax_id',
    ]

    readonly_fields = ['code', 'created_at', 'updated_at']

    autocomplete_fields = ['parent']

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    'code',
                    'name',
                    'partner_type',
                    'parent',
                )
            },
        ),
        (
            _("Roles"),
            {
                "fields": (
                    'is_customer',
                    'is_supplier',
                    'is_carrier',
                    'is_contractor',
                )
            },
        ),
        (
            _("Contact Information"),
            {
                "fields": (
                    'email',
                    'phone',
                    'mobile',
                    'fax',
                    'website',
                )
            },
        ),
        (
            _("Address Information"),
            {
                "fields": (
                    'address',
                    'city',
                    'state',
                    'country',
                    'postal_code',
                )
            },
        ),
        (
            _("Business Information"),
            {
                "fields": (
                    'tax_id',
                    'is_active',
                    'remark',
                )
            },
        ),
        (
            _("System Information"),
            {
                "fields": (
                    'owner',
                    'created_by',
                    'updated_by',
                    'created_at',
                    'updated_at',
                )
            },
        ),
    )

    def get_inlines(self, request, obj=None):
        """动态显示 Profile Inline"""
        inlines = [PartnerRelationInline]

        if obj:
            if obj.is_customer:
                inlines.append(CustomerProfileInline)
            if obj.is_supplier:
                inlines.append(SupplierProfileInline)
            if obj.is_carrier:
                inlines.append(CarrierProfileInline)

        return inlines

    def get_roles_display(self, obj):
        """显示角色列表"""
        roles = obj.get_role_display_list()
        return ", ".join(roles) if roles else "-"
    get_roles_display.short_description = _("Roles")


@admin.register(PartnerRelation)
class PartnerRelationAdmin(admin.ModelAdmin):
    """PartnerRelation Admin"""

    list_display = [
        'partner',
        'related_partner',
        'relation_type',
        'is_primary',
        'role',
    ]

    list_filter = ['relation_type', 'is_primary']

    search_fields = [
        'partner__name',
        'related_partner__name',
        'role',
    ]

    autocomplete_fields = ['partner', 'related_partner']
7.2 Admin 注册

# /Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/admin/__init__.py

from .partner import PartnerAdmin, PartnerRelationAdmin

# 移除旧 Admin
# - CompanyAdmin (已删除)
# - ContactAdmin (已删除)
# - SupplierAdmin (已删除)

__all__ = [
    "PartnerAdmin",
    "PartnerRelationAdmin",
]
八、实施步骤
阶段 1：删除旧模型（1 天）
任务清单：

 备份当前数据库（如有测试数据）
 删除旧模型文件：
sea_saw_crm/models/company.py
sea_saw_crm/models/contact.py
sea_saw_crm/models/supplier.py
 删除旧序列化器：
sea_saw_crm/serializers/company.py
sea_saw_crm/serializers/contact.py
sea_saw_crm/serializers/supplier.py
 删除旧视图：
sea_saw_crm/views/company_view.py
sea_saw_crm/views/contact_view.py
sea_saw_crm/views/supplier_view.py
 删除旧权限：
sea_saw_crm/permissions/company_permission.py
sea_saw_crm/permissions/contact_permission.py
sea_saw_crm/permissions/supplier_permission.py
 删除旧 Admin：
sea_saw_crm/admin/company.py
sea_saw_crm/admin/contact.py
sea_saw_crm/admin/supplier.py
验收标准：

旧模型文件全部删除
导入语句无错误
阶段 2：创建 Partner 模型（2-3 天）
任务清单：

 创建 partner.py 模型文件（Partner, PartnerRelation, Profiles）
 更新 models/__init__.py 导出 Partner 模型
 创建 Django Migration
 运行 Migration 创建数据库表
 编写模型单元测试（覆盖率 90%+）
 测试验证逻辑（clean() 方法）
关键文件：

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/partner.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/models/__init__.py
验收标准：

Migration 成功执行
所有模型测试通过
数据库表创建成功
clean() 验证逻辑正确
阶段 3：更新业务模型（2-3 天）
任务清单：

 更新 Order 模型（company → customer, contact → contact_person）
 更新 PurchaseOrder 模型（supplier → supplier:Partner）
 更新 Pipeline 模型（company → customer, contact → contact_person）
 创建 Migration
 运行 Migration
 编写单元测试
关键文件：

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_sales/models/order.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_procurement/models/purchase_order.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_pipeline/models/pipeline/pipeline.py
验收标准：

外键引用更新成功
Migration 无错误
测试覆盖所有场景
阶段 4：创建序列化器和 ViewSet（2-3 天）
任务清单：

 创建 partner.py 序列化器（PartnerSerializer, ProfileSerializers）
 创建 partner_view.py ViewSet
 创建 partner_permission.py 权限类
 更新 urls.py 注册路由
 编写 API 单元测试
 测试自定义端点（customers, suppliers, carriers, contacts）
关键文件：

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/serializers/partner.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/views/partner_view.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/permissions/partner_permission.py
/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/urls.py
验收标准：

API 端点正常工作
CRUD 操作成功
权限逻辑正确
嵌套 Profile 创建/更新成功
阶段 5：创建 Django Admin（1 天）
任务清单：

 创建 partner.py Admin 配置
 配置 Inline（PartnerRelation, Profiles）
 更新 admin/__init__.py
 测试 Admin 界面
关键文件：

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/admin/partner.py
验收标准：

Admin 界面正常显示
Inline 正常工作
创建/编辑 Partner 成功
阶段 6：集成测试（2-3 天）
任务清单：

 端到端测试：创建客户 → 创建订单 → 查看订单详情
 端到端测试：创建供应商 → 创建采购订单 → 查看采购详情
 测试"既是客户又是供应商"场景
 测试层级关系（公司 → 联系人）
 测试 PartnerRelation（主联系人）
 性能测试（Partner 列表查询）
验收标准：

所有端到端测试通过
性能测试达标
无重大 bug
阶段 7：文档和前端对接（1-2 天）
任务清单：

 编写 API 文档
 编写前端对接指南
 提供前端示例代码
 与前端团队对齐
交付物：

API 文档（Swagger/OpenAPI）
前端对接指南（Markdown）
示例代码（TypeScript）
九、测试计划
9.1 单元测试（覆盖率目标：90%+）
Partner 模型测试

# tests/test_partner_model.py

class PartnerModelTest(TestCase):
    def test_create_customer(self):
        """测试创建客户"""
        partner = Partner.objects.create(
            name="ABC Company",
            partner_type='company',
            is_customer=True,
        )
        self.assertTrue(partner.is_customer)
        self.assertIsNotNone(partner.code)

    def test_create_supplier(self):
        """测试创建供应商"""
        partner = Partner.objects.create(
            name="XYZ Supplier",
            partner_type='company',
            is_supplier=True,
        )
        self.assertTrue(partner.is_supplier)

    def test_dual_role(self):
        """测试既是客户又是供应商"""
        partner = Partner.objects.create(
            name="Dual Role Company",
            partner_type='company',
            is_customer=True,
            is_supplier=True,
        )
        self.assertTrue(partner.is_customer)
        self.assertTrue(partner.is_supplier)

    def test_contact_person(self):
        """测试联系人（个人类型）"""
        company = Partner.objects.create(
            name="Company A",
            partner_type='company',
            is_customer=True,
        )
        contact = Partner.objects.create(
            name="John Doe",
            partner_type='individual',
            parent=company,
            is_customer=False,
        )
        self.assertEqual(contact.parent, company)

    def test_validation_at_least_one_role(self):
        """测试必须至少选择一个角色"""
        partner = Partner(
            name="Invalid Partner",
            partner_type='company',
            is_customer=False,
            is_supplier=False,
            is_carrier=False,
            is_contractor=False,
        )
        with self.assertRaises(ValidationError):
            partner.full_clean()

    def test_circular_parent_prevention(self):
        """测试防止循环引用"""
        # 待实现
        pass
PartnerRelation 测试

class PartnerRelationTest(TestCase):
    def test_primary_contact_uniqueness(self):
        """测试主联系人唯一性"""
        company = Partner.objects.create(
            name="Company",
            partner_type='company',
            is_customer=True,
        )
        contact1 = Partner.objects.create(
            name="Contact 1",
            partner_type='individual',
            parent=company,
        )
        contact2 = Partner.objects.create(
            name="Contact 2",
            partner_type='individual',
            parent=company,
        )

        # 创建第一个主联系人
        rel1 = PartnerRelation.objects.create(
            partner=company,
            related_partner=contact1,
            is_primary=True,
        )

        # 创建第二个主联系人（应该自动移除第一个的主标记）
        rel2 = PartnerRelation.objects.create(
            partner=company,
            related_partner=contact2,
            is_primary=True,
        )

        rel1.refresh_from_db()
        self.assertFalse(rel1.is_primary)
        self.assertTrue(rel2.is_primary)
9.2 API 集成测试

class PartnerAPITest(APITestCase):
    def test_create_partner(self):
        """测试创建 Partner API"""
        data = {
            'name': 'New Customer',
            'partner_type': 'company',
            'is_customer': True,
            'email': 'customer@example.com',
            'customer_profile_data': {
                'credit_limit': '10000.00',
                'payment_terms': 'Net 30',
            }
        }
        response = self.client.post('/api/sea-saw-crm/partners/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['customer_profile'])

    def test_list_customers(self):
        """测试客户列表端点"""
        response = self.client.get('/api/sea-saw-crm/partners/customers/')
        self.assertEqual(response.status_code, 200)

    def test_list_suppliers(self):
        """测试供应商列表端点"""
        response = self.client.get('/api/sea-saw-crm/partners/suppliers/')
        self.assertEqual(response.status_code, 200)
9.3 端到端测试

class E2EOrderTest(TestCase):
    def test_create_order_with_partner(self):
        """端到端：创建客户 → 创建订单 → 查看订单"""
        # 1. 创建客户
        customer = Partner.objects.create(
            name="Customer A",
            partner_type='company',
            is_customer=True,
        )

        # 2. 创建联系人
        contact = Partner.objects.create(
            name="Contact Person",
            partner_type='individual',
            parent=customer,
        )

        # 3. 创建订单
        order = Order.objects.create(
            customer=customer,
            contact_person=contact,
            order_date=timezone.now().date(),
        )

        # 4. 验证
        self.assertEqual(order.customer, customer)
        self.assertEqual(order.contact_person, contact)
十、API 使用示例
10.1 创建客户

POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "ABC Company Ltd.",
  "partner_type": "company",
  "is_customer": true,
  "email": "sales@abc.com",
  "phone": "+86-10-12345678",
  "address": "123 Main St, Beijing",
  "city": "Beijing",
  "country": "China",
  "tax_id": "91110000XXXXXXXX",
  "customer_profile_data": {
    "credit_limit": "100000.00",
    "payment_terms": "Net 30",
    "payment_method": "Wire Transfer"
  }
}
10.2 创建供应商

POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "XYZ Supplier Inc.",
  "partner_type": "company",
  "is_supplier": true,
  "email": "procurement@xyz.com",
  "phone": "+1-555-1234",
  "supplier_profile_data": {
    "payment_terms": "COD",
    "currency": "USD",
    "rating": 4,
    "is_approved": true,
    "bank_name": "Bank of America",
    "bank_account": "1234567890",
    "swift_code": "BOFAUS3N"
  }
}
10.3 创建既是客户又是供应商的 Partner

POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "Dual Role Company",
  "partner_type": "company",
  "is_customer": true,
  "is_supplier": true,
  "email": "contact@dual.com",
  "customer_profile_data": {
    "credit_limit": "50000.00",
    "payment_terms": "Net 60"
  },
  "supplier_profile_data": {
    "payment_terms": "Net 30",
    "currency": "CNY",
    "is_approved": true
  }
}
10.4 创建联系人

POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "John Doe",
  "partner_type": "individual",
  "parent": 5,  # 父级 Partner ID（公司）
  "email": "john.doe@abc.com",
  "mobile": "+86-138-1234-5678",
  "is_customer": false  # 联系人通常不直接作为客户
}
10.5 为供应商添加联系人关系

POST /api/sea-saw-crm/partners/
Content-Type: application/json

{
  "name": "Supplier X",
  "partner_type": "company",
  "is_supplier": true,
  "relations_data": [
    {
      "related_partner_id": 10,  # 联系人 Partner ID
      "relation_type": "contact",
      "is_primary": true,
      "role": "Sales Manager"
    },
    {
      "related_partner_id": 11,
      "relation_type": "technical",
      "is_primary": false,
      "role": "Technical Support"
    }
  ],
  "supplier_profile_data": {
    "is_approved": true
  }
}
10.6 查询客户列表

GET /api/sea-saw-crm/partners/customers/
10.7 查询供应商列表

GET /api/sea-saw-crm/partners/suppliers/
10.8 查询联系人列表

GET /api/sea-saw-crm/partners/contacts/
10.9 复杂查询（既是客户又是供应商）

GET /api/sea-saw-crm/partners/?is_customer=true&is_supplier=true
十一、关键文件路径清单
新增文件

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/
├── models/
│   └── partner.py (Partner, PartnerRelation, CustomerProfile, SupplierProfile, CarrierProfile)
├── serializers/
│   └── partner.py (PartnerSerializer, ProfileSerializers, PartnerRelationSerializer)
├── views/
│   └── partner_view.py (PartnerViewSet)
├── permissions/
│   └── partner_permission.py (PartnerAdminPermission, PartnerSalePermission)
├── admin/
│   └── partner.py (PartnerAdmin, PartnerRelationAdmin)
└── migrations/
    └── XXXX_create_partner_models.py
修改文件

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/
├── sea_saw_crm/
│   ├── models/__init__.py (更新导出)
│   ├── serializers/__init__.py (更新导出)
│   ├── views/__init__.py (更新导出)
│   ├── permissions/__init__.py (更新导出)
│   ├── admin/__init__.py (更新导出)
│   └── urls.py (注册 PartnerViewSet)
├── sea_saw_sales/models/
│   └── order.py (company → customer, contact → contact_person)
├── sea_saw_procurement/models/
│   └── purchase_order.py (supplier → supplier:Partner)
└── sea_saw_pipeline/models/pipeline/
    └── pipeline.py (company → customer, contact → contact_person)
删除文件

/Users/coolister/Desktop/sea-saw/sea-saw-server/app/sea_saw_crm/
├── models/
│   ├── company.py (删除)
│   ├── contact.py (删除)
│   └── supplier.py (删除)
├── serializers/
│   ├── company.py (删除)
│   ├── contact.py (删除)
│   └── supplier.py (删除)
├── views/
│   ├── company_view.py (删除)
│   ├── contact_view.py (删除)
│   └── supplier_view.py (删除)
├── permissions/
│   ├── company_permission.py (删除)
│   ├── contact_permission.py (删除)
│   └── supplier_permission.py (删除)
└── admin/
    ├── company.py (删除)
    ├── contact.py (删除)
    └── supplier.py (删除)
十二、验证清单
12.1 功能验证
 Partner CRUD 操作正常
 创建客户并添加 CustomerProfile 成功
 创建供应商并添加 SupplierProfile 成功
 创建承运商并添加 CarrierProfile 成功
 创建"既是客户又是供应商"的 Partner 成功
 创建联系人（individual）并关联公司成功
 PartnerRelation 创建和管理正常
 主联系人唯一性验证正确
 Order 使用 customer/contact_person 创建成功
 PurchaseOrder 使用 supplier:Partner 创建成功
 Pipeline 同步 customer/contact_person 正常
12.2 权限验证
 Admin 可以查看所有 Partner
 Sale 只能查看自己和可见用户的 Partner
 Sale 只能修改/删除自己创建的 Partner
 权限逻辑与旧模型一致
12.3 API 验证
 /api/sea-saw-crm/partners/ 端点正常
 /api/sea-saw-crm/partners/customers/ 返回正确
 /api/sea-saw-crm/partners/suppliers/ 返回正确
 /api/sea-saw-crm/partners/carriers/ 返回正确
 /api/sea-saw-crm/partners/contacts/ 返回正确
 /api/sea-saw-crm/partners/{id}/children/ 返回正确
 查询参数过滤正常（is_customer, is_supplier 等）
 搜索功能正常
12.4 性能验证
 Partner 列表查询性能可接受（<500ms for 10000 records）
 嵌套 Profile 序列化性能可接受
 数据库索引正确创建
十三、总结与建议
推荐采用方案 B 的核心优势
统一模型 - Partner 统一客户、供应商、联系人、承运商
多重角色 - 同一 Partner 可以是客户+供应商（is_customer + is_supplier）
层级关系 - 支持公司 → 联系人、公司 → 分支机构
扩展性强 - 通过 Profile 模型扩展特定角色字段
符合业界最佳实践 - Odoo、SAP、ERPNext 都采用类似设计
简化权限 - 一套 PartnerPermission 替代三套权限类
代码复用 - 统一序列化器、ViewSet、Admin
实施时间估算
阶段	任务	工作量
阶段 1	删除旧模型	0.5 天
阶段 2	创建 Partner 模型	2-3 天
阶段 3	更新业务模型	2-3 天
阶段 4	序列化器和 ViewSet	2-3 天
阶段 5	Django Admin	1 天
阶段 6	集成测试	2-3 天
阶段 7	文档和对接	1-2 天
总计	-	11-16 天
团队配置建议：

1 名后端开发（全职）：10-15 天
或 2 名后端开发（并行）：5-8 天
关键成功因素
✅ 开发阶段，无历史数据包袱
✅ 可以直接实现最优架构
✅ 充分的单元测试和集成测试
✅ 与前端团队充分对齐
✅ 详细的 API 文档
后续优化建议
地址模型独立 - 未来可以创建 Address 模型支持多地址
标签系统 - 添加 Tag/Label 模型支持灵活分类
版本控制 - 使用 django-simple-history 追踪修改历史
全文搜索 - 使用 PostgreSQL Full-Text Search 或 Elasticsearch
图片支持 - 添加 logo/avatar 字段使用 django-storages
方案 B 是开发阶段的最佳选择，建议立即实施！

User approved the plan
完美！计划已获批准，现在开始实施。让我创建任务清单来跟踪进度：

Update Todos

删除旧 CRM 模型文件（company.py, contact.py, supplier.py）

删除旧序列化器、视图、权限、Admin 文件

创建 Partner 模型（含 PartnerRelation、Profiles）

更新 models/__init__.py 导出新模型

创建并运行 Django Migration

更新 Order 模型使用 Partner（customer, contact_person）

更新 PurchaseOrder 模型使用 Partner（supplier）

更新 Pipeline 模型使用 Partner（customer, contact_person）

创建 Partner 序列化器（含 Profile 和 Relation 序列化器）

创建 PartnerViewSet 和权限类

创建 Partner Django Admin 配置

更新 URLs 注册 Partner 路由
好的！开始实施 Partner 模型重构。我会按照计划的 7 个阶段逐步进行。

让我先从阶段 1：删除旧模型开始。

Update Todos

删除旧 CRM 模型文件（company.py, contact.py, supplier.py）

删除旧序列化器、视图、权限、Admin 文件

创建 Partner 模型（含 PartnerRelation、Profiles）

更新 models/__init__.py 导出新模型

创建并运行 Django Migration

更新 Order 模型使用 Partner（customer, contact_person）

更新 PurchaseOrder 模型使用 Partner（supplier）

更新 Pipeline 模型使用 Partner（customer, contact_person）

创建 Partner 序列化器（含 Profile 和 Relation 序列化器）

创建 PartnerViewSet 和权限类

创建 Partner Django Admin 配置

更新 URLs 注册 Partner 路由
好的！已创建任务清单，现在开始实施 Partner 模型重构。

实施进度追踪已启动（共 12 个任务）。由于这是一个较大的重构工作，我建议分步实施并测试每个阶段。

