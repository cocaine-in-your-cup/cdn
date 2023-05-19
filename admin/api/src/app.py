import socket
from flask import Flask, jsonify, redirect, request
from geopy.distance import geodesic as GD
import json
import requests

app = Flask(__name__)

# Opens and updates json file
def update_file(obj):
    with open ('../data/log_request.json', mode="r+") as file:
        file.seek(0,2)
        position = file.tell() - 2
        file.seek(position)
        file.write(str(","+json.dumps(obj)+"]}"))
    return

# Returns logs of request
@app.route('/monitor', methods=['GET'])
def stats_monitor():
    # add condition for when the file doesnt exist
    return json.load(open('../data/log_request.json'))


def find_object_in_array(array, key, value):
    for obj in array:
        if key in obj and obj[key] == value:
            return obj
    return None

# Returns geolocation info from ip addr
def get_location(ip):
    ip_address = ip
    response = requests.get(f'https://ipinfo.io/{ip_address}/geo').json()
    location_data = {
        "ip": ip_address,
        "city": response.get("city"),
        "region": response.get("region"),
        "country": response.get("country"),
        "loc": (float(response.get("loc").split(',')[0]),float(response.get("loc").split(',')[1])),
    }
    return location_data

# List of IPs to compare against
ip_list = []
ip_obj = []

for i in json.load(open('../data/data.json')):
    ip_obj.append(i)
    ip_list.append(get_location(i["ip"]))

@app.route('/cdn/lb/ip', methods=['GET'])
@app.route('/cdn/lb/ip/<path:subpath>', methods=['GET'])
def closest_ip(subpath=None):
    # Get the request IP
    req_ip = request.headers.get('X-Real-IP')

    # Get the geolocation of the request ip
    req_ip = get_location(req_ip)
    # Append request to the log file
    update_file(req_ip)

    # Initialize variables to hold the closest IP and distance
    closest_ip = None
    min_distance = float('inf')

    # Iterate through the IP list and calculate the distance to each IP
    for ip in ip_list:

        # Calculate the distance between the request IP and the list IP
        distance = GD(req_ip["loc"],ip["loc"]).km
        
        # print("The distance between", req_ip["region"]," (" +req_ip["country"]+")" ,"and", ip["region"],"("+ip["country"]+")" , "is :",distance, "km")

        # If the distance is smaller than the current minimum distance, update the closest IP and minimum distance
        if distance < min_distance:
            closest_ip = ip
            min_distance = distance


    found_object = find_object_in_array(ip_obj, "ip", closest_ip['ip'])
    # Return the closest IP as a JSON response
    # return jsonify({'ip': closest_ip["ip"],'name': str(closest_ip["region"]+" ("+closest_ip["country"]+")"), "dist": min_distance, "req_ip": req_ip["ip"]})
    
    # Handle the route without additional content     
    if subpath is None:   
        # ...
        return jsonify({'region': found_object["name"],'cdn_url': str("https://" + found_object["url"]),"request_ip": req_ip["ip"]})
    
    # Handle the route with additional content
    else: 
        return redirect(str("https://" + found_object["url"] + "/" + subpath), code=302)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def redirect_to_cdn_lb_ip(path):
    if not path.startswith('cdn/lb/ip'):
        redirect_url = '/cdn/lb/ip'
        return redirect(redirect_url, code=302)
    else:
        return closest_ip()
    
if __name__ == '__main__':
    app.run()
