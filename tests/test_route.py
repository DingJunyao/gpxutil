from datetime import datetime, timezone
import csv

import gpxpy.gpx
import pytest

from src.gpxutil.models.route import Route, RoutePoint


def test_from_gpx_obj_keeps_points_with_duplicate_time():
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    recorded_at = datetime(2026, 8, 30, 2, 50, 4, tzinfo=timezone.utc)

    gpx_segment.points = [
        gpxpy.gpx.GPXTrackPoint(
            latitude=-7.927668,
            longitude=112.954775,
            elevation=2138,
            time=recorded_at,
        ),
        gpxpy.gpx.GPXTrackPoint(
            latitude=-7.927712,
            longitude=112.954786,
            elevation=2133,
            time=recorded_at,
        ),
        gpxpy.gpx.GPXTrackPoint(
            latitude=-7.927736,
            longitude=112.954829,
            elevation=2134,
            time=recorded_at.replace(second=14),
        ),
    ]
    gpx_track.segments.append(gpx_segment)
    gpx.tracks.append(gpx_track)

    route = Route.from_gpx_obj(gpx)

    assert [point.index for point in route.points] == [0, 1, 2]
    assert [point.time for point in route.points] == [
        recorded_at,
        recorded_at,
        recorded_at.replace(second=14),
    ]
    assert route.points[1].speed == pytest.approx(
        gpx_segment.points[1].distance_3d(gpx_segment.points[2]) / 10
    )


def test_to_csv_fills_missing_speeds(tmp_path):
    route = Route(points=[
        RoutePoint(index=0, speed=None),
        RoutePoint(index=1, speed=12.34),
        RoutePoint(index=2, speed=None),
    ])
    csv_path = tmp_path / 'speeds.csv'

    route.to_csv(str(csv_path))

    with open(csv_path, encoding='utf-8-sig', newline='') as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert [float(row['speed']) for row in rows] == [0.0, 12.34, 12.34]
    assert [point.speed for point in route.points] == [None, 12.34, None]
