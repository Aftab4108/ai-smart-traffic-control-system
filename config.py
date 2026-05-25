# config.py - Central configuration for AI Traffic Control System

CONFIG = {
    # Dataset path (Kaggle CSV)
    "dataset_path": "dataset/traffic_data.csv",

    # YOLO model (uses pretrained COCO - no training needed)
    "model_path": "yolov8n.pt",

    # Signal timing (seconds)
    "max_green_time": 45,
    "min_green_time": 45,
    "yellow_time": 5,
    "red_time": 5,

    # Vehicle weights for signal priority scoring
    "vehicle_weights": {
        "car": 1,
        "motorcycle": 0.5,
        "bus": 2,
        "truck": 2,
        "person": 0.3,
    },

    # Emergency vehicle classes
    "emergency_classes": ["ambulance", "fire truck", "police car"],

    # Roads
    "road_names": ["North", "South", "East", "West"],

    # Simulation speed (ms between updates)
    "simulation_interval": 1000,

    # CSV column mapping (adjust to match your Kaggle dataset columns)
    "csv_columns": {
        "time": "Time",           # Time column name in CSV
        "cars": "CarCount",       # Car count column
        "bikes": "BikeCount",     # Bike/motorcycle count
        "buses": "BusCount",      # Bus count
        "trucks": "TruckCount",   # Truck count
        "total": "Total",         # Total vehicle count
        "junction": "Junction"    # Junction/road ID column (optional)
    }
}
