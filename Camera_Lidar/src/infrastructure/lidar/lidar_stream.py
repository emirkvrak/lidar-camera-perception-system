import struct
import numpy as np
from typing import Iterator, Tuple, Dict, Any

FRAME_HEADER_FMT = "<I"
RUNTIME_FMT = "<f"
POINT_FMT = "<fffII"
POINT_SIZE = struct.calcsize(POINT_FMT)


def decode_lidar_stream(
    file_path: str,
    start_timestamp: float = 0.0,
    end_timestamp: float = float("inf")
) -> Iterator[Tuple[float, Dict[str, Any]]]:

    with open(file_path, "rb") as f:
        while True:
            header = f.read(struct.calcsize(FRAME_HEADER_FMT))
            if not header:
                break

            (chunk_length,) = struct.unpack(FRAME_HEADER_FMT, header)
            chunk = f.read(chunk_length)

            runtime = struct.unpack_from(RUNTIME_FMT, chunk, 0)[0]
            if runtime < start_timestamp:
                continue
            if runtime > end_timestamp:
                break

            data = chunk[struct.calcsize(RUNTIME_FMT):]
            n_points = len(data) // POINT_SIZE

            points = np.frombuffer(
                data,
                dtype=np.dtype([
                    ("x", "<f4"),
                    ("y", "<f4"),
                    ("z", "<f4"),
                    ("photon_count", "<u4"),
                    ("direction_id", "<u4"),
                ]),
                count=n_points
            )

            cartesian = np.column_stack(
                (points["x"], points["y"], points["z"])
            )

            yield runtime, {
                "cartesian": cartesian,
                "photon_count": points["photon_count"],
                "direction_id": points["direction_id"],
            }
