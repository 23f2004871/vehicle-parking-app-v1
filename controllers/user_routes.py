
from flask import Blueprint,render_template,request,flash,redirect,url_for,session,jsonify
from functools import wraps
from datetime import datetime
import pytz

IST=pytz.timezone('Asia/Kolkata')

def get_ist_now( ):
    return datetime.now(IST)

from models.models import db,Parkingplaces,Parkingspace,Reservation,User,Vehicle,Review,Payment
from sqlalchemy import func,or_
import qrcode
import os
import uuid
from math import radians,cos,sin,asin,sqrt

u_bp=Blueprint('user',__name__,template_folder='../templates/user')

def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if 'uid' not in session:
            flash('Please log in to access this page.','warning')
            return redirect(url_for('auth.login'))
        return f(*args,**kwargs)
    return decorated_function


@u_bp.route('/dashboard')
@login_required
def dashboard():
    q=request.args.get('q')
    on=request.args.get('open_now',type=bool)
    s=request.args.get('sort_by','name')

    qry=Parkingplaces.query

    if q:
        t=f"%{q}%"
        qry=qry.filter(or_(
            Parkingplaces.prime_location_name.ilike(t),
            Parkingplaces.address.ilike(t),
            Parkingplaces.pin_code.ilike(t)
        ))

    if on:
        n=datetime.now().time()
        qry=qry.filter(
            (Parkingplaces.opening <= n) & 
            (Parkingplaces.closing >= n)
        )

    if s=='price':
        qry=qry.order_by(Parkingplaces.price)
    elif s=='rating':
        qry=qry.order_by(Parkingplaces.ratings.desc())
    else:
        qry=qry.order_by(Parkingplaces.prime_location_name)

    l=qry.all()
    
    av=[]
    md=[]
    
    for lt in l:
        as_={
            'standard':Parkingspace.query.filter_by(lid=lt.id,status='A',isreserved=False,spacetype='standard',evsupport=False).count(),
            'premium':Parkingspace.query.filter_by(lid=lt.id,status='A',isreserved=False,spacetype='premium',evsupport=False).count(),
            'ev':Parkingspace.query.filter_by(lid=lt.id,status='A',isreserved=False,evsupport=True).count()
        }
        
        ts=as_['standard'] + as_['premium'] + as_['ev']
        
        av.append({'lot':lt,'available_spots':as_})
        
        md.append({
            'id':lt.id,'name':lt.prime_location_name,
            'address':lt.address,'price':float(lt.price) if lt.price else 0,
            'lat':float(lt.lat) if lt.lat else None,
            'lon':float(lt.lon) if lt.lon else None,'available_spots':ts
        })

    c=Vehicle.query.filter_by(uid=session['uid']).all()
    
    return render_template('user/user_dashboard.html',
                         av=av,
                         md=md,
                           cars=c,
                         q=q,
                         open_now=on,
                         sort=s)


@u_bp.route('/my_parkings')
@login_required
def my_parkings():
    r = Reservation.query.filter_by(uid=session['uid']).order_by(Reservation.createat.desc()).all()
    
    total_spent = sum([res.parking_cost for res in r if res.parking_cost]) or 0
    total_reservations = len(r)
    completed_reservations = len([res for res in r if res.reservestatus == "completed"])
    
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    monthly_data = defaultdict(float)
    monthly_counts = defaultdict(int)
    
    today = datetime.now()
    
    # Collect data by actual month-year
    for res in r:
        if res.createat and res.parking_cost:
            month_key = res.createat.strftime('%Y-%m')  # Use YYYY-MM format for proper grouping
            monthly_data[month_key] += float(res.parking_cost)
            monthly_counts[month_key] += 1
    
    months, spending, counts = [], [], []
    
    # Generate last 6 months properly
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_date = month_date.replace(day=1)  # Ensure we're at the start of month
        
        month_key = month_date.strftime('%Y-%m')
        month_label = month_date.strftime('%b')
        
        months.append(month_label)
        spending.append(monthly_data.get(month_key, 0))
        counts.append(monthly_counts.get(month_key, 0))
    
    chart_data = {
        'months': months,
        'spending': spending,
        'counts': counts
    }
    
    return render_template('user/my_parkings.html',
                           reservations=r,
                           total_spent=total_spent,
                           total_reservations=total_reservations,
                           completed_reservations=completed_reservations,
                           chart_data=chart_data)

@u_bp.route('/my_vehicles')
@login_required
def my_vehicles():
    v=Vehicle.query.filter_by(uid=session['uid']).all()
    return render_template('user/my_vehicles.html',vehicles=v)

@u_bp.route('/add_vehicle',methods=['POST'])
@login_required
def add_vehicle():
    lp=request.form.get('license_plate','').strip().upper()
    m=request.form.get('make','').strip()
    md=request.form.get('model','').strip()
    cl=request.form.get('color','').strip()
    
    if not all([lp,m,md,cl]):
        flash('All vehicle details are required.','danger')
        return redirect(url_for('user.my_vehicles'))
    
    ev=Vehicle.query.filter_by(license_plate=lp).first()
    if ev:
        flash('A vehicle with this license plate is already registered.','warning')
        return redirect(url_for('user.my_vehicles'))
    
    try:
        nv=Vehicle(license_plate=lp,make=m,model=md,color=cl,uid=session['uid'])
        db.session.add(nv)
        db.session.commit()
        flash('Vehicle added successfully!','success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding vehicle:{e}','danger')
    
    return redirect(url_for('user.my_vehicles'))

