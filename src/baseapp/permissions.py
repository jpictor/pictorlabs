from rest_framework import permissions


class InternalOrIsAuthenticated(permissions.BasePermission):
    """
    Permissions class which allows internal services to use the API without authorization.
    Access using NGINX proxy.
    The HTTP_IS_INTERNAL header should be added by NGINX internal proxy.
    The header should be set to 0 with no forwarding for the Internet-facing proxy.
    """
    def has_permission(self, request, view):
        if request.META.get('HTTP_IS_INTERNAL') == '1':
            return True
        return request.user and request.user.is_authenticated()

