from rest_framework.request import clone_request

from .base_metadata import BaseMetadata
from ..services import OrderStateService


class OrderMetadata(BaseMetadata):
    """
    Metadata with State Machine Actions
    - injects state_actions
    - depends on view.state_service
    """

    def determine_metadata(self, request, view):
        metadata = super().determine_metadata(request, view)
        metadata["state_actions"] = self.get_state_actions(request, view)
        return metadata

    def get_state_actions(self, request, view):
        if not hasattr(view, "get_object"):
            return {}

        try:
            obj = view.get_object()
        except Exception:
            return {}

        allowed_actions = OrderStateService.get_allowed_actions(obj, request.user)
        return allowed_actions
