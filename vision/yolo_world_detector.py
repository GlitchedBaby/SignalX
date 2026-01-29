import cv2
from ultralytics import YOLO

VEHICLE_LABELS = {
    "car", "truck", "bus", "bicycle", "motorcycle", "motorbike",
    "auto rickshaw", "autorickshaw", "ambulance", "fire truck", "firetruck",
    "handcart", "vehicle"
}

class YOLOWorldDetector:
    def __init__(self, weights, prompts, conf, iou):
        self.model = YOLO(weights)
        self.model.set_classes(prompts)
        self.conf = conf
        self.iou = iou

    @staticmethod
    def crop_roi(frame, roi):
        x1, y1, x2, y2 = roi
        x1 = max(0, int(x1)); y1 = max(0, int(y1))
        x2 = min(frame.shape[1], int(x2)); y2 = min(frame.shape[0], int(y2))
        return frame[y1:y2, x1:x2], (x1, y1, x2, y2)

    def detect_and_plot(self, frame, roi):
        roi_img, (x1, y1, x2, y2) = self.crop_roi(frame, roi)

        if roi_img.size == 0:
            return frame, 0, {}

        res = self.model.predict(
            roi_img,
            imgsz=640,
            conf=self.conf,
            iou=self.iou,
            verbose=False
        )[0]

        roi_plot = res.plot()
        out = frame.copy()
        out[y1:y2, x1:x2] = roi_plot

        vehicle_count = 0
        label_hist = {}

        if res.boxes is not None and len(res.boxes) > 0:
            names = res.names
            for b in res.boxes:
                cls_id = int(b.cls)
                label = names.get(cls_id, str(cls_id)).lower().strip()
                label_hist[label] = label_hist.get(label, 0) + 1
                if label in VEHICLE_LABELS and label != "person":
                    vehicle_count += 1

        return out, vehicle_count, label_hist
