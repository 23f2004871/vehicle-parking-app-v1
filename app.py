import os
from flask import Flask
from models.models import db, User 

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'v_database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '4309aa486f863abc079e644230b00fc6' 

db.init_app(app)

def create_admin():
    if not User.query.filter_by(role='superuser').first():
        print("Admin user not found, creating one...")
        super_user = User(
            username='superuser@vparking.com',
            full_name='Super User',
            role='superuser'
        )
        super_user.set_password('superuser@vehicle')
        db.session.add(super_user)
        db.session.commit()
        print("Admin user created")
    else:
        print("Admin user already exists")

with app.app_context():
    print("Creating database")
    db.create_all() 
    print("Database created")
    create_admin()

@app.route('/')
def index():
    return "<h1>Vehicle Parking App V1</h1>"

if __name__ == '__main__':
    app.run(debug=True)


