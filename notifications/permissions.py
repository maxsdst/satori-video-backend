from rest_framework.permissions import SAFE_METHODS, BasePermission


class UserOwnsObjectOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        if not user or not user.is_authenticated:
            return False

        return obj.profile.id == user.profile.id
