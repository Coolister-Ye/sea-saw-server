from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 5  # 默认每页大小
    page_size_query_param = 'page_size'  # 客户端可以通过此参数动态改变 page size
    max_page_size = 100  # 设置最大分页大小，防止用户请求过多数据

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1

        # Clamp to last valid page instead of returning 404
        num_pages = max(paginator.num_pages, 1)
        if page_number > num_pages:
            page_number = num_pages

        try:
            self.page = paginator.page(page_number)
        except Exception:
            self.page = paginator.page(1)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        self.request = request
        return list(self.page)
