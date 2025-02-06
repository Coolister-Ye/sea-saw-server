from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 5  # 默认每页大小
    page_size_query_param = 'page_size'  # 客户端可以通过此参数动态改变 page size
    max_page_size = 100  # 设置最大分页大小，防止用户请求过多数据