<<<<<<< HEAD
from django.core.exceptions import PermissionDenied
=======
>>>>>>> b8ed2530b8fff5b07d0c432a841b3ffb83230787
from django.http import Http404
from rest_framework import exceptions
from rest_framework.metadata import SimpleMetadata
from rest_framework.request import clone_request
<<<<<<< HEAD
=======
from django.core.exceptions import PermissionDenied
>>>>>>> b8ed2530b8fff5b07d0c432a841b3ffb83230787


class CustomMetadata(SimpleMetadata):
    def determine_actions(self, request, view):
        """
        For generic class based views we return information about
        the fields that are accepted for 'PUT' and 'POST' methods.
        """
        actions = {}
        for method in {'PUT', 'POST', 'OPTIONS'} & set(view.allowed_methods):
            view.request = clone_request(request, method)
            try:
                # Test global permissions
                if hasattr(view, 'check_permissions'):
                    view.check_permissions(view.request)
                # Test object permissions
                if method == 'PUT' and hasattr(view, 'get_object'):
                    view.get_object()
            except (exceptions.APIException, PermissionDenied, Http404):
                pass
            else:
                # If user has appropriate permissions for the view, include
                # appropriate metadata about the fields that should be supplied.
                serializer = view.get_serializer()
                actions[method] = self.get_serializer_info(serializer)
            finally:
                view.request = request

<<<<<<< HEAD
        return actions
=======
        return actions
>>>>>>> b8ed2530b8fff5b07d0c432a841b3ffb83230787
