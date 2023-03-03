from flask import Flask, jsonify, request
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

for i in json.load(open('../data/data.json')):
    ip_list.append(get_location(i["ip"]))

@app.route('/cdn/lb/ip', methods=['GET'])
def closest_ip():
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

    # Return the closest IP as a JSON response
    return jsonify({'ip': closest_ip["ip"],'name': str(closest_ip["region"]+" ("+closest_ip["country"]+")"), "dist": min_distance, "req_ip": req_ip["ip"]})

if __name__ == '__main__':
    app.run()