@u_bp.route('/delete_vehicle/<int:vid>',methods=['POST'])
@login_required
def delete_vehicle(vid):
    v=Vehicle.query.get_or_404(vid)
    
    if v.uid!=session['uid']:
        flash('You can only delete your own vehicles.','danger')
        return redirect(url_for('user.my_vehicles'))
    
    ar=Reservation.query.filter_by(uid=session['uid'],vno=v.license_plate,reservestatus='active').first()
    
    if ar:
        flash('Cannot delete vehicle. It has active parking reservations.','warning')
        return redirect(url_for('user.my_vehicles'))
    
    try:
        db.session.delete(v)
        db.session.commit()
        flash('Vehicle deleted successfully!','success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting vehicle:{e}','danger')
    
    return redirect(url_for('user.my_vehicles'))


@u_bp.route('/lot/<int:lot_id>')
@login_required
def lot_details(lid):
    l=Parkingplaces.query.get_or_404(lid)
    uv=Vehicle.query.filter_by(uid=session['uid']).all()
    
    as_={
        "standard":Parkingspace.query.filter_by(lid=lid,status='A',isreserved=False,spacetype='standard',evsupport=False).count(),
        "premium":Parkingspace.query.filter_by(lid=lid,status='A',isreserved=False,spacetype='premium',evsupport=False).count(),
        "ev":Parkingspace.query.filter_by(lid=lid,status='A',isreserved=False,evsupport=True).count()
    }
    
    return render_template('user/lot_details.html',lot=l,user_vehicles=uv,available_spots=as_)


