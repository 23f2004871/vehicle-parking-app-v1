from flask import Blueprint,render_template,request,flash,redirect,url_for,session,make_response
from functools import wraps
import io
import csv
from datetime import datetime,timedelta
from models.models import db,Parkingplaces,Parkingspace,Reservation,User,Vehicle,Review,Payment
import pytz
from sqlalchemy import func


IST=pytz.timezone('Asia/Kolkata')

def get_ist_now( ):
  return datetime.now(IST)

a_bp=Blueprint('admin',__name__,template_folder='../templates/admin')

def ar(f):
  @wraps(f)
  def df( *args,**kwargs ):
    if 'uid' not in session or session.get('role')!='admin':
      flash('Access denied.','danger')
      return redirect(url_for('auth.login'))
    return f(*args,**kwargs)
  return df


@a_bp.route('/dashboard')
@ar
def admin_dashboard():
 q=request.args.get('q')
 if q:
  st=f"%{q}%"
  l=Parkingplaces.query.filter(Parkingplaces.prime_location_name.ilike(st)).all()
 else:
  l=Parkingplaces.query.all()
 return render_template('admin/admin_dashboard.html',lots=l,query=q)

@a_bp.route('/add_lot',methods=['GET','POST'])
@ar
def add_lot():
 if request.method=='POST':
  try:
   print("Form data received:")
   for k,v in request.form.items():
    print(f"  {k}:{v}")
   rf=['prime_location_name','address','pin_code','price','maximum_number_of_spots']
   for f in rf:
    if not request.form.get(f):
     flash(f"Field '{f}' is required.","danger")
     return render_template('admin/add_lot.html')
   ot=request.form.get('opening')
   ct=request.form.get('closing')
   if ot:
    ot=datetime.strptime(ot,'%H:%M').time()
   if ct:
    ct=datetime.strptime(ct,'%H:%M').time()
   
   nl=Parkingplaces(
       prime_location_name=request.form.get('prime_location_name'),
       address=request.form.get('address'),city=request.form.get('city'),
       state=request.form.get('state'),pin_code=request.form.get('pin_code'),
       lat=float(request.form.get('lat')) if request.form.get('lat') else None,
       lon=float(request.form.get('lon')) if request.form.get('lon') else None,
       price=float(request.form.get('price')),
       maximum_number_of_spots=int(request.form.get('maximum_number_of_spots')),
       amenities=request.form.get('amenities'),opening=ot,closing=ct
   )
   print(f"Created lot object:{nl.prime_location_name}")
   db.session.add(nl)
   db.session.flush()
   print(f"Lot added to session,ID:{nl.id}")
   li=request.form.get('levels','G')
   ll=[lv.strip() for lv in li.split(',')]
   spl=nl.maximum_number_of_spots//len(ll)
   rs=nl.maximum_number_of_spots%len(ll)
   hes='has_ev_support' in request.form
   hps='has_premium_spots' in request.form
   
   sc=1
   for i,lv in enumerate(ll):
    sftl=spl+(1 if i<rs else 0)
    for j in range(sftl):
     st='standard'
     pm=1.0
     es=False
     ts=nl.maximum_number_of_spots
     pc=int(ts*0.1)
     ec=int(ts*0.1)
     
     if hps and sc<=pc:
      st='premium'
      pm=1.5
     elif hes and sc<=(pc+ec):
      es=True
      pm=1.25
    
     sp=Parkingspace(
      lid=nl.id,spot_number=f"{lv}{sc:02d}",
      levels=lv,status='A',
      spacetype=st,pricemulti=pm,
      evsupport=es
     )
     db.session.add(sp)
     sc+=1
   
   print(f"Created {sc - 1} parking spots")
   
   db.session.commit()
   print("Database commit successful")
   
   flash(f'Parking lot "{nl.prime_location_name}" created successfully with {nl.maximum_number_of_spots} spots!','success')
   return redirect(url_for('admin.admin_dashboard'))
   
  except ValueError as ve:
   db.session.rollback()
   print(f"ValueError:{ve}")
   flash(f'Invalid input:{ve}','danger')
  except Exception as e:
   db.session.rollback()
   print(f"Exception:{e}")
   flash(f'Error creating parking lot:{e}','danger')
 
 return render_template('admin/add_lot.html')

