from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'Owner' or request.user.is_superuser


class IsUserOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'User' or request.user.is_superuser