from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests


# ================================
# HOME PAGE
# ================================
def home(request):
    return render(request, 'hospital.html')


# ================================
# GET ROUTE (Navigation + Ambulance tracking)
# ================================
@csrf_exempt
def get_route(request):

    try:

        start_lat = float(request.GET.get("start_lat"))
        start_lon = float(request.GET.get("start_lon"))
        end_lat = float(request.GET.get("end_lat"))
        end_lon = float(request.GET.get("end_lon"))

        url = "https://api.openrouteservice.org/v2/directions/driving-car"

        headers = {
            "Authorization": "5b3ce3597851110001cf624855a68673b58f49c4a7cab32a810eac2c",
            "Content-Type": "application/json"
        }

        body = {
            "coordinates": [
                [start_lon, start_lat],
                [end_lon, end_lat]
            ]
        }

        response = requests.post(url, json=body, headers=headers)

        print("ORS STATUS:", response.status_code)

        data = response.json()

        if "routes" not in data or len(data["routes"]) == 0:
            return JsonResponse({"error": "No route found"}, status=500)

        route = data["routes"][0]

        geometry = route.get("geometry")   # THIS IS ENCODED STRING

        summary = route.get("summary", {})

        distance = summary.get("distance", 0)
        duration = summary.get("duration", 0)

        return JsonResponse({

            "geometry": geometry,   # send encoded polyline
            "distance": distance,
            "duration": duration

        })

    except Exception as e:

        print("ERROR:", str(e))

        return JsonResponse({
            "error": str(e)
        }, status=500)


# ================================
# FIND NEARBY HOSPITALS
# ================================
def nearby_hospitals(request):

    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    if not lat or not lon:
        return JsonResponse({'error': 'Missing latitude or longitude'}, status=400)

    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"="hospital"](around:5000,{lat},{lon});
      node["amenity"="clinic"](around:5000,{lat},{lon});
    );
    out body;
    """

    # Multiple Overpass servers (fallback list)
    servers = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://overpass.openstreetmap.fr/api/interpreter"
    ]

    for server in servers:

        try:

            print("Trying server:", server)

            response = requests.post(
                server,
                data=query,
                headers={"Content-Type": "text/plain"},
                timeout=10
            )

            if response.status_code == 200:

                data = response.json()

                hospitals = []

                for element in data.get("elements", []):

                    hospitals.append({
                        "id": element.get("id"),
                        "name": element.get("tags", {}).get("name", "Unnamed Hospital"),
                        "lat": element.get("lat"),
                        "lon": element.get("lon")
                    })

                print("Success from:", server)

                return JsonResponse({
                    "hospitals": hospitals
                })

        except Exception as e:

            print("Server failed:", server, str(e))

            continue

    return JsonResponse({
        "error": "All Overpass servers failed"
    }, status=500)


# ================================
# CALL AMBULANCE (Simulation)
# ================================
def call_ambulance(request):

    user_lat = request.GET.get('lat')
    user_lon = request.GET.get('lon')

    hospital_lat = request.GET.get('hospital_lat')
    hospital_lon = request.GET.get('hospital_lon')

    if not all([user_lat, user_lon, hospital_lat, hospital_lon]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    # reuse get_route logic
    request.GET = request.GET.copy()

    request.GET['start_lat'] = hospital_lat
    request.GET['start_lon'] = hospital_lon
    request.GET['end_lat'] = user_lat
    request.GET['end_lon'] = user_lon

    return get_route(request)
