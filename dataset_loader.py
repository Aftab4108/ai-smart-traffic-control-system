# dataset_loader.py - Loads and parses Kaggle Traffic Flow CSV dataset

import pandas as pd
import numpy as np
import os
from config import CONFIG


class DatasetLoader:
    def __init__(self):
        self.df = None
        self.current_index = 0
        self.road_names = CONFIG["road_names"]
        self.col = CONFIG["csv_columns"]
        self._load()

    def _load(self):
        path = CONFIG["dataset_path"]
        if not os.path.exists(path):
            print(f"[WARNING] Dataset not found at '{path}'. Using simulated data.")
            self.df = self._generate_simulated_data()
            return

        try:
            self.df = pd.read_csv(path)
            print(f"[INFO] Loaded dataset: {len(self.df)} rows, columns: {list(self.df.columns)}")
            self._normalize_columns()
        except Exception as e:
            print(f"[ERROR] Failed to load CSV: {e}. Using simulated data.")
            self.df = self._generate_simulated_data()

    def _normalize_columns(self):
        """Try to auto-map common Kaggle traffic CSV column names."""
        col_map = {}
        lower_cols = {c.lower(): c for c in self.df.columns}

        # Auto-detect column names
        for key, candidates in {
            "cars":   ["carcount", "cars", "car", "car_count", "car count"],
            "bikes":  ["bikecount", "bikes", "bike", "motorcycle", "moto"],
            "buses":  ["buscount", "buses", "bus", "bus_count"],
            "trucks": ["truckcount", "trucks", "truck", "truck_count"],
            "total":  ["total", "totalcount", "total_count", "count"],
            "time":   ["time", "datetime", "timestamp", "date_time", "date"],
            "junction": ["junction", "road", "road_id", "lane", "location"]
        }.items():
            for c in candidates:
                if c in lower_cols:
                    col_map[key] = lower_cols[c]
                    break

        # Update config col mapping with detected names
        for k, v in col_map.items():
            self.col[k] = v

        print(f"[INFO] Column mapping: {self.col}")

    def _generate_simulated_data(self):
        """Generate realistic simulated traffic data for 4 roads."""
        np.random.seed(42)
        n = 500
        times = pd.date_range("2024-01-01 06:00", periods=n, freq="1min")
        data = []
        for i, t in enumerate(times):
            # Simulate peak hours (8-10am, 5-7pm)
            hour = t.hour
            peak = 1.0
            if 8 <= hour <= 10 or 17 <= hour <= 19:
                peak = 3.0
            elif 12 <= hour <= 14:
                peak = 1.8

            for j, road in enumerate(["1", "2", "3", "4"]):
                base = np.random.randint(5, 20) * peak
                cars   = int(base * np.random.uniform(0.5, 1.5))
                bikes  = int(base * np.random.uniform(0.2, 0.8))
                buses  = int(base * np.random.uniform(0.05, 0.2))
                trucks = int(base * np.random.uniform(0.05, 0.15))
                total  = cars + bikes + buses + trucks
                data.append({
                    "Time": str(t),
                    "Junction": road,
                    "CarCount": cars,
                    "BikeCount": bikes,
                    "BusCount": buses,
                    "TruckCount": trucks,
                    "Total": total
                })

        df = pd.DataFrame(data)
        print(f"[INFO] Generated simulated dataset: {len(df)} rows")
        return df

    def get_next_row(self):
        """
        Returns vehicle counts for all 4 roads at the next timestep.
        Returns: dict { "North": {cars, bikes, buses, trucks, total, emergency}, ... }
        """
        result = {}
        junction_col = self.col.get("junction")

        # Check if dataset has junction/road column
        if junction_col and junction_col in self.df.columns:
            junctions = self.df[junction_col].unique()
            for i, road in enumerate(self.road_names):
                junc_id = junctions[i % len(junctions)]
                junc_df = self.df[self.df[junction_col] == junc_id]
                idx = self.current_index % len(junc_df)
                row = junc_df.iloc[idx]
                result[road] = self._extract_counts(row)
        else:
            # Single road CSV - split rows across 4 roads
            for i, road in enumerate(self.road_names):
                idx = (self.current_index + i * 10) % len(self.df)
                row = self.df.iloc[idx]
                result[road] = self._extract_counts(row)

        self.current_index = (self.current_index + 1) % len(self.df)

        # Randomly inject emergency vehicle (2% chance per cycle)
        if np.random.random() < 0.02:
            emergency_road = np.random.choice(self.road_names)
            result[emergency_road]["emergency"] = True
            print(f"[ALERT] Emergency vehicle detected on {emergency_road} road!")

        return result

    def _extract_counts(self, row):
        """Extract vehicle counts from a CSV row."""
        def safe_get(col_key, default=0):
            col = self.col.get(col_key)
            if col and col in row.index:
                val = row[col]
                return int(val) if pd.notna(val) else default
            return default

        cars   = safe_get("cars", np.random.randint(5, 40))
        bikes  = safe_get("bikes", np.random.randint(2, 20))
        buses  = safe_get("buses", np.random.randint(0, 8))
        trucks = safe_get("trucks", np.random.randint(0, 5))
        total  = safe_get("total") or (cars + bikes + buses + trucks)

        return {
            "cars": cars,
            "bikes": bikes,
            "buses": buses,
            "trucks": trucks,
            "total": total,
            "emergency": False
        }

    def get_stats_summary(self):
        """Return summary statistics from the full dataset."""
        if self.df is None:
            return {}
        stats = {}
        for key in ["cars", "bikes", "buses", "trucks", "total"]:
            col = self.col.get(key)
            if col and col in self.df.columns:
                stats[key] = {
                    "mean": round(self.df[col].mean(), 1),
                    "max":  int(self.df[col].max()),
                    "min":  int(self.df[col].min()),
                }
        return stats
