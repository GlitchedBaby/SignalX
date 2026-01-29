import cv2
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import sounddevice as sd

import config as C
from vision.yolo_world_detector import YOLOWorldDetector
from audio.siren_infer import SirenInfer
from audio.mic_worker import MicWorker, list_mics
from logic.controller import FlowHoldController

EMERGENCY_LATCH_SEC = C.EMERGENCY_LATCH_SEC



# -----------------------------
# Helpers
# -----------------------------
def compute_signals(n, ph):
    signals = ["RED"] * n
    state = ph.get("state", "")
    g = ph.get("green_idx", None)
    y = ph.get("yellow_idx", None)

    if state == "ALL_YELLOW":
        return ["YELLOW"] * n

    if state == "GREEN" and g is not None and 0 <= g < n:
        signals[g] = "GREEN"
    elif state == "YELLOW" and y is not None and 0 <= y < n:
        signals[y] = "YELLOW"
    return signals



def probe_cameras(max_index=8):
    ok_list = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                ok_list.append(i)
        cap.release()
    return ok_list


def list_input_mics():
    devices = sd.query_devices()
    res = []
    for idx, d in enumerate(devices):
        if d.get("max_input_channels", 0) > 0:
            name = d["name"].lower()
            if "vb-audio" in name or "cable" in name or "steam" in name:
                continue
            res.append((idx, d["name"]))
    return res



def draw_signal_light(frame, state: str):
    x, y = 40, 170
    r = 12
    gap = 30
    cv2.circle(frame, (x, y), r, (0, 0, 255) if state == "RED" else (40, 40, 40), -1)
    cv2.circle(frame, (x, y + gap), r, (0, 255, 255) if state == "YELLOW" else (40, 40, 40), -1)
    cv2.circle(frame, (x, y + 2 * gap), r, (0, 255, 0) if state == "GREEN" else (40, 40, 40), -1)


def draw_sound_meter(frame, db, x=20, y=220, w=260, h=16):
    """
    db approx: -80 (quiet) to -10 (loud)
    """
    db_min, db_max = -80.0, -10.0
    db_c = max(db_min, min(db_max, float(db)))
    frac = (db_c - db_min) / (db_max - db_min)

    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 1)
    fill_w = int(w * frac)
    cv2.rectangle(frame, (x, y), (x + fill_w, y + h), (0, 255, 255), -1)

    cv2.putText(frame, f"Audio {db:.1f} dB", (x, y - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)


def setup_cap(cam_index: int):
    cap = cv2.VideoCapture(cam_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, C.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, C.FRAME_HEIGHT)
    return cap


# -----------------------------
# Popup UI
# -----------------------------
def setup_popup(default_n=2):
    cams = probe_cameras(8)
    mics = list_input_mics()

    if not cams:
        raise RuntimeError("No cameras found. Check camera indexes / drivers.")
    if not mics:
        raise RuntimeError("No input microphones found.")

    root = tk.Tk()
    root.title("Intersection Setup (Cams + Mics)")
    root.geometry("900x420")
    root.resizable(False, False)

    info = tk.Label(
        root,
        text=(
            "Select which Camera + Microphone belongs to each Approach.\n"
            "Rotation is circular.\n"
            "Emergency: mic siren triggers preemption."
        ),
        justify="left"
    )
    info.pack(pady=10)

    top_frame = tk.Frame(root)
    top_frame.pack(pady=5, fill="x")
    tk.Label(top_frame, text="Number of Approaches (2-4):").pack(side="left", padx=10)

    n_var = tk.IntVar(value=max(2, min(4, default_n)))
    n_box = ttk.Combobox(top_frame, textvariable=n_var, values=[2, 3, 4], state="readonly", width=6)
    n_box.pack(side="left")

    table = tk.Frame(root)
    table.pack(pady=10)

    tk.Label(table, text="Approach").grid(row=0, column=0, padx=8)
    tk.Label(table, text="Name").grid(row=0, column=1, padx=8)
    tk.Label(table, text="Camera Index").grid(row=0, column=2, padx=8)
    tk.Label(table, text="Mic Device").grid(row=0, column=3, padx=8)

    cam_values = cams
    mic_values = [f"{idx}: {name}" for idx, name in mics]

    row_widgets = []
    result = {"approaches": None}

    def rebuild_rows(*_):
        for row in row_widgets:
            for w in row["widgets"]:
                w.destroy()
        row_widgets.clear()

        n = int(n_var.get())
        for i in range(n):
            lbl = tk.Label(table, text=f"A{i+1}")
            lbl.grid(row=i+1, column=0, padx=8, pady=6)

            name_var = tk.StringVar(value=f"CAM{i+1}")
            ent = tk.Entry(table, textvariable=name_var, width=18)
            ent.grid(row=i+1, column=1, padx=8)

            cam_var = tk.IntVar(value=cam_values[i] if i < len(cam_values) else cam_values[0])
            cam_box = ttk.Combobox(table, textvariable=cam_var, values=cam_values, state="readonly", width=12)
            cam_box.grid(row=i+1, column=2, padx=8)

            mic_var = tk.StringVar(value=mic_values[i] if i < len(mic_values) else mic_values[0])
            mic_box = ttk.Combobox(table, textvariable=mic_var, values=mic_values, state="readonly", width=55)
            mic_box.grid(row=i+1, column=3, padx=8)

            row_widgets.append({
                "widgets": [lbl, ent, cam_box, mic_box],
                "name_var": name_var,
                "cam_var": cam_var,
                "mic_var": mic_var
            })

    def on_start():
        n = int(n_var.get())
        chosen = []
    
        used_cams = set()
        used_mics = set()
    
        if len(row_widgets) < n:
            messagebox.showerror(
                "Setup Error",
                "Rows not built. Change approach count again and press START."
            )
            return
    
        for i in range(n):
            row = row_widgets[i]
    
            name = row["name_var"].get().strip() or f"CAM{i+1}"
    
            cam_index = int(row["cam_var"].get())
            if cam_index in used_cams:
                messagebox.showerror(
                    "Setup Error",
                    f"Camera index {cam_index} is used twice. Pick unique cameras."
                )
                return
            used_cams.add(cam_index)
    
            mic_str = row["mic_var"].get()          
            mic_id = int(mic_str.split(":")[0])    
    
            if mic_id in used_mics:
                messagebox.showerror(
                    "Setup Error",
                    f"Microphone device {mic_id} is used twice. Use different mics."
                )
                return
            used_mics.add(mic_id)
    
            chosen.append({
                "name": name,
                "cam_index": cam_index,
                "mic_device": mic_id,
                "roi": (0, 0, C.FRAME_WIDTH, C.FRAME_HEIGHT),
            })
    
        result["approaches"] = chosen
        root.destroy()


    def on_cancel():
        result["approaches"] = None
        root.destroy()

    rebuild_rows()
    n_box.bind("<<ComboboxSelected>>", rebuild_rows)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=12)
    tk.Button(btn_frame, text="START", command=on_start, width=18, height=2).pack(side="left", padx=10)
    tk.Button(btn_frame, text="CANCEL", command=on_cancel, width=18, height=2).pack(side="left", padx=10)

    root.mainloop()

    if not result["approaches"]:
        raise RuntimeError("Setup cancelled.")
    return result["approaches"]


