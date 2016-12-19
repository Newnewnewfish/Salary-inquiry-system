from functools import wraps
from flask import abort
from flask.ext.login import current_user
from .models import Permission


def permission_required(permission):
    '''用户权限检查'''
	def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
	'''管理员权限检查'''
    return permission_required(Permission.ADMINISTER)(f)

def hr_required(f):
	'''HR帐号权限检查'''
	return permission_required(Permission.INPUT)(f)