from flask import Blueprint,render_template,session,redirect,url_for
from functools import wraps
from models.models import Parkingplaces,Parkingspace

d_bp = Blueprint('dashboard',__name__,template_folder='../templates/dashboard')

def lr(f):
    @wraps(f)
    def df(*args,**kwargs):
        if 'uid' not in session:
            return redirect(url_for('auth.login'))
        return f(*args,**kwargs)
    return df



@d_bp.route('/dashboard')
@lr
def dashboard():
   if session.get("role")=='admin':
      return redirect(
         url_for('admin.summary')
        )
   else:
        return redirect(url_for("user.dashboard"))