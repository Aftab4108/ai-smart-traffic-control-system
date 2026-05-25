# gui.py - Tkinter GUI with scrollable page, vehicle caps (no limit shown), and 2 live graphs

import tkinter as tk
from tkinter import ttk
from signal_controller import SignalState
from config import CONFIG
import collections

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ─── Color Palette ────────────────────────────────────────────────────────────
BG_DARK       = "#0D1117"
BG_PANEL      = "#161B22"
BG_CARD       = "#1E2530"
ACCENT_BLUE   = "#1F6FEB"
ACCENT_GREEN  = "#3FB950"
ACCENT_RED    = "#F85149"
ACCENT_YELL   = "#D29922"
ACCENT_ORANGE = "#E07B30"
TEXT_PRIMARY  = "#E6EDF3"
TEXT_MUTED    = "#8B949E"
TEXT_WHITE    = "#FFFFFF"
EMERGENCY_BG  = "#5A1A1A"
BORDER_COLOR  = "#30363D"

ROAD_COLORS   = ["#1F6FEB", "#3FB950", "#F85149", "#D29922"]   # one per road
MAX_HISTORY   = 60   # data points kept per road


class RoadCard:
    """A single road's signal display card."""

    def __init__(self, parent, road_name, col_index):
        self.road_name = road_name

        self.frame = tk.Frame(parent, bg=BG_CARD, bd=0, relief="flat",
                              highlightthickness=1, highlightbackground=BORDER_COLOR,
                              width=220, height=560)
        self.frame.grid(row=0, column=col_index, padx=8, pady=8, sticky="nsew")
        self.frame.pack_propagate(False)

        tk.Label(self.frame, text=f"🚦 {road_name.upper()} ROAD",
                 bg=BG_CARD, fg=TEXT_PRIMARY, font=("Consolas", 11, "bold")).pack(pady=(12, 4))

        self.canvas = tk.Canvas(self.frame, width=70, height=170,
                                bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(pady=6)
        self._draw_light_housing()
        self.red_light    = self.canvas.create_oval(15, 10,  55, 50,  fill="#3a1010", outline="#555")
        self.yellow_light = self.canvas.create_oval(15, 65,  55, 105, fill="#3a3010", outline="#555")
        self.green_light  = self.canvas.create_oval(15, 120, 55, 160, fill="#103a10", outline="#555")

        self.countdown_var = tk.StringVar(value="--")
        tk.Label(self.frame, textvariable=self.countdown_var,
                 bg=BG_CARD, fg=TEXT_WHITE, font=("Consolas", 22, "bold"),
                 width=4, anchor="center").pack()
        tk.Label(self.frame, text="seconds", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Consolas", 9)).pack()

        self.state_var = tk.StringVar(value="RED")
        self.state_label = tk.Label(self.frame, textvariable=self.state_var,
                                    bg=ACCENT_RED, fg=TEXT_WHITE,
                                    font=("Consolas", 10, "bold"),
                                    width=10, pady=4, anchor="center")
        self.state_label.pack(pady=6)

        # ── Emergency vehicle ALERT only (no count shown) ─────────────
        self.emergency_label = tk.Label(
            self.frame,
            text="🚨 EMERGENCY VEHICLE!",
            bg=BG_CARD,
            fg=BG_CARD,          # hidden by default (same as bg)
            font=("Consolas", 9, "bold"),
            height=1
        )
        self.emergency_label.pack()

        # ── Vehicle count grid — count only, no cap shown ─────────────
        count_frame = tk.Frame(self.frame, bg=BG_CARD)
        count_frame.pack(pady=(6, 2), padx=10, fill="x")

        hdr = tk.Frame(count_frame, bg=BG_CARD)
        hdr.pack(fill="x", pady=(0, 3))
        tk.Label(hdr, text="Vehicle", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Consolas", 8, "bold"), anchor="w", width=12).pack(side="left")
        tk.Label(hdr, text="Count", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Consolas", 8, "bold"), anchor="e").pack(side="right")

        self.count_vars = {}
        icons = {"cars": "🚗", "bikes": "🏍️", "buses": "🚌", "trucks": "🚛"}
        for vtype, icon in icons.items():
            row_f = tk.Frame(count_frame, bg=BG_CARD)
            row_f.pack(fill="x", pady=1)
            tk.Label(row_f, text=f"{icon} {vtype.capitalize()}:",
                     bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 9),
                     anchor="w", width=12).pack(side="left")
            self.count_vars[vtype] = tk.StringVar(value="0")
            tk.Label(row_f, textvariable=self.count_vars[vtype],
                     bg=BG_CARD, fg=ACCENT_BLUE, font=("Consolas", 9, "bold"),
                     anchor="e", width=5).pack(side="right")

        # Total row
        total_f = tk.Frame(count_frame, bg="#252D3A",
                           highlightthickness=1, highlightbackground="#3A4458")
        total_f.pack(fill="x", pady=(6, 0))
        tk.Label(total_f, text="📊 Total:",
                 bg="#252D3A", fg=TEXT_MUTED, font=("Consolas", 9, "bold"),
                 anchor="w", width=12).pack(side="left", padx=4, pady=3)
        self.total_var = tk.StringVar(value="0")
        tk.Label(total_f, textvariable=self.total_var,
                 bg="#252D3A", fg=ACCENT_GREEN, font=("Consolas", 9, "bold"),
                 anchor="e", width=5).pack(side="right", padx=4)

        # Score
        score_frame = tk.Frame(self.frame, bg=BG_CARD)
        score_frame.pack(fill="x", padx=10, pady=(8, 8))
        tk.Label(score_frame, text="Priority Score:",
                 bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 9)).pack(side="left")
        self.score_var = tk.StringVar(value="0.0")
        tk.Label(score_frame, textvariable=self.score_var,
                 bg=BG_CARD, fg=ACCENT_YELL, font=("Consolas", 9, "bold")).pack(side="right")

        self._last_state = None

    def _draw_light_housing(self):
        self.canvas.create_rectangle(5, 0, 65, 170, fill="#1a1a2e", outline="#444", width=2)

    def update(self, state_data):
        state       = state_data["state"]
        countdown   = state_data["countdown"]
        counts      = state_data["counts"]
        score       = state_data["score"]
        emergency   = state_data["emergency"]       # True for exactly one tick when EV arrives
        type_limits = state_data.get("type_limits", {})
        max_limit   = state_data.get("max_limit", 120)

        # ── Traffic light colours ──────────────────────────────────────
        if state != self._last_state:
            self._last_state = state
            self.canvas.itemconfig(self.red_light,    fill="#FF4444" if state == SignalState.RED    else "#3a1010")
            self.canvas.itemconfig(self.yellow_light, fill="#FFD700" if state == SignalState.YELLOW else "#3a3010")
            self.canvas.itemconfig(self.green_light,  fill="#44FF44" if state == SignalState.GREEN  else "#103a10")
            colors = {SignalState.GREEN: ACCENT_GREEN, SignalState.YELLOW: ACCENT_YELL, SignalState.RED: ACCENT_RED}
            self.state_label.config(bg=colors.get(state, ACCENT_RED))
            border = ACCENT_GREEN if state == SignalState.GREEN else (ACCENT_YELL if state == SignalState.YELLOW else BORDER_COLOR)
            self.frame.config(highlightbackground=border)

        # ── Countdown ─────────────────────────────────────────────────
        if state in (SignalState.GREEN, SignalState.YELLOW) and countdown > 0:
            self.countdown_var.set(str(countdown))
        else:
            self.countdown_var.set("--")
        self.state_var.set(state)

        # ── Emergency vehicle ALERT — show text only, NO count ─────────
        if emergency:
            self.emergency_label.config(fg="#FF6B6B", bg=EMERGENCY_BG)
            self.frame.config(bg=EMERGENCY_BG)
        else:
            self.emergency_label.config(fg=BG_CARD, bg=BG_CARD)
            self.frame.config(bg=BG_CARD)

        # ── Vehicle counts ─────────────────────────────────────────────
        for vtype, var in self.count_vars.items():
            count = counts.get(vtype, 0)
            var.set(str(count))

        self.total_var.set(str(counts.get("total", 0)))
        self.score_var.set(str(score))


# ─── Live Graph Panel ─────────────────────────────────────────────────────────

class GraphPanel:
    """Two live matplotlib charts embedded in a Tkinter frame."""

    def __init__(self, parent, road_names):
        self.road_names = road_names
        self.history    = {r: collections.deque([0] * MAX_HISTORY, maxlen=MAX_HISTORY) for r in road_names}
        self.state_map  = {SignalState.GREEN: 2, SignalState.YELLOW: 1, SignalState.RED: 0}
        self.sig_history= {r: collections.deque([0] * MAX_HISTORY, maxlen=MAX_HISTORY) for r in road_names}
        self._tick      = 0

        outer = tk.Frame(parent, bg=BG_PANEL,
                         highlightthickness=1, highlightbackground=BORDER_COLOR)
        outer.pack(fill="x", padx=16, pady=(0, 16))

        tk.Label(outer, text="📈  Live Traffic Analytics",
                 bg=BG_PANEL, fg=TEXT_PRIMARY,
                 font=("Consolas", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 4))

        self.fig = Figure(figsize=(11, 5), dpi=96, facecolor="#0D1117")
        self.fig.subplots_adjust(left=0.07, right=0.97, top=0.88, bottom=0.12, wspace=0.3)

        # Graph 1 — total vehicles per road over time
        self.ax1 = self.fig.add_subplot(1, 2, 1)
        self.ax1.set_facecolor("#161B22")
        self.ax1.set_title("Total Vehicles per Road (last 60 ticks)",
                           color=TEXT_PRIMARY, fontsize=9, pad=6)
        self.ax1.tick_params(colors=TEXT_MUTED, labelsize=7)
        self.ax1.set_xlabel("Ticks ago", color=TEXT_MUTED, fontsize=8)
        self.ax1.set_ylabel("Vehicles", color=TEXT_MUTED, fontsize=8)
        for sp in self.ax1.spines.values():
            sp.set_color(BORDER_COLOR)
        self.ax1.grid(True, color="#2A3040", linewidth=0.5, linestyle="--")

        self.lines1 = {}
        xs = list(range(-MAX_HISTORY + 1, 1))
        for i, road in enumerate(road_names):
            line, = self.ax1.plot(xs, [0]*MAX_HISTORY,
                                  color=ROAD_COLORS[i % len(ROAD_COLORS)],
                                  linewidth=1.6, label=road.capitalize())
            self.lines1[road] = line
        self.ax1.legend(loc="upper left", fontsize=7,
                        facecolor=BG_CARD, edgecolor=BORDER_COLOR,
                        labelcolor=TEXT_PRIMARY)

        # Graph 2 — signal state per road over time
        self.ax2 = self.fig.add_subplot(1, 2, 2)
        self.ax2.set_facecolor("#161B22")
        self.ax2.set_title("Signal State per Road (last 60 ticks)",
                           color=TEXT_PRIMARY, fontsize=9, pad=6)
        self.ax2.tick_params(colors=TEXT_MUTED, labelsize=7)
        self.ax2.set_xlabel("Ticks ago", color=TEXT_MUTED, fontsize=8)
        self.ax2.set_ylabel("State", color=TEXT_MUTED, fontsize=8)
        self.ax2.set_yticks([0, 1, 2])
        self.ax2.set_yticklabels(["RED", "YELLOW", "GREEN"],
                                 color=TEXT_MUTED, fontsize=7)
        self.ax2.set_ylim(-0.3, 2.5)
        for sp in self.ax2.spines.values():
            sp.set_color(BORDER_COLOR)
        self.ax2.grid(True, color="#2A3040", linewidth=0.5, linestyle="--")

        self.lines2 = {}
        for i, road in enumerate(road_names):
            line, = self.ax2.plot(xs, [0]*MAX_HISTORY,
                                  color=ROAD_COLORS[i % len(ROAD_COLORS)],
                                  linewidth=1.8, label=road.capitalize(),
                                  drawstyle="steps-post")
            self.lines2[road] = line
        self.ax2.legend(loc="upper left", fontsize=7,
                        facecolor=BG_CARD, edgecolor=BORDER_COLOR,
                        labelcolor=TEXT_PRIMARY)

        self.mpl_canvas = FigureCanvasTkAgg(self.fig, master=outer)
        self.mpl_canvas.draw()
        self.mpl_canvas.get_tk_widget().pack(fill="x", padx=8, pady=(0, 10))

    def update(self, states):
        self._tick += 1
        xs = list(range(-MAX_HISTORY + 1, 1))

        for road in self.road_names:
            if road in states:
                total = states[road]["counts"].get("total", 0)
                sig   = self.state_map.get(states[road]["state"], 0)
                self.history[road].append(total)
                self.sig_history[road].append(sig)

            self.lines1[road].set_data(xs, list(self.history[road]))
            self.lines2[road].set_data(xs, list(self.sig_history[road]))

        all_vals = [v for road in self.road_names for v in self.history[road]]
        if all_vals:
            lo = max(0, min(all_vals) - 2)
            hi = max(all_vals) + 5
            self.ax1.set_ylim(lo, hi)

        self.mpl_canvas.draw_idle()


# ─── Main GUI ─────────────────────────────────────────────────────────────────

class TrafficGUI:
    def __init__(self, root, controller):
        self.root       = root
        self.controller = controller
        self.interval   = CONFIG["simulation_interval"]
        self._build_ui()

    def _build_ui(self):
        self.root.title("🚦 AI Smart Traffic Control System")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("1100x820")
        self.root.resizable(True, True)

        # ── Fixed header ────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=ACCENT_BLUE, pady=12)
        header.pack(fill="x", side="top")
        tk.Label(header, text="🚦  AI-Based Smart Traffic Congestion Control System",
                 bg=ACCENT_BLUE, fg=TEXT_WHITE,
                 font=("Consolas", 15, "bold")).pack()
        tk.Label(header, text="A.G. Patil Institute of Technology, Solapur  |  Real-Time Signal Controller",
                 bg=ACCENT_BLUE, fg="#A8C8FF",
                 font=("Consolas", 9)).pack()

        # ── Scrollable body ─────────────────────────────────────────────
        body_outer = tk.Frame(self.root, bg=BG_DARK)
        body_outer.pack(fill="both", expand=True, side="top")

        self._vscroll = tk.Scrollbar(body_outer, orient="vertical")
        self._vscroll.pack(side="right", fill="y")

        self._scroll_canvas = tk.Canvas(body_outer, bg=BG_DARK,
                                        yscrollcommand=self._vscroll.set,
                                        highlightthickness=0)
        self._scroll_canvas.pack(side="left", fill="both", expand=True)
        self._vscroll.config(command=self._scroll_canvas.yview)

        self._inner = tk.Frame(self._scroll_canvas, bg=BG_DARK)
        self._inner_id = self._scroll_canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )

        def _on_inner_configure(event):
            self._scroll_canvas.configure(
                scrollregion=self._scroll_canvas.bbox("all")
            )

        def _on_canvas_configure(event):
            self._scroll_canvas.itemconfig(self._inner_id, width=event.width)

        self._inner.bind("<Configure>", _on_inner_configure)
        self._scroll_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self._scroll_canvas.bind_all("<Button-4>",
            lambda e: self._scroll_canvas.yview_scroll(-1, "units"))
        self._scroll_canvas.bind_all("<Button-5>",
            lambda e: self._scroll_canvas.yview_scroll(1, "units"))

        # ── Road Cards ──────────────────────────────────────────────────
        cards_frame = tk.Frame(self._inner, bg=BG_DARK)
        cards_frame.pack(fill="x", padx=16, pady=12)

        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)
        cards_frame.rowconfigure(0, weight=1)

        self.road_cards = {}
        for i, road in enumerate(CONFIG["road_names"]):
            card = RoadCard(cards_frame, road, i)
            self.road_cards[road] = card

        # ── Status Bar ──────────────────────────────────────────────────
        status_frame = tk.Frame(self._inner, bg=BG_PANEL, pady=8,
                                highlightthickness=1, highlightbackground=BORDER_COLOR)
        status_frame.pack(fill="x", padx=16, pady=(0, 6))

        self.stats_vars = {
            "cycle":     tk.StringVar(value="Cycles: 0"),
            "vehicles":  tk.StringVar(value="Vehicles Cleared: 0"),
            "green":     tk.StringVar(value="Active Green: --"),
            "emergency": tk.StringVar(value="🚨 EV: 0 / 5"),
            "status":    tk.StringVar(value="🟢 System Running"),
        }

        for key, var in self.stats_vars.items():
            color = ACCENT_GREEN if key == "status" else (ACCENT_RED if key == "emergency" else TEXT_MUTED)
            tk.Label(status_frame, textvariable=var, bg=BG_PANEL, fg=color,
                     font=("Consolas", 9)).pack(side="left", padx=16)

        # ── Legend ──────────────────────────────────────────────────────
        legend = tk.Frame(self._inner, bg=BG_DARK)
        legend.pack(pady=(0, 10))
        for color, label in [
            (ACCENT_GREEN,  "GREEN – Go"),
            (ACCENT_YELL,   "YELLOW – Caution"),
            (ACCENT_RED,    "RED – Stop"),
            ("#FF6B6B",     "🚨 Emergency Vehicle Alert"),
        ]:
            tk.Label(legend, text="●", bg=BG_DARK, fg=color,
                     font=("Consolas", 12)).pack(side="left", padx=4)
            tk.Label(legend, text=label, bg=BG_DARK, fg=TEXT_MUTED,
                     font=("Consolas", 9)).pack(side="left", padx=(0, 12))

        # ── Two live graphs ──────────────────────────────────────────────
        self.graph_panel = GraphPanel(self._inner, CONFIG["road_names"])

    def start(self):
        self._update()

    def _update(self):
        states = self.controller.tick()

        for road, card in self.road_cards.items():
            if road in states:
                card.update(states[road])

        self.graph_panel.update(states)

        sys_stats = self.controller.get_stats()
        self.stats_vars["cycle"].set(f"Cycles: {sys_stats['cycle_count']}")
        self.stats_vars["vehicles"].set(f"Vehicles Cleared: {sys_stats['total_vehicles']}")
        self.stats_vars["green"].set(f"Active Green: {sys_stats['current_green']}")
        self.stats_vars["emergency"].set(
            f"🚨 EV: {sys_stats['ev_spawned']} / {sys_stats['ev_max']}"
        )

        self.root.after(self.interval, self._update)
