from dataclasses import dataclass
from typing import List
import numpy as np
import numpy.typing as npt

@dataclass
class Cluster:
    @dataclass
    class PhotonCount:
        sum: float
        mean: float
        max: float
        min: float

    @dataclass
    class Cartesian:
        weighted: npt.NDArray[np.float64]
        min: npt.NDArray[np.float64]
        max: npt.NDArray[np.float64]
        mean: npt.NDArray[np.float64]

    photon_count: PhotonCount
    cartesian: Cartesian
    volume: float
    size: npt.NDArray[np.float64]
    boundaries: npt.NDArray[np.float64]

@dataclass
class A2DetectionResult:
    unique_id: str
    license_plate: str
    location: List[float]
    confidence_score: float
    color: str
    brand: str
    type: str