@a_bp.route('/edit_lot/<int:lid>',methods=['GET','POST'])
@ar
def edit_lot(lid):
 l=Parkingplaces.query.get_or_404(lid)
 if request.method=='POST':
  l.prime_location_name=request.form.get('prime_location_name')
  l.price=float(request.form.get('price'))
  l.address=request.form.get('address')
  l.pin_code=request.form.get('pin_code')
  try:
   db.session.commit()
   flash(f'Parking lot "{l.prime_location_name}" updated successfully!','success')
   return redirect(url_for('admin.admin_dashboard'))
  except Exception as e:
   db.session.rollback()
   flash(f'Error updating parking lot:{e}','danger')
 return render_template('admin/edit_lot.html',lot=l)


@a_bp.route('/delete_lot/<int:lid>',methods=['POST'])
@ar
def delete_lot(lid):
 l=Parkingplaces.query.get_or_404(lid)
 
 os=Parkingspace.query.filter_by(lid=lid,status='O').first()
 if os:
  flash('Cannot delete lot. One or more parking spots are currently occupied.','danger')
  return redirect(url_for('admin.admin_dashboard'))
 
 ar=Reservation.query.join(Parkingspace).filter(
  Parkingspace.lid==lid,
  Reservation.reservestatus=='active'
 ).first()
 if ar:
  flash('Cannot delete lot. There are active reservations for this parking lot.','danger')
  return redirect(url_for('admin.admin_dashboard'))
 
 try:
  Parkingspace.query.filter_by(lid=lid).delete()
  db.session.delete(l)
  db.session.commit()
  flash(f'Parking lot "{l.prime_location_name}" has been deleted successfully.','success')
 except Exception as e:
  db.session.rollback()
  flash(f'Error deleting parking lot:{e}','danger')
 
 return redirect(url_for('admin.admin_dashboard'))


@a_bp.route('/manage_spots/<int:lid>',methods=['GET','POST'])
@ar
def manage_spots(lid):
 l=Parkingplaces.query.get_or_404(lid)
 
 if request.method=='POST':
  action=request.form.get('action')
  
  if action=="add_spots":
   spots_to_add=int(request.form.get('spots_to_add',0))
   level=request.form.get('level','G')
   spot_type=request.form.get('spot_type','standard')
   
   if spots_to_add > 0:
    try:
     existing_spots=Parkingspace.query.filter_by(lid=lid,levels=level).all()
     if existing_spots:
      max_num=max([int(s.spot_number[len(level):]) for s in existing_spots if s.spot_number[len(level):].isdigit()])
     else:
      max_num=0
     
     for i in range(1,spots_to_add+1):
      spot_num=max_num+i
      pm=1.5 if spot_type=='premium' else 1.25 if spot_type=='ev' else 1.0
      es=True if spot_type=='ev' else False
      st='premium' if spot_type=='premium' else 'standard'
      
      new_spot=Parkingspace(
       lid=lid,spot_number=f"{level}{spot_num:02d}",
       levels=level,status='A',spacetype=st,
       pricemulti=pm,evsupport=es
      )
      db.session.add(new_spot)
     
     l.maximum_number_of_spots+=spots_to_add
     db.session.commit()
     
     flash(f'Successfully added {spots_to_add} {spot_type} spots to level {level}!','success')
     
    except Exception as e:
     db.session.rollback()
     flash(f'Error adding spots:{e}','danger')
  
  elif action=='remove_spots':
   spots_to_remove=request.form.getlist('spots_to_remove')
   
   if spots_to_remove:
    try:
     occupied_spots=Parkingspace.query.filter(
      Parkingspace.id.in_(spots_to_remove),Parkingspace.status=='O'
     ).all()
     
     reserved_spots=Parkingspace.query.filter(
      Parkingspace.id.in_(spots_to_remove),Parkingspace.isreserved==True
     ).all()
     
     if occupied_spots or reserved_spots:
      flash('Cannot remove occupied or reserved spots. Please wait for them to be freed.','danger')
     else:
      removed_count=Parkingspace.query.filter(Parkingspace.id.in_(spots_to_remove)).delete()
      l.maximum_number_of_spots -= removed_count
      db.session.commit()
      flash(f'Successfully removed {removed_count} spots!','success')
      
    except Exception as e:
     db.session.rollback()
     flash(f'Error removing spots:{e}','danger')
  
  return redirect(url_for('admin.manage_spots',lid=lid))
 
 spots=Parkingspace.query.filter_by(lid=lid).order_by(Parkingspace.levels,Parkingspace.spot_number).all()
 levels=list(set([s.levels for s in spots]))
 
 return render_template('admin/manage_spots.html',lot=l,spots=spots,levels=levels)

