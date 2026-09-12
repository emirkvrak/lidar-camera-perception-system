
DEFAULT_ROADS_JSON = {
    "roads": [
        {
            "name": "Road1",
            "visible": True,
            "type": "both",          # incoming | outgoing | both
            "lane_width": 3.75,
            "color": "#2600FF",
            "incoming": {
                "count": 1
            },
            "outgoing": {
                "count": 1
            }
        }
    ]
}


DEFAULT_MARKERS_JSON = {
    "markers": [
        {
            "name": "marker_1",
            "visible": True,
            "position": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0
            },
            "size": {
                "width": 0.3,
                "height": 0.75
            },
            "color": "#FF000D"
        }
    ]
}


DEFAULT_CAMERAS_JSON = {
    "cameras": [
        {
            "name": "CAM_1",
            "extrinsic": {
                "x": 0.0,
                "y": 1.5,
                "z": 0.0,
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0
            },
            "intrinsic": {
                "fx": 1000.0,
                "fy": 1000.0,
                "cx": 640.0,
                "cy": 360.0,
                "k1": 0.0,
                "k2": 0.0,
                "k3": 0.0,
                "p1": 0.0,
                "p2": 0.0
            }
        }
    ]
}

DEFAULT_LIDARS_JSON = {
    "lidars": [
        {
            "name": "lidar1",
            "visible": True,
            "extrinsic": {
                "x": -3.0,
                "y": 1.7,
                "z": 0.0,
                "yaw": -13.0,
                "pitch": 10.0,
                "roll": 0.0
            }
        }
    ]
}
