# 🚦 AI-Based Smart Traffic Congestion Control System
**A.G. Patil Institute of Technology, Solapur | BE-CSE Mini Project Phase-II 2026**

---

## 📁 Project Structure

```
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

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add your Kaggle dataset
- Download from Kaggle (e.g., **Traffic Flow Count Dataset**)
- Place the CSV file at: `dataset/traffic_data.csv`
- Common Kaggle dataset: https://www.kaggle.com/datasets/hasibullahaman/traffic-prediction-dataset

> ✅ **No dataset?** The system auto-generates realistic simulated data if no CSV is found.

### 3. Run the system
```bash
python main.py
```

---

## 🗂️ Supported CSV Column Names (Auto-detected)

The system auto-detects these common Kaggle column names:

| Data | Accepted Column Names |
|------|-----------------------|
| Time | `Time`, `DateTime`, `Timestamp` |
| Cars | `CarCount`, `Cars`, `Car` |
| Bikes | `BikeCount`, `Bikes`, `Motorcycle` |
| Buses | `BusCount`, `Buses`, `Bus` |
| Trucks | `TruckCount`, `Trucks`, `Truck` |
| Total | `Total`, `TotalCount` |
| Junction | `Junction`, `Road`, `Lane`, `Location` |

If your columns differ, edit `config.py → csv_columns`.

---

## 🔧 Configuration (`config.py`)

| Setting | Value | Description |
|---------|---------|-------------|
| `max_green_time` | 45s | Green signal duration |
| `min_green_time` | 45s | Green signal duration |
| `yellow_time` | 5s | Yellow signal duration |
| `simulation_interval` | 1000ms | Speed of simulation |
| `vehicle_weights` | car=1, bus=2, truck=2, bike=0.5 | Priority scoring weights |

---

## 🚦 How It Works

```
CSV Dataset Row
      ↓
DatasetLoader.get_next_row()
      ↓
Vehicle counts per road (North/South/East/West)
      ↓
SignalController.update_counts()
      ↓
Dynamic green time = min_green + (score/60) × (max_green - min_green)
      ↓
Highest priority road gets GREEN signal
      ↓
Emergency vehicle? → Immediate GREEN override
      ↓
Tkinter GUI updates every second
```

---

## 🖥️ GUI Features

- 🟢🟡🔴 Animated traffic lights for all 4 roads
- ⏱️ Live countdown timer per road
- 🚗 Vehicle type counts (cars, bikes, buses, trucks)
- 📊 Priority score display
- 🚨 Emergency vehicle alert banner
- 📈 System stats (cycles, total vehicles cleared, active green road)

---

## 🧠 Algorithm: Dynamic Signal Timing

```python
score = cars×1 + bikes×0.5 + buses×2 + trucks×2
green_time = clamp(min_green + (score/60) × (max_green - min_green), 10, 50)
```

A road with more heavy vehicles (buses, trucks) gets proportionally more green time.

---

## 👩‍💻 Team
- Aditi Kulkarni
- Meghana Sidgiddi
- Aftab Patel
- Ganesh Jadhav

**Guide:** Prof. A. P. Hosale (Computer Engineering)
