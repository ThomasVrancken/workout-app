import os
import sys
import requests
from datetime import datetime, timezone

API_BASE = "https://api.hevyapp.com"


def get_api_key():
    key = os.environ.get("HEVY_API_KEY")
    if not key:
        print("Error: HEVY_API_KEY environment variable not set.")
        print("Get your key at https://hevy.com/settings?developer")
        sys.exit(1)
    return key


def fetch_latest_workout(api_key: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/v1/workouts",
        headers={"api-key": api_key},
        params={"page": 1, "pageSize": 1},
    )
    resp.raise_for_status()
    data = resp.json()
    workouts = data.get("workouts", [])
    if not workouts:
        print("No workouts found on your account.")
        sys.exit(0)
    return workouts[0]


def format_duration(start_iso: str, end_iso: str) -> str:
    start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    delta = end - start
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def format_set(s: dict) -> str:
    parts = []
    set_type = s.get("type", "normal")
    if set_type != "normal":
        parts.append(f"[{set_type}]")

    weight = s.get("weight_kg")
    reps = s.get("reps")
    distance = s.get("distance_meters")
    duration = s.get("duration_seconds")
    rpe = s.get("rpe")
    custom = s.get("custom_metric")

    if weight is not None:
        parts.append(f"{weight} kg")
    if reps is not None:
        parts.append(f"x {reps} reps")
    if distance is not None:
        parts.append(f"{distance} m")
    if duration is not None:
        parts.append(f"{duration} s")
    if rpe is not None:
        parts.append(f"(RPE {rpe})")
    if custom is not None:
        parts.append(f"(custom: {custom})")

    return " ".join(parts) if parts else "—"


def print_workout(workout: dict):
    title = workout.get("title", "Untitled Workout")
    description = workout.get("description", "")
    start = workout.get("start_time", "")
    end = workout.get("end_time", "")

    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    local_start = start_dt.astimezone()

    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print(f"  Date     : {local_start.strftime('%A, %B %d %Y')}")
    print(f"  Time     : {local_start.strftime('%H:%M')} ({format_duration(start, end)})")
    if description:
        print(f"  Notes    : {description}")
    print("-" * 60)

    exercises = workout.get("exercises", [])
    if not exercises:
        print("  No exercises recorded.")
        return

    total_sets = 0
    total_volume_kg = 0.0

    for ex in exercises:
        idx = ex.get("index", 0) + 1
        ex_title = ex.get("title", "Unknown Exercise")
        notes = ex.get("notes", "")
        sets = ex.get("sets", [])

        print(f"\n  {idx}. {ex_title}")
        if notes:
            print(f"     Note: {notes}")

        for s in sets:
            set_idx = s.get("index", 0) + 1
            print(f"     Set {set_idx}: {format_set(s)}")
            total_sets += 1
            w = s.get("weight_kg")
            r = s.get("reps")
            if w is not None and r is not None:
                total_volume_kg += w * r

    print()
    print("-" * 60)
    print(f"  Total exercises : {len(exercises)}")
    print(f"  Total sets      : {total_sets}")
    if total_volume_kg > 0:
        print(f"  Total volume    : {total_volume_kg:,.0f} kg")
    print("=" * 60)


def main():
    api_key = get_api_key()
    print("Fetching your latest workout from Hevy...\n")
    workout = fetch_latest_workout(api_key)
    print_workout(workout)


if __name__ == "__main__":
    main()
