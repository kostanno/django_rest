from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsOwnerOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


class IsAdminUser(BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsModerator(BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name='Модераторы').exists()
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwnerOrAdmin(BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj == request.user or (request.user and request.user.is_staff)