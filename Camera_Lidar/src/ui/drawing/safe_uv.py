import numpy as np
from typing import Optional, Dict, Any

def safe_scalar(x):
    if x is None:
        return None
    if isinstance(x, (list, tuple, np.ndarray)):
        try:
            return float(x[0])
        except Exception:
            return None
    try:
        return float(x)
    except Exception:
        return None

def safe_get_uv(cam_result: Optional[Dict[str, Any]]):
    if cam_result is None or not cam_result.get("visible", False):
        return None

    u = safe_scalar(cam_result.get("u"))
    v = safe_scalar(cam_result.get("v"))
    if u is None or v is None:
        return None


    return int(u), int(v)
