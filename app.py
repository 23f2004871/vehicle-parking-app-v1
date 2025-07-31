import os
from flask import Flask,url_for,render_template
from flask_mail import Mail,Message
from threading import Thread
from models.models import db,User

from controllers.auth_routes import a_bp
from controllers.admin_routes import a_bp as admin_a_bp
from controllers.user_routes import u_bp
from controllers.dashboard_routes import d_bp
from controllers.api_routes import a_bp as api_a_bp

app=Flask(__name__)
basedir=os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY']='your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///' + os.path.join(basedir,'parking.db')
app.config[ 'SQLALCHEMY_TRACK_MODIFICATIONS' ]= False

app.config['MAIL_SERVER']=os.environ.get('MAIL_SERVER','smtp.gmail.com')
app.config['MAIL_PORT']=int(os.environ.get('MAIL_PORT',465))
app.config['MAIL_USE_SSL'] =True
app.config[ 'MAIL_USERNAME' ] =os.environ.get('MAIL_USERNAME','your-email@gmail.com')
app.config['MAIL_PASSWORD']=os.environ.get('MAIL_PASSWORD','your-app-password')
app.config[ 'MAIL_DEFAULT_SENDER' ]=('V-Parking App',os.environ.get('MAIL_USERNAME','your-email@gmail.com'))

mail=Mail(app)

def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)

def send_email( to,subject,template ):
    msg=Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    Thread(target=send_async_email,args=(app,msg)).start()

db.init_app(app)

app.register_blueprint(a_bp)
app.register_blueprint(admin_a_bp,url_prefix='/admin')

app.register_blueprint(u_bp,url_prefix='/user')
app.register_blueprint(d_bp)
app.register_blueprint(api_a_bp,url_prefix='/api')

def create_admin( ):
    if not User.query.filter_by(role='admin').first():
        print("Admin user not found,creating one...")
        admin_user=User(
            username='admin@vparking.com',
            full_name='Admin User',
            role='admin'
        )
        admin_user.set_password('admin@vehicle')
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully with username 'admin@vparking.com' and password 'admin@vehicle'.")
    else:
        print("Admin user already exists.")

with app.app_context():
    print("Creating database tables.....")
    db.create_all() 
    print("Database tables created.")
    create_admin()


@app.route('/')
def index( ):
    return render_template('index.html')


if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)