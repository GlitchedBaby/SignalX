import numpy as np

class SirenInfer:
    """
    BYPASS MODE
    -----------
    Siren detection is disabled.
    Always returns 'traffic' with 0 confidence.
    """

    def __init__(self, model_path: str | None = None, sr: int = 16000):
        self.sr = sr

    def predict(self, audio: np.ndarray):
        return "traffic", 0.0
