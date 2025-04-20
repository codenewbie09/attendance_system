from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from functools import wraps


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.user_type == role:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You don't have permission to access this page.")
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required('admin')(view_func)


def teacher_required(view_func):
    return role_required('teacher')(view_func)


def student_required(view_func):
    return role_required('student')(view_func)
