"""
Moradabad + Delhi zone configuration.

IMPORTANT (data honesty):
Coordinates are approximate geographic centers of these localities (public
knowledge, OpenStreetMap-level accuracy). The environmental attributes
(built_up_density, ndvi_base, road_density, water_proximity) are NOT measured
values -- they are reasonable, hand-set *priors* used only to generate a
synthetic training/demo dataset so the ML pipeline has something realistic to
learn from. They are clearly separate from anything the system calls
"live" or "measured". Replace this prior table with real
Sentinel-2 / IMD / municipal readings to make the whole pipeline real.

UNVERIFIED: these numbers have not been checked against satellite imagery
or ground truth. Please review each zone with local knowledge before
presenting any zone ranking as a finding (e.g. leafy administrative areas
such as Civil Lines are often less built-up than a 0.78 prior suggests).
Because the priors are fixed, zone rankings (and therefore "hotspots") are
largely determined by this table, not by live measurements.

The same applies to the Delhi zones below: coordinates are approximate,
land-cover values are hand-set estimates and must be replaced with real
satellite / OpenStreetMap data.
"""

# ----------------------------------------------------------------- Moradabad
# ZONES / ZONE_BY_ID stay Moradabad-only so existing code keeps working.
ZONES = [
    {"id": "civil_lines", "name": "Civil Lines", "city": "Moradabad", "lat": 28.8418, "lon": 78.7748,
     "built_up_density": 0.78, "ndvi_base": 0.24, "road_density": 0.62, "water_proximity": 0.35},
    {"id": "katghar", "name": "Katghar", "city": "Moradabad", "lat": 28.8558, "lon": 78.7981,
     "built_up_density": 0.66, "ndvi_base": 0.31, "road_density": 0.55, "water_proximity": 0.30},
    {"id": "majhola", "name": "Majhola", "city": "Moradabad", "lat": 28.8632, "lon": 78.7801,
     "built_up_density": 0.60, "ndvi_base": 0.34, "road_density": 0.48, "water_proximity": 0.55},
    {"id": "pakwara", "name": "Pakwara", "city": "Moradabad", "lat": 28.8291, "lon": 78.7423,
     "built_up_density": 0.42, "ndvi_base": 0.46, "road_density": 0.33, "water_proximity": 0.40},
    {"id": "asalatpura", "name": "Asalatpura", "city": "Moradabad", "lat": 28.8355, "lon": 78.7602,
     "built_up_density": 0.74, "ndvi_base": 0.22, "road_density": 0.58, "water_proximity": 0.25},
    {"id": "galshaheed", "name": "Galshaheed", "city": "Moradabad", "lat": 28.8386, "lon": 78.7789,
     "built_up_density": 0.80, "ndvi_base": 0.19, "road_density": 0.66, "water_proximity": 0.20},
    {"id": "budh_bazaar", "name": "Budh Bazaar", "city": "Moradabad", "lat": 28.8365, "lon": 78.7841,
     "built_up_density": 0.88, "ndvi_base": 0.12, "road_density": 0.74, "water_proximity": 0.15},
    {"id": "moradabad_central", "name": "Moradabad Central", "city": "Moradabad", "lat": 28.8386, "lon": 78.7733,
     "built_up_density": 0.90, "ndvi_base": 0.10, "road_density": 0.80, "water_proximity": 0.18},
    {"id": "rampur_road", "name": "Rampur Road", "city": "Moradabad", "lat": 28.8477, "lon": 78.8102,
     "built_up_density": 0.55, "ndvi_base": 0.29, "road_density": 0.50, "water_proximity": 0.28},
    {"id": "delhi_road", "name": "Delhi Road", "city": "Moradabad", "lat": 28.8203, "lon": 78.7562,
     "built_up_density": 0.58, "ndvi_base": 0.27, "road_density": 0.52, "water_proximity": 0.22},
    {"id": "new_moradabad", "name": "New Moradabad", "city": "Moradabad", "lat": 28.8156, "lon": 78.7891,
     "built_up_density": 0.48, "ndvi_base": 0.38, "road_density": 0.40, "water_proximity": 0.45},
]