# -----------------------------
# Main
# -----------------------------
def main():
    list_mics()

    approaches = setup_popup(default_n=2)
    n = len(approaches)

    det = YOLOWorldDetector(C.YOLO_WORLD_WEIGHTS, C.PROMPTS, C.CONF, C.IOU)
    siren = SirenInfer(C.SIREN_MODEL_PATH, sr=C.AUDIO_SR)

    caps = []
    mic_workers = []
    for ap in approaches:
        caps.append(setup_cap(ap["cam_index"]))

        mw = MicWorker(
            device_id=ap["mic_device"],
            infer=siren,
            window_sec=C.AUDIO_WINDOW_SEC,
            sr=C.AUDIO_SR,
            threshold=C.SIREN_CONF_THRESHOLD,
            consecutive_needed=C.SIREN_CONSECUTIVE_HITS
        )
        mic_workers.append(mw)
        threading.Thread(target=mw.run_loop, daemon=True).start()

    ctrl = FlowHoldController(
        n=n,
        yellow=3,
        all_red=2,
        base_green=10,
        extend_step=10,
        max_green=90,
        emergency_all_red_sec=C.EMERGENCY_ALL_RED_SEC,
        emergency_release_delay_sec=C.EMERGENCY_RELEASE_DELAY_SEC,
    )


    em_latch_until = [0.0] * n
    last_print = 0.0

    while True:
        frames = [None] * n
        counts = [0] * n

        for i in range(n):
            ok, frame = caps[i].read()
            if not ok or frame is None:
                continue

            out_frame, count, labels = det.detect_and_plot(frame, approaches[i]["roi"])
            frames[i] = out_frame
            counts[i] = int(count)

        now = time.time()
        for i, mw in enumerate(mic_workers):
            if mw.state.triggered:
                em_latch_until[i] = max(em_latch_until[i], now + EMERGENCY_LATCH_SEC)

        emergency_idxs = [i for i in range(n) if now < em_latch_until[i]]

        ph = ctrl.tick(counts, emergency_idxs)

        signals = compute_signals(n, ph)

        if now - last_print > 1.0:
            mic_status = " | ".join(
                f"{approaches[i]['name']}:{mic_workers[i].state.label}:{mic_workers[i].state.conf:.2f}"
                f"(trig={mic_workers[i].state.triggered}, db={mic_workers[i].state.db:.1f}, latch={(em_latch_until[i]-now):.1f}s)"
                for i in range(n)
            )
            print(
                f"[{time.strftime('%H:%M:%S')}] counts={counts} emergency={emergency_idxs} | {mic_status} => "
                f"CTRL={ph.get('state')} green_idx={ph.get('green_idx')} yellow_idx={ph.get('yellow_idx')} "
                f"left={ph.get('remaining',0):.1f}s tag={ph.get('tag','NORMAL')}"
            )
            last_print = now

        if C.SHOW_WINDOWS:
            for i in range(n):
                frame = frames[i]
                if frame is None:
                    continue

                x1, y1, x2, y2 = approaches[i]["roi"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

                draw_signal_light(frame, signals[i])

                cv2.putText(frame,
                            f"{approaches[i]['name']} | vehicles={counts[i]} | SIGNAL={signals[i]}",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                cv2.putText(frame,
                            f"Mic={mic_workers[i].state.label}:{mic_workers[i].state.conf:.2f} "
                            f"trig={mic_workers[i].state.triggered}",
                            (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                cv2.putText(frame,
                            f"CTRL={ph.get('state')} green_idx={ph.get('green_idx')} yellow_idx={ph.get('yellow_idx')} "
                            f"left={ph.get('remaining',0):.1f}s tag={ph.get('tag','NORMAL')}",
                            (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

                draw_sound_meter(frame, mic_workers[i].state.db, x=20, y=150, w=260, h=16)

                cv2.imshow(f"Approach {i+1} - {approaches[i]['name']}", frame)

        key = cv2.waitKey(1)
        if key == 27:
            break

    for mw in mic_workers:
        mw.stop()
    for cap in caps:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
