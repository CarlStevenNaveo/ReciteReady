from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator to restrict view access to specific user roles.
    If the user has a different role, redirects them to their designated dashboard
    with an error notification, strictly preventing unauthorized cross-role access.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')

            user_role = getattr(request.user, 'role', None)
            if user_role not in allowed_roles:
                messages.error(
                    request,
                    f"Access Denied: You do not have permission to view the "
                    f"{' / '.join(allowed_roles).capitalize()} portal."
                )
                if user_role == 'INSTRUCTOR':
                    return redirect('instructor_dashboard')
                elif user_role == 'STUDENT':
                    return redirect('student_dashboard')
                else:
                    raise PermissionDenied("You do not have access to this resource.")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
