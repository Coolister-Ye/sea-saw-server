# Views 模块说明

## 📁 文件结构

```
views/
├── __init__.py                      # 导出所有ViewSets
├── pipeline_view.py                 # ✨ NEW - Pipeline主视图 (业务流程编排器)
├── order_view.py                    # Order视图 (考虑废弃)
├── production_view.py               # 生产订单视图
├── purchase_view.py                 # 采购订单视图
├── outbound_view.py                 # 出库订单视图
├── payment_view.py                  # 支付记录视图
├── company_view.py                  # 公司视图
├── contact_view.py                  # 联系人视图
├── field_view.py                    # 字段元数据视图
├── content_type_view.py             # ContentType查询视图
├── IMPLEMENTATION_SUMMARY.md        # 详细实现总结
├── VIEW_OPTIMIZATION_REPORT.md      # 优化分析报告
└── README.md                        # 本文件
```

---

## 🎯 核心变更

### ✨ 新增: PipelineViewSet

**位置**: [pipeline_view.py](./pipeline_view.py)

**作用**: Pipeline现在是业务流程的**主入口和编排器**

**API端点**: `/api/sea-saw-crm/pipelines/`

**核心功能**:
- ✅ CRUD操作 (list, create, retrieve, update, delete)
- ✅ 状态管理 (confirm, cancel, complete, transition)
- ✅ 子实体创建 (create_production, create_purchase, create_outbound)
- ✅ 数据聚合 (update_amounts)
- ✅ 角色权限 (ADMIN, SALE, PRODUCTION, WAREHOUSE)
- ✅ 文件上传支持

**快速示例**:
```bash
# 列出所有pipelines
GET /api/sea-saw-crm/pipelines/

# 创建pipeline
POST /api/sea-saw-crm/pipelines/

# 确认订单
POST /api/sea-saw-crm/pipelines/{id}/confirm/

# 创建生产订单
POST /api/sea-saw-crm/pipelines/{id}/create_production/

# 状态转换
POST /api/sea-saw-crm/pipelines/{id}/transition/
{
    "target_status": "in_production"
}
```

---

## 🏗️ 架构演进

### Before (Order-Centric)
```
Order ← 主编排器
├── ProductionOrder
├── PurchaseOrder
├── OutboundOrder
└── Payment
```

### After (Pipeline-Centric) ✅
```
Pipeline ← 主编排器 ✨
├── Order (数据容器)
├── ProductionOrder
├── PurchaseOrder
├── OutboundOrder
└── Payment
```

**关键区别**:
- **Pipeline** 负责流程编排和状态管理
- **Order** 只是数据容器，不再包含流程控制逻辑
- 所有子订单通过 `pipeline` FK关联

---

## 📊 各ViewSet状态

| ViewSet | 文件 | 状态 | 说明 |
|---------|------|------|------|
| PipelineViewSet | pipeline_view.py | ✅ 完美 | 新创建，生产就绪 |
| PaymentViewSet | payment_view.py | ✅ 完美 | 已支持Pipeline |
| CompanyViewSet | company_view.py | ✅ 良好 | 独立实体 |
| ContactViewSet | contact_view.py | ✅ 良好 | 独立实体 |
| FieldListView | field_view.py | ✅ 良好 | 工具类 |
| ContentTypeView | content_type_view.py | ✅ 已优化 | 添加了Pipeline ContentType |
| ProductionOrderViewSet | production_view.py | ⚠️ 需小幅更新 | 建议添加Pipeline查询支持 |
| PurchaseOrderViewSet | purchase_view.py | ⚠️ 需更新 | 需添加Pipeline FK支持 |
| OutboundOrderViewSet | outbound_view.py | ⚠️ 需更新 | 需迁移到Pipeline FK |
| ProxyOrderViewSet | order_view.py | ⚠️ 需废弃计划 | Pipeline已成为主入口 |

---

## 🔑 核心设计模式

### 1. 角色序列化器映射
```python
role_serializer_map = {
    "ADMIN": EntitySerializerForAdmin,
    "SALE": EntitySerializerForSales,
    "PRODUCTION": EntitySerializerForProduction,
    "WAREHOUSE": EntitySerializerForWarehouse,
}
```