@a_bp.route('/users')
@ar
def view_users():
 u=User.query.filter_by(role='user').order_by(User.creation.desc()).all()
 return render_template('admin/view_users.html',users=u)


@a_bp.route('/user/details/<int:user_id>')
@ar
def user_details(user_id):
 u=User.query.get_or_404(user_id)
 reservations=Reservation.query.filter_by(uid=user_id).order_by(Reservation.createat.desc()).all()
 vehicles=Vehicle.query.filter_by(uid=user_id).all()
 return render_template('admin/user_details.html',u=u,reservations=reservations,vehicles=vehicles)


@a_bp.route('/user/toggle_active/<int:user_id>',methods=['POST'])
@ar
def toggle_user_active(user_id):
 u=User.query.get_or_404(user_id)
 
 if u.id==session['uid']:
  flash('You cannot deactivate your own account.','warning')
  return redirect(url_for('admin.view_users'))
 
 u.active= not u.active
 u.updation=get_ist_now()
 db.session.commit()
 
 st="activated" if u.active else "deactivated"
 flash(f'User {u.full_name} ({u.username}) has been {st}.','success')
 return redirect(url_for('admin.view_users'))


@a_bp.route('/reservations')
@ar
def view_reservations():
 r=Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()
 return render_template('admin/view_reservations.html',reservations=r)

@a_bp.route('/view_spots/<int:lid>')
@ar
def view_spots(lid):
 l=Parkingplaces.query.get_or_404(lid)
 s=Parkingspace.query.filter_by(lid=lid).order_by(Parkingspace.spot_number).all()
 return render_template('admin/view_spots.html',lot=l,spots=s)

@a_bp.route('/reviews')
@ar
def view_reviews():
 from models.models import Review
 r=Review.query.order_by(Review.timestamp.desc()).all()
 for rv in r:
  rv.user=User.query.get(rv.uid)
  rv.lot=Parkingplaces.query.get(rv.lid)
 ar=db.session.query(func.avg(Review.rating)).scalar() or 0
 tr=Review.query.count()
 return render_template('admin/view_reviews.html',
       reviews=r,
     avg_rating=ar,
   total_reviews=tr)

@a_bp.route('/lot_reviews/<int:lot_id>')
@ar
def lot_reviews(lot_id):
 from models.models import Review
 l=Parkingplaces.query.get_or_404(lot_id)
 r=Review.query.filter_by(lid=lot_id).order_by(Review.timestamp.desc()).all()
 for rv in r:
  rv.user=User.query.get(rv.uid)
 return render_template('admin/lot_reviews.html',lot=l,reviews=r)


@a_bp.route('/summary')
@ar
def summary():
 tu=User.query.filter_by(role='user').count()
 tl=Parkingplaces.query.count()
 tr=db.session.query(func.sum(Reservation.parking_cost)).scalar() or 0
 
 rr=Reservation.query.order_by(Reservation.createat.desc()).limit(5).all()
 
 td=get_ist_now().date()
 cl,cd=[],[]
 
 for i in range(6,-1,-1):
  dt=td - timedelta(days=i)
  dn=dt.strftime('%a')
  ct=Reservation.query.filter(func.date(Reservation.createat)==dt).count()
  cl.append(dn)
  cd.append(ct)
 
 cdd={'labels':cl,'data':cd}
 
 return render_template('admin/summary.html',tu=tu,tl=tl,tr=tr,rr=rr,cd=cdd)


@a_bp.route('/export/reservations')
@ar
def export_reservations():
 o=io.StringIO()
 w=csv.writer(o)
 w.writerow(['ID','User','Lot Name','Spot','Vehicle','Parked On','Left On','Cost','Status'])
 r=Reservation.query.all()
 for rs in r:
  w.writerow([
   rs.id,rs.user.full_name,rs.spot.lot.prime_location_name,
   rs.spot.spot_number,rs.vno,rs.parking_timestamp,
   rs.leaving_timestamp,rs.parking_cost,rs.reservestatus
   ])
 o.seek(0)
 rsp=make_response(o.getvalue())
 rsp.headers["Content-Disposition"]="attachment; filename=reservations.csv"
 rsp.headers["Content-type"]="text/csv"
 return rsp