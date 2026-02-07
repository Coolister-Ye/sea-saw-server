import re
from django.http import QueryDict


_index_re = re.compile(r"([^\[\]]+)|\[(\d+)\]")


class MultipartNestedDataMixin:
    """
    Automatically normalize multipart/form-data with nested keys
    before passing into serializer.
    """

    enable_multipart_nested = True
    multipart_nested_actions = None
    multipart_strip_fields = {"created_at", "updated_at"}

    # =========================
    # DRF REAL hook（关键）
    # =========================
    def get_serializer(self, *args, **kwargs):
        """
        This method IS called by DRF.
        """
        if self.enable_multipart_nested and "data" in kwargs:
            data = kwargs["data"]

            if isinstance(data, QueryDict):
                action = getattr(self, "action", None)

                if (
                    self.multipart_nested_actions is None
                    or action in self.multipart_nested_actions
                ):
                    parsed = self._querydict_to_dict(data)
                    kwargs["data"] = self._strip_fields(parsed)

        return super().get_serializer(*args, **kwargs)

    # =====================
    # internal helpers
    # =====================
    def _parse_key_path(self, key: str):
        parts = []
        for part in key.split("."):
            for name, index in _index_re.findall(part):
                if name:
                    parts.append(name)
                elif index:
                    parts.append(int(index))
        return parts

    def _set_deep_value(self, data, path, value):
        cur = data
        for i, p in enumerate(path):
            is_last = i == len(path) - 1

            if isinstance(p, int):
                while len(cur) <= p:
                    cur.append({})
                if is_last:
                    cur[p] = value
                else:
                    if not isinstance(cur[p], (dict, list)):
                        cur[p] = [] if isinstance(path[i + 1], int) else {}
                    cur = cur[p]
            else:
                if is_last:
                    cur[p] = value
                else:
                    if p not in cur:
                        cur[p] = [] if isinstance(path[i + 1], int) else {}
                    cur = cur[p]

    def _querydict_to_dict(self, qd: QueryDict):
        result = {}
        for key in qd.keys():
            values = qd.getlist(key)
            value = values if len(values) > 1 else values[0]

            path = self._parse_key_path(key)
            self._set_deep_value(result, path, value)
        return result

    def _strip_fields(self, data):
        if not self.multipart_strip_fields:
            return data
        if isinstance(data, dict):
            return {
                k: self._strip_fields(v)
                for k, v in data.items()
                if k not in self.multipart_strip_fields
            }
        if isinstance(data, list):
            return [self._strip_fields(v) for v in data]
        return data
