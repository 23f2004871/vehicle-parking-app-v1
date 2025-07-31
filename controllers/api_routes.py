from flask import Blueprint,jsonify
from models.models import Parkingplaces,Parkingspace

a_bp=Blueprint('api',__name__,url_prefix='/api')


@a_bp.route('/lots',methods=['GET'])
def get_lots( ):
    try:
        l=Parkingplaces.query.all()
        
        ll=[]
        for lt in l:
            ll.append({
                'id':lt.id,'name':lt.prime_location_name,
                'address' :lt.address,
                'pincode':lt.pin_code,'price_per_hour' :lt.price,
                'total_spots':lt.maximum_number_of_spots
            })
            
        return jsonify(ll)
    except Exception as e:
        return jsonify({"error":str(e)}),500
    
@a_bp.route('/lots/<int:lot_id>',methods=['GET'])
def get_lot_details(lid):
     try:
          lt=Parkingplaces.query.get_or_404(lid)
          s=lt.spots 
          sl=[]
          for sp in s:
               sl.append({
                    "id":sp.id,
                    "spot_number":sp.spot_number,
                    "status":'Available' if sp.status == 'A' else 'Occupied',
                    "type":sp.spacetype
               })

          ld={
               'id':lt.id,
                'name':lt.prime_location_name,
                         'address':lt.address,
            'price_per_hour':lt.price,
                    'spots':sl
          }
          
          return jsonify(ld)
     except Exception as e:
          return jsonify({'error':str(e)}),500