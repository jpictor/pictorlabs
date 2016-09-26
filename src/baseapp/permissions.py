from rest_framework import permissions


class InternalOrIsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.META.get('HTTP_IS_INTERNAL') == '1':
            return True
        return request.user and request.user.is_authenticated()