ZONE_BY_ID = {z["id"]: z for z in ZONES}

# --------------------------------------------------------------------- Delhi
# IDs are prefixed "dl_" so they can never clash with Moradabad zone IDs.
DELHI_ZONES = [
    {"id": "dl_connaught_place", "name": "Connaught Place", "city": "Delhi", "lat": 28.6315, "lon": 77.2167,
     "built_up_density": 0.85, "ndvi_base": 0.15, "road_density": 0.80, "water_proximity": 0.20},
    {"id": "dl_chandni_chowk", "name": "Chandni Chowk", "city": "Delhi", "lat": 28.6506, "lon": 77.2303,
     "built_up_density": 0.95, "ndvi_base": 0.05, "road_density": 0.85, "water_proximity": 0.35},
    {"id": "dl_karol_bagh", "name": "Karol Bagh", "city": "Delhi", "lat": 28.6519, "lon": 77.1909,
     "built_up_density": 0.90, "ndvi_base": 0.08, "road_density": 0.78, "water_proximity": 0.12},
    {"id": "dl_laxmi_nagar", "name": "Laxmi Nagar", "city": "Delhi", "lat": 28.6304, "lon": 77.2773,
     "built_up_density": 0.92, "ndvi_base": 0.07, "road_density": 0.76, "water_proximity": 0.40},
    {"id": "dl_lutyens", "name": "Lutyens Delhi", "city": "Delhi", "lat": 28.5918, "lon": 77.2273,
     "built_up_density": 0.35, "ndvi_base": 0.55, "road_density": 0.45, "water_proximity": 0.20},
    {"id": "dl_saket", "name": "Saket", "city": "Delhi", "lat": 28.5245, "lon": 77.2066,
     "built_up_density": 0.68, "ndvi_base": 0.28, "road_density": 0.60, "water_proximity": 0.12},
    {"id": "dl_okhla", "name": "Okhla", "city": "Delhi", "lat": 28.5355, "lon": 77.2710,
     "built_up_density": 0.86, "ndvi_base": 0.10, "road_density": 0.70, "water_proximity": 0.35},
    {"id": "dl_dwarka", "name": "Dwarka", "city": "Delhi", "lat": 28.5921, "lon": 77.0460,
     "built_up_density": 0.62, "ndvi_base": 0.30, "road_density": 0.55, "water_proximity": 0.10},
    {"id": "dl_janakpuri", "name": "Janakpuri", "city": "Delhi", "lat": 28.6219, "lon": 77.0878,
     "built_up_density": 0.75, "ndvi_base": 0.22, "road_density": 0.62, "water_proximity": 0.10},
    {"id": "dl_rohini", "name": "Rohini", "city": "Delhi", "lat": 28.7495, "lon": 77.0565,
     "built_up_density": 0.70, "ndvi_base": 0.25, "road_density": 0.58, "water_proximity": 0.12},
    {"id": "dl_narela", "name": "Narela", "city": "Delhi", "lat": 28.8527, "lon": 77.0929,
     "built_up_density": 0.50, "ndvi_base": 0.35, "road_density": 0.40, "water_proximity": 0.15},
    {"id": "dl_najafgarh", "name": "Najafgarh", "city": "Delhi", "lat": 28.6092, "lon": 76.9798,
     "built_up_density": 0.52, "ndvi_base": 0.36, "road_density": 0.42, "water_proximity": 0.30},
]

DELHI_ZONE_BY_ID = {z["id"]: z for z in DELHI_ZONES}

# ------------------------------------------------------------ multi-city API
CITIES = {
    "Moradabad": {"zones": ZONES, "center": (28.8386, 78.7733)},
    "Delhi": {"zones": DELHI_ZONES, "center": (28.6139, 77.2090)},
}

ALL_ZONES = ZONES + DELHI_ZONES
ALL_ZONE_BY_ID = {z["id"]: z for z in ALL_ZONES}


def zones_for_city(city):
    """Zones of one city, or [] if the city is not supported."""
    entry = CITIES.get(city)
    return entry["zones"] if entry else []