@u_bp.route('/book_spot/<int:lid>',methods=['POST'])
@login_required
def book_spot_simple(lid):
    vehicle_id=request.form.get('vehicle_id')
    spot_type=request.form.get('spot_type')
    
    if not vehicle_id or not spot_type:
        flash('Please select a vehicle and spot type.','warning')
        return redirect(url_for('user.dashboard'))
    
    v=Vehicle.query.filter_by(id=vehicle_id,uid=session['uid']).first_or_404()
    l=Parkingplaces.query.get_or_404(lid)
    
    es=spot_type=='ev'
    spt='premium' if spot_type=='premium' else 'standard'
    
    as_=Parkingspace.query.filter_by(
        lid=lid,status='A',isreserved=False,
        spacetype=spt,evsupport=es
    ).first()
    
    if not as_:
        flash(f'No {spot_type} spots available at this location.','warning')
        return redirect(url_for('user.dashboard'))
    
    try:
        r=Reservation(
            uid=session['uid'],
            sid=as_.id,
            vno=v.license_plate,
            reservestatus='active'
        )
        
        as_.status,as_.isreserved='R',True
        
        db.session.add(r)
        db.session.flush()
        
        qr_data=f"RESERVATION:{r.id}:{session['uid']}:{as_.spot_number}"
        qr=qrcode.QRCode(version=1,box_size=10,border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img=qr.make_image(fill_color="black",back_color="white")
        
        qr_filename=f"qr_{r.id}_{uuid.uuid4().hex[:8]}.png"
        qr_path=os.path.join('static','qrcodes',qr_filename)
        
        os.makedirs(os.path.dirname(qr_path),exist_ok=True)
        qr_img.save(qr_path)
        
        r.qrcode=f"qrcodes/{qr_filename}"
        db.session.commit()
        
        flash(f'Parking spot #{as_.spot_number} booked successfully!','success')
        return redirect(url_for('user.my_parkings'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error booking spot:{e}','danger')
        return redirect(url_for('user.dashboard'))

@u_bp.route('/check_in/<int:rid>',methods=['POST'])
@login_required
def check_in(rid):
    r=Reservation.query.get_or_404(rid)
    
    if r.uid!=session['uid'] or r.reservestatus!='active':
        flash('Invalid reservation.','danger')
        return redirect(url_for('user.my_parkings'))
    
    try:
        r.parking_timestamp=get_ist_now()
        db.session.commit()
        flash('Checked in successfully!','success')
    except Exception as e:
        db.session.rollback()
        flash(f'Check-in failed:{e}','danger')
    
    return redirect(url_for('user.my_parkings'))


@u_bp.route('/check_out/<int:rid>',methods=['POST'])
@login_required
def check_out(rid):
    r=Reservation.query.get_or_404(rid)
    
    try:
        r.leaving_timestamp=get_ist_now()
        
        if r.parking_timestamp.tzinfo is None:
            parking_time=IST.localize(r.parking_timestamp)
        else:
            parking_time=r.parking_timestamp
            
        ds=(r.leaving_timestamp - parking_time).total_seconds()
        dh=ds/3600
        r.durmin=int(ds/60)
        
        bp=r.spot.lot.price
        sm=r.spot.pricemulti
        c=(int(dh)+ 1)*bp* sm
        r.parking_cost=c
        
        r.reservestatus='completed'
        r.spot.status='A'
        r.spot.isreserved=False
        
        db.session.commit()
        flash(f'Spot released successfully! Total cost:₹{c:.2f}','success')

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred:{e}','danger')

    return redirect(url_for('user.my_parkings'))

@u_bp.route('/cancel/<int:rid>',methods=['POST'])
@login_required
def cancel_reservation(rid):
    r=Reservation.query.get_or_404(rid)
    
    if r.uid!=session['uid'] or r.reservestatus!='active':
        flash('This reservation cannot be cancelled.','danger')
        return redirect(url_for('user.my_parkings'))
        
    try:
        r.reservestatus='cancelled'
        r.spot.status='A'
        r.spot.isreserved=False
        
        db.session.commit()
        flash('Your reservation has been cancelled.','success')

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred:{e}','danger')
        
    return redirect(url_for('user.my_parkings'))


@u_bp.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    u=User.query.get_or_404(session['uid'])
    nu=request.args.get('next')

    if request.method=='POST':
        nu=request.form.get('next_url')
        
        if 'update_details' in request.form:
            u.full_name=request.form.get('full_name')
            u.pno=request.form.get('pno')
            u.add=request.form.get('add')
            db.session.commit()
            flash('Your details have been updated successfully!','success')
            
            if nu:
                return redirect(nu)
                
        elif 'change_password' in request.form:
            cp,np,cnp=request.form.get('current_password'),request.form.get('new_password'),request.form.get('confirm_password')
            
            if not u.check_password(cp):
                flash('Current password is incorrect.','danger')
            elif np!=cnp:
                flash('New passwords do not match.','danger')
            elif len(np) < 6:
                flash('Password must be at least 6 characters long.','danger')
            else:
                u.set_password(np)
                db.session.commit()
                flash('Password changed successfully!','success')
                
                if nu:
                    return redirect(nu)

    return render_template('user/profile.html',user=u,next_url=nu)


@u_bp.route('/reservation/<int:rid>')
@login_required
def reservation_details(rid):
    r=Reservation.query.get_or_404(rid)
    
    if r.uid!=session['uid']:
        flash('You can only view your own reservations.','danger')
        return redirect(url_for('user.my_parkings'))
    
    return render_template('user/reservation_details.html',r=r)


@u_bp.route('/pay_for_reservation/<int:reservation_id>',methods=['GET','POST'])
@login_required
def pay_for_reservation(reservation_id):
    r=Reservation.query.get_or_404(reservation_id)
    
    if r.uid!=session['uid']:
        flash('You can only pay for your own reservations.','danger')
        return redirect(url_for('user.my_parkings'))
    
    if r.pstatus=='paid':
        flash('This reservation has already been paid.','info')
        return redirect(url_for('user.my_parkings'))
    
    if request.method=='POST':
        try:
            import uuid
            transaction_id=str(uuid.uuid4())
            
            payment=Payment(
                reservation_id=r.id,amount=r.parking_cost,
                payment_method='Credit Card',transaction_id=transaction_id,
                status='Completed'
            )
            
            r.pstatus,r.pmethod='paid','card'
            
            db.session.add(payment)
            db.session.commit()
            
            flash(' Payment successful!','success')
            return redirect(url_for('user.my_parkings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Payment failed:{e}','danger')
    
    return render_template('user/payment.html',r=r)

@u_bp.route('/receipt/<int:reservation_id>')
@login_required
def receipt(reservation_id):
    r=Reservation.query.get_or_404(reservation_id)
    
    if r.uid!= session['uid']:
        flash('You can only view your own receipts.','danger')
        return redirect(url_for('user.my_parkings'))
    
    p=Payment.query.filter_by(reservation_id= r.id).first()
    
    return render_template('user/receipt.html',r=r,p =p)

@u_bp.route('/submit_review/<int:reservation_id>',methods=['POST'])
@login_required
def submit_review(reservation_id):
    r=Reservation.query.get_or_404(reservation_id)
    
    if r.uid!=session['uid']:
        flash('You can only review your own reservations.','danger')
        return redirect(url_for('user.my_parkings'))
    
    rating=request.form.get('rating',type=int)
    comment=request.form.get('comment','').strip()
    
    try:
        review=Review(
            uid=session['uid'],lid=r.spot.lot.id,
            rating=rating,comment=comment
        )
        
        db.session.add(review)
        db.session.flush()
        
        lot=r.spot.lot
        all_reviews=Review.query.filter_by(lid=lot.id).all()
        
        if all_reviews:
            avg_rating=sum(rev.rating for rev in all_reviews) / len(all_reviews)
            lot.ratings=round(avg_rating,1)
            lot.reviewno=len(all_reviews)
        
        db.session.commit()
        
        flash('Review submitted successfully!','success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting review:{e}','danger')
    
    return redirect(url_for('user.my_parkings'))
