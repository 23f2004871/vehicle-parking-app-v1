from flask import Blueprint,render_template,request,flash,redirect,url_for,session
from models.models import db,User
from datetime import datetime

a_bp=Blueprint('auth',__name__,template_folder='../templates/auth')

@a_bp.route('/register',methods=['GET','POST'])
def register():
  if request.method=='POST':
    u=request.form.get('username')
    p=request.form.get('password')
    fn=request.form.get('full_name')
    ph=request.form.get('phone')
    if User.query.filter_by(username=u).first():
      flash('Username already exists. Please choose a different one.',"danger")
    elif len(p) < 6:
      flash("Password must be at least 6 characters long.",'danger')
    else:
      nu=User(
          username=u,
        full_name=fn,
          pno=ph,
              email=u,
        role='user'
      )
      nu.set_password(p)
      db.session.add(nu)
      db.session.commit()
      try:
        from app import send_email
        hb=f"""
        <h1>Welcome to V-Parking,{nu.full_name}!</h1>
        <p>Thank you for registering with our parking management system.</p>
        <p>You can now log in and start booking parking spots.</p>
        """
        send_email(nu.username,"Welcome to V-Parking!",hb)
      except Exception as e:
        print(f"Email sending failed: {e}")
      flash('Registration successful! Please log in.','success')
      return redirect( url_for('auth.login') )
  return render_template('register.html')

@a_bp.route('/login',methods=['GET','POST'])
def login():
   if request.method=='POST':
      u=request.form.get('username')
      p=request.form.get('password')
      
      usr=User.query.filter_by(username=u).first()
      
      if usr and usr.check_password( p ):
         if not usr.active:
            flash('Your account has been deactivated...','danger')
            return redirect(url_for('auth.login'))
         
         session['uid']=usr.id
         
         session["role"]=usr.role
         session['username']=usr.username
         
         usr.llgoin=datetime.utcnow()
         db.session.commit()
         
         flash('Logged in successfully!',"success")
         
         if usr.role=='admin':
            return redirect(url_for('admin.summary'))
         else:
            return redirect(url_for("user.dashboard"))
      else:
         flash('Invalid username or password.','danger')
   
   return render_template('login.html')




@a_bp.route('/logout')
def logout():
     session.pop('uid',None)
     session.pop("username",None)
     session.pop('role',None)
     flash('You have been logged out.','info')
     return redirect(url_for('auth.login'))