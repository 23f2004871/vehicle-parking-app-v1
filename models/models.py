from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from werkzeug.security import generate_password_hash, check_password_hash

db=SQLAlchemy()

IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    return datetime.now(IST)

class User(db.Model):
    __tablename__='user'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True,nullable=False)
    password_hash=db.Column(db.String(256),nullable=False)
    full_name=db.Column(db.String(100),nullable=True)
    email=db.Column(db.String(120),unique=True,nullable=True)
    pno=db.Column(db.String(15),unique=True,nullable=True)
    add=db.Column(db.String(200),nullable=True) 
    role=db.Column(db.String(10),nullable=False,default='user')
    active=db.Column(db.Boolean,nullable=False,default=True)
    llgoin=db.Column(db.DateTime,nullable=True)
    creation=db.Column(db.DateTime,nullable=False,default=get_ist_now)
    updation=db.Column(db.DateTime,nullable=False,default=get_ist_now,onupdate=get_ist_now)
    reservations=db.relationship('Reservation',backref='user',lazy=True,cascade="all,delete-orphan")
    vehicles=db.relationship('Vehicle',backref='owner',lazy=True,cascade="all,delete-orphan")

    def set_password(self,password):
        self.password_hash=generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Parkingplaces(db.Model):
    __tablename__='parking_places' 
    id=db.Column(db.Integer,primary_key=True)
    prime_location_name=db.Column(db.String(100),nullable=False)
    price=db.Column(db.Float,nullable=False)
    address=db.Column(db.String(200),nullable=False)
    pin_code=db.Column(db.String(6),nullable=False)
    city=db.Column(db.String(50),nullable=True)
    state=db.Column(db.String(50),nullable=True)
    lat=db.Column(db.Float,nullable=True)
    lon=db.Column(db.Float,nullable=True) 
    maximum_number_of_spots=db.Column(db.Integer,nullable=False)
    opening=db.Column(db.Time,nullable=True)
    closing=db.Column(db.Time,nullable=True)
    amenities=db.Column(db.String(200),nullable=True)
    ratings=db.Column(db.Float,nullable=True,default=0.0)
    reviewno=db.Column(db.Integer,nullable=True,default=0)
    spots=db.relationship('Parkingspace',backref='lot',lazy=True,cascade="all,delete-orphan")
    reviews=db.relationship('Review',backref='lot',lazy=True,cascade="all,delete-orphan")


class Parkingspace(db.Model):
    __tablename__='parking_space'
    id=db.Column(db.Integer,primary_key=True)
    spot_number=db.Column(db.Integer,nullable=False)
    status=db.Column(db.String(10),nullable=False,default='A')
    isreserved=db.Column(db.Boolean,nullable=False,default=False)
    evsupport=db.Column(db.Boolean,nullable=False,default=False)
    spacetype=db.Column(db.String(20),nullable=False,default='standard')
    pricemulti=db.Column(db.Float,nullable=False,default=1.0)
    levels=db.Column(db.String(10),nullable=True)
    lid=db.Column(db.Integer,db.ForeignKey('parking_places.id'),nullable=False)
    reservations=db.relationship('Reservation',backref='spot',lazy=True)


class Reservation(db.Model):
    __tablename__='reservation'
    id=db.Column(db.Integer,primary_key=True)
    parking_timestamp=db.Column(db.DateTime,nullable=True)  
    leaving_timestamp=db.Column(db.DateTime,nullable=True)
    parking_cost=db.Column(db.Float,nullable=True)
    durmin=db.Column(db.Integer,nullable=True)
    vno=db.Column(db.String(20),nullable=True)
    vtype=db.Column(db.String(20),nullable=True)
    qrcode=db.Column(db.String(255),nullable=True)
    reservestatus=db.Column(db.String(20),nullable=False,default='active')
    pstatus=db.Column(db.String(20),nullable=False,default='pending')
    pmethod=db.Column(db.String(20),nullable=True)
    createat=db.Column(db.DateTime,nullable=False,default=get_ist_now)
    updateat=db.Column(db.DateTime,nullable=False,default=get_ist_now,onupdate=get_ist_now)
    uid=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    sid=db.Column(db.Integer,db.ForeignKey('parking_space.id'),nullable=False)
    vid=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=True)
    payment=db.relationship('Payment',backref='reservation',uselist=False,cascade="all,delete-orphan")

class Vehicle(db.Model):
    __tablename__='vehicle'
    id=db.Column(db.Integer,primary_key=True)
    license_plate=db.Column(db.String(20),unique=True,nullable=False)
    make=db.Column(db.String(50))
    model=db.Column(db.String(50))
    color=db.Column(db.String(30))
    uid=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

class Payment(db.Model):
    __tablename__='payment'
    id=db.Column(db.Integer,primary_key=True)
    amount=db.Column(db.Float,nullable=False)
    payment_method=db.Column(db.String(50),default="Credit Card")
    transaction_id=db.Column(db.String(100),unique=True,nullable=False)
    status=db.Column(db.String(20),nullable=False,default="Completed")
    timestamp=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    reservation_id=db.Column(db.Integer,db.ForeignKey('reservation.id'),nullable=False,unique=True)

class Review(db.Model):
    __tablename__='review'
    id=db.Column(db.Integer,primary_key=True)
    rating=db.Column(db.Integer,nullable=False)
    comment=db.Column(db.Text,nullable=True)
    timestamp=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    lid=db.Column(db.Integer,db.ForeignKey('parking_places.id'),nullable=False)
    uid=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    user = db.relationship('User', backref='user_reviews')
