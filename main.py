# main.py - AI Smart Traffic Congestion Control System
# Entry point: loads CSV dataset → feeds signal controller → runs Tkinter GUI

import tkinter as tk
import threading
import time

from config import CONFIG
from dataset_loader import DatasetLoader
from signal_controller import SignalController
from gui import TrafficGUI


def dataset_feed_loop(loader, controller, stop_event):
    """
    Background thread: reads CSV rows at simulation speed,
    feeds vehicle counts into the signal controller.
    """
    interval = CONFIG["simulation_interval"] / 1000.0  # Convert ms → seconds
    while not stop_event.is_set():
        counts = loader.get_next_row()
        controller.update_counts(counts)
        time.sleep(interval)


def main():
    print("=" * 55)
    print("  AI-Based Smart Traffic Congestion Control System")
    print("  A.G. Patil Institute of Technology, Solapur")
    print("=" * 55)

    # 1. Load Kaggle CSV dataset
    loader = DatasetLoader()

    # Print dataset stats
    stats = loader.get_stats_summary()
    if stats:
        print("\n[Dataset Summary]")
        for key, s in stats.items():
            print(f"  {key.capitalize()}: avg={s['mean']}, max={s['max']}, min={s['min']}")

    # 2. Initialize signal controller
    controller = SignalController()

    # 3. Start dataset feed in background thread
    stop_event = threading.Event()
    feed_thread = threading.Thread(
        target=dataset_feed_loop,
        args=(loader, controller, stop_event),
        daemon=True
    )
    feed_thread.start()
    print("\n[INFO] Dataset feed thread started.")

    # 4. Launch Tkinter GUI (runs in main thread)
    root = tk.Tk()
    gui = TrafficGUI(root, controller)
    gui.start()

    def on_close():
        print("\n[INFO] Shutting down...")
        stop_event.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    print("[INFO] GUI launched. Close window to exit.\n")
    root.mainloop()


if __name__ == "__main__":
    main()
