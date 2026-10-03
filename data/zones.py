"""
Moradabad zone configuration.

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
"""

ZONES = [
    {"id": "civil_lines", "name": "Civil Lines", "lat": 28.8418, "lon": 78.7748,
     "built_up_density": 0.78, "ndvi_base": 0.24, "road_density": 0.62, "water_proximity": 0.35},
    {"id": "katghar", "name": "Katghar", "lat": 28.8558, "lon": 78.7981,
     "built_up_density": 0.66, "ndvi_base": 0.31, "road_density": 0.55, "water_proximity": 0.30},
    {"id": "majhola", "name": "Majhola", "lat": 28.8632, "lon": 78.7801,
     "built_up_density": 0.60, "ndvi_base": 0.34, "road_density": 0.48, "water_proximity": 0.55},
    {"id": "pakwara", "name": "Pakwara", "lat": 28.8291, "lon": 78.7423,
     "built_up_density": 0.42, "ndvi_base": 0.46, "road_density": 0.33, "water_proximity": 0.40},
    {"id": "asalatpura", "name": "Asalatpura", "lat": 28.8355, "lon": 78.7602,
     "built_up_density": 0.74, "ndvi_base": 0.22, "road_density": 0.58, "water_proximity": 0.25},
    {"id": "galshaheed", "name": "Galshaheed", "lat": 28.8386, "lon": 78.7789,
     "built_up_density": 0.80, "ndvi_base": 0.19, "road_density": 0.66, "water_proximity": 0.20},
    {"id": "budh_bazaar", "name": "Budh Bazaar", "lat": 28.8365, "lon": 78.7841,
     "built_up_density": 0.88, "ndvi_base": 0.12, "road_density": 0.74, "water_proximity": 0.15},
    {"id": "moradabad_central", "name": "Moradabad Central", "lat": 28.8386, "lon": 78.7733,
     "built_up_density": 0.90, "ndvi_base": 0.10, "road_density": 0.80, "water_proximity": 0.18},
    {"id": "rampur_road", "name": "Rampur Road", "lat": 28.8477, "lon": 78.8102,
     "built_up_density": 0.55, "ndvi_base": 0.29, "road_density": 0.50, "water_proximity": 0.28},
    {"id": "delhi_road", "name": "Delhi Road", "lat": 28.8203, "lon": 78.7562,
     "built_up_density": 0.58, "ndvi_base": 0.27, "road_density": 0.52, "water_proximity": 0.22},
    {"id": "new_moradabad", "name": "New Moradabad", "lat": 28.8156, "lon": 78.7891,
     "built_up_density": 0.48, "ndvi_base": 0.38, "road_density": 0.40, "water_proximity": 0.45},
]

ZONE_BY_ID = {z["id"]: z for z in ZONES}
