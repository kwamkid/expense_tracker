# app/middleware/org_required.py
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def org_required(view_func):
    """
    Middleware ที่ตรวจสอบว่าผู้ใช้มีการเลือกองค์กรที่ใช้งานอยู่หรือไม่
    ถ้าไม่มี จะเด้งไปที่หน้าเลือกองค์กร
    """

    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        # ถ้าผู้ใช้ไม่ได้เลือกองค์กรที่ใช้งานอยู่
        if not current_user.active_organization_id:
            # ถ้าผู้ใช้มีองค์กรอยู่แล้ว
            if current_user.organizations:
                flash('กรุณาเลือกองค์กรที่ต้องการใช้งาน', 'warning')
                return redirect(url_for('organization.index'))

            # ถ้าผู้ใช้ยังไม่มีองค์กร
            flash('กรุณาสร้างองค์กรใหม่เพื่อใช้งานระบบ', 'warning')
            return redirect(url_for('organization.create'))

        return view_func(*args, **kwargs)

    return decorated_view


def admin_required(view_func):
    """
    Middleware ที่ตรวจสอบว่าผู้ใช้เป็นแอดมินขององค์กรที่กำลังใช้งานอยู่หรือไม่
    ถ้าไม่ใช่ จะเด้งไปที่หน้า Dashboard พร้อมกับข้อความแจ้งเตือน
    """

    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        # ต้องมีการเลือกองค์กรก่อน
        if not current_user.active_organization_id:
            if current_user.organizations:
                flash('กรุณาเลือกองค์กรที่ต้องการใช้งาน', 'warning')
                return redirect(url_for('organization.index'))
            else:
                flash('กรุณาสร้างองค์กรใหม่เพื่อใช้งานระบบ', 'warning')
                return redirect(url_for('organization.create'))

        # ตรวจสอบว่าเป็นแอดมินหรือไม่
        org = current_user.get_active_organization()
        if not org or not org.user_has_role(current_user.id, 'admin'):
            flash('คุณไม่มีสิทธิ์ในการเข้าถึงหน้านี้ ต้องเป็นแอดมินเท่านั้น', 'danger')
            return redirect(url_for('dashboard.index'))

        return view_func(*args, **kwargs)

    return decorated_view


def member_required(view_func):
    """
    Middleware ที่ตรวจสอบว่าผู้ใช้เป็นสมาชิกหรือแอดมินขององค์กรที่กำลังใช้งานอยู่หรือไม่
    ถ้าไม่ใช่ จะเด้งไปที่หน้า Dashboard พร้อมกับข้อความแจ้งเตือน
    """

    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        # ต้องมีการเลือกองค์กรก่อน
        if not current_user.active_organization_id:
            if current_user.organizations:
                flash('กรุณาเลือกองค์กรที่ต้องการใช้งาน', 'warning')
                return redirect(url_for('organization.index'))
            else:
                flash('กรุณาสร้างองค์กรใหม่เพื่อใช้งานระบบ', 'warning')
                return redirect(url_for('organization.create'))

        # ตรวจสอบว่าเป็นสมาชิกหรือแอดมินหรือไม่
        org = current_user.get_active_organization()
        if not org or not org.user_has_role(current_user.id, ['admin', 'member']):
            flash('คุณไม่มีสิทธิ์ในการเข้าถึงหน้านี้ ต้องเป็นสมาชิกหรือแอดมินเท่านั้น', 'danger')
            return redirect(url_for('dashboard.index'))

        return view_func(*args, **kwargs)

    return decorated_view