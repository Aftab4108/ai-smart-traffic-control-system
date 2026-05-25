# 🚦 AI-Based Smart Traffic Congestion Control System
### A.G. Patil Institute of Technology, Solapur | BE-CSE Mini Project Phase-II 2026

---

# 📁 Project Structure

```text
traffic_system/
│
├── main.py              ← Entry point (run this)
├── config.py            ← All settings (timing, paths, weights)
├── dataset_loader.py    ← Kaggle CSV loader + auto column detection
├── signal_controller.py ← Dynamic signal timing algorithm
├── gui.py               ← Tkinter 4-road traffic light GUI
├── requirements.txt     ← Python dependencies
│
└── dataset/
    └── traffic_data.csv ← Place your Kaggle CSV here
```

---

# ⚙️ Setup

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Add Your Kaggle Dataset

- Download a traffic dataset from Kaggle  
- Example Dataset:  
  https://www.kaggle.com/datasets/hasibullahaman/traffic-prediction-dataset

- Place the CSV file inside:

```text
dataset/traffic_data.csv
```

> ✅ If no dataset is found, the system automatically generates simulated traffic data.

## 3. Run the System

```bash
python main.py
```

---

# 🗂️ Supported CSV Column Names (Auto-Detected)

| Data Type | Accepted Column Names |
|------------|-----------------------|
| Time | `Time`, `DateTime`, `Timestamp` |
| Cars | `CarCount`, `Cars`, `Car` |
| Bikes | `BikeCount`, `Bikes`, `Motorcycle` |
| Buses | `BusCount`, `Buses`, `Bus` |
| Trucks | `TruckCount`, `Trucks`, `Truck` |
| Total | `Total`, `TotalCount` |
| Junction | `Junction`, `Road`, `Lane`, `Location` |

If your dataset uses different column names, edit:

```python
config.py → csv_columns
```

---

# 🔧 Configuration (`config.py`)

| Setting | Value | Description |
|----------|--------|-------------|
| `max_green_time` | 45s | Maximum green signal duration |
| `min_green_time` | 10s | Minimum green signal duration |
| `yellow_time` | 5s | Yellow signal duration |
| `simulation_interval` | 1000ms | Simulation update speed |
| `vehicle_weights` | car=1, bus=2, truck=2, bike=0.5 | Vehicle priority weights |

---

# 🚦 How It Works

```text
CSV Dataset Row
      ↓
DatasetLoader.get_next_row()
      ↓
Vehicle counts per road
      ↓
SignalController.update_counts()
      ↓
Dynamic green time calculation
      ↓
Highest priority road gets GREEN signal
      ↓
Emergency vehicle override (if detected)
      ↓
Tkinter GUI updates every second
```

---

# 🖥️ GUI Features

- 🟢🟡🔴 Animated traffic lights for all 4 roads
- ⏱️ Live countdown timer
- 🚗 Vehicle count display
- 📊 Priority score monitoring
- 🚨 Emergency vehicle alert system
- 📈 Traffic statistics dashboard

---

# 🧠 Dynamic Signal Timing Algorithm

```python
score = cars * 1 + bikes * 0.5 + buses * 2 + trucks * 2

green_time = clamp(
    min_green + (score / 60) * (max_green - min_green),
    10,
    50
)
```

Roads with more heavy vehicles such as buses and trucks receive longer green signal duration.

---

# 👨‍💻 Developer

## Aftab Patel

### Guide:
Prof. A. P. Hosale  
(Computer Engineering Department)

---
