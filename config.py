# =========================
# INTERSECTION DEMO CONFIG
# Multi-approach (N sides)
# =========================

# -----------------------
# VIDEO
# -----------------------
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# If you only have 2 cameras, define 2 approaches (2 sides).
# Each approach maps:
# - name: side name
# - cam_index: OpenCV camera index
# - mic_device: sounddevice device id (use the list printed at startup)
# - roi: rectangle for counting (x1, y1, x2, y2)
#
# NOTE: If you later add more cameras, just append more dicts.
APPROACHES = [
    {
        "name": "CAM1_SIDE",     
        "cam_index": 0,
        "mic_device": 1,
        "roi": (200, 200, 1200, 700),
    },
    {
        "name": "CAM2_SIDE",     
        "cam_index": 1,
        "mic_device": 2,
        "roi": (200, 200, 1200, 700),
    },
]

# -----------------------
# OPEN-VOCAB DETECTION (YOLO-World)
# -----------------------
PROMPTS = [
    "car", "motorcycle", "bus", "truck", "bicycle",
    "person",
    "auto rickshaw", "ambulance", "fire truck",
    "cow", "dog", "handcart"
]

YOLO_WORLD_WEIGHTS = "yolov8s-world.pt"

CONF = 0.10
IOU = 0.50

for a in APPROACHES:
    a["roi"] = (0, 0, FRAME_WIDTH, FRAME_HEIGHT)


# -----------------------
# AUDIO / SIREN
# -----------------------
SIREN_MODEL_PATH = r"models\siredetect_pro.h5"
AUDIO_SR = 48000
AUDIO_WINDOW_SEC = 3


SIREN_CONF_THRESHOLD = 0.85
SIREN_CONSECUTIVE_HITS = 2 

# -----------------------
# SIGNAL CONTROL (ADVANCED ROTATIONAL FSM)
# -----------------------
MIN_GREEN = 8
MAX_GREEN = 60

YELLOW = 3        
ALL_RED = 2      

COUNT_TO_SECONDS = 2.0

SMOOTHING_ALPHA = 0.6

MAX_WAIT = 90         
MIN_SWITCH_GAP = 5    

EMERGENCY_GREEN = 45      
EMERGENCY_COOLDOWN = 20   

# -----------------------
# VISUAL
# -----------------------
SHOW_WINDOWS = True

MIN_RED = 6
CYCLE_CAP = 120

EMERGENCY_LATCH_SEC = 6.0             
EMERGENCY_RELEASE_DELAY_SEC = 3.0     
EMERGENCY_ALL_RED_SEC = 2.0           

EMERGENCY_YELLOW_SEC = 2.0    
EMERGENCY_ALL_RED_SEC = 1.0    
EMERGENCY_RELEASE_DELAY_SEC = 3.0  
EMERGENCY_LATCH_SEC = 6.0      