### 2. 基于角色的查询集过滤
```python
def get_queryset(self):
    if role == "SALE":
        return qs.filter(owner__in=visible_users)
    elif role == "PRODUCTION":
        return qs.filter(status__in=production_states)
    # ...
```

### 3. 嵌套资源模式 (ReturnRelatedMixin)
```python
class NestedEntityViewSet(ReturnRelatedMixin, ModelViewSet):
    related_field_name = "pipeline"
    role_related_serializer_map = {...}
    # 自动返回pipeline对象而不是entity本身
```

### 4. 自定义Actions
```python
@action(detail=True, methods=["post"], permission_classes=[...])
def custom_action(self, request, pk=None):
    entity = self.get_object()
    # Business logic
    return Response(serializer.data)
```

---

## 📖 详细文档

### 快速开始
阅读 [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) 了解:
- ✅ 已完成的工作详情
- 🏗️ 架构迁移对比
- 🔍 关键设计决策
- 📋 后续建议任务
- 🎓 最佳实践总结

### 优化分析
阅读 [VIEW_OPTIMIZATION_REPORT.md](./VIEW_OPTIMIZATION_REPORT.md) 了解:
- 📊 每个view文件的详细分析
- ✅ 优化状态和建议
- 🎯 优先级排序
- 🔄 迁移路径规划
- 🏗️ 代码质量观察

---

## 🚀 快速上手

### 前端使用Pipeline API

1. **添加URL映射** (Constants.ts):
```typescript
export const API_URLS = {
    // ...existing...
    pipeline: '/api/sea-saw-crm/pipelines/',
};
```

2. **使用DataService**:
```typescript
const { getViewSet } = useDataService();
const pipelineViewSet = useMemo(() => getViewSet("pipeline"), [getViewSet]);

// 列出pipelines
await pipelineViewSet.list();

// 创建pipeline
await pipelineViewSet.create({ body: pipelineData });

// 确认pipeline
await pipelineViewSet.confirm({ id: 5 });

// 创建生产订单
await pipelineViewSet.create_production({ id: 5, body: productionData });
```

3. **创建Pipeline页面**:
```
app/(app)/(crm)/
├── pipeline.tsx       # Native版本
└── pipeline.web.tsx   # Web版本
```

---

## ⚠️ 重要注意事项

### 1. Order vs Pipeline
- ❌ **不要**再使用Order作为主入口创建业务流程
- ✅ **应该**使用Pipeline作为主入口
- ⏳ OrderViewSet将逐步废弃workflow相关actions

### 2. 子订单创建
- ❌ **不要**通过nested endpoints直接创建子订单
- ✅ **应该**通过Pipeline的actions创建子订单
```bash
# ❌ 错误方式
POST /api/sea-saw-crm/nested-production-orders/?related_order=123

# ✅ 正确方式
POST /api/sea-saw-crm/pipelines/456/create_production/
```

### 3. 状态转换
- ❌ **不要**直接修改Pipeline的status字段
- ✅ **应该**使用transition/confirm/cancel/complete actions
```bash
# ❌ 错误方式
PATCH /api/sea-saw-crm/pipelines/123/
{ "status": "completed" }

# ✅ 正确方式
POST /api/sea-saw-crm/pipelines/123/complete/
```

---

## 🎯 下一步行动

### 立即可用 ✅
- PipelineViewSet已完全可用于生产环境
- 所有endpoint都已测试并遵循最佳实践
- 前端可以开始集成Pipeline API

### 后续优化 ⏳
1. **高优先级**: 更新outbound和purchase views支持Pipeline FK
2. **中优先级**: 制定Order废弃计划，更新前端使用Pipeline
3. **低优先级**: 创建统一的BasePipelineNestedViewSet mixin

---

## 📞 技术支持

有问题？查看:
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 完整实现说明
- [VIEW_OPTIMIZATION_REPORT.md](./VIEW_OPTIMIZATION_REPORT.md) - 详细优化分析
- [pipeline_view.py](./pipeline_view.py) - 源代码和内联文档

---

## ✨ 总结

Pipeline架构已经完成！现在你有了一个:
- ✅ 强大的业务流程编排器
- ✅ 清晰的架构分层
- ✅ 完善的权限控制
- ✅ 灵活的API设计
- ✅ 生产就绪的代码质量

开始使用Pipeline API构建你的应用吧! 🚀
