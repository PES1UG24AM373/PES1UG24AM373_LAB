"""Conference room and equipment scheduler.

Books rooms for time slots, allocates equipment such as projectors and
webcams, logs double bookings and exports the schedule to JSON.
"""
import itertools
import json
from collections import Counter
from datetime import datetime

# Shared state (mutated in place, never rebound, so no `global` is needed)
reservations = {}
equipment_pool = {"projector": 2, "microphone": 4, "webcam": 1}
conflicts = []
_RESERVATION_IDS = itertools.count(1)


def parse_slot(time_slot):
    """Return (start, end) hours for a slot written like '09-11'.

    Raises ValueError unless the slot is a string 'HH-HH' with
    0 <= start < end <= 24.
    """
    if not isinstance(time_slot, str):
        raise ValueError(f"slot must look like '09-11', got {time_slot!r}")
    try:
        start, end = (int(part) for part in time_slot.split("-"))
    except ValueError as exc:
        raise ValueError(
            f"slot must look like '09-11', got {time_slot!r}") from exc
    if not 0 <= start < end <= 24:
        raise ValueError(f"slot {time_slot!r} needs 0 <= start < end <= 24")
    return start, end


def slot_hours(time_slot):
    """Return the length in hours of a slot written like '09-11'."""
    start, end = parse_slot(time_slot)
    return end - start


def schedule_room(room_id, time_slot, equipment_list=None):
    """Book a room for a slot and reserve equipment.

    Overlapping bookings of the same room are still accepted but are
    recorded in `conflicts`. Raises ValueError, changing nothing, if the
    slot is invalid or the equipment is unknown or not in stock.
    Returns the new reservation id.
    """
    start, end = parse_slot(time_slot)
    equipment_list = list(equipment_list or [])
    for item, needed in Counter(equipment_list).items():
        if item not in equipment_pool:
            raise ValueError(f"unknown equipment {item!r}")
        if equipment_pool[item] < needed:
            raise ValueError(
                f"not enough {item}: need {needed}, "
                f"{equipment_pool[item]} available")
    for reservation in reservations.values():
        other_start, other_end = parse_slot(reservation["slot"])
        if (reservation["room"] == room_id
                and start < other_end and other_start < end):
            conflicts.append(
                f"{room_id} double-booked at {time_slot} "
                f"(overlaps {reservation['slot']})")
    for item in equipment_list:
        equipment_pool[item] -= 1
    reservation_id = next(_RESERVATION_IDS)
    reservations[reservation_id] = {
        "room": room_id, "slot": time_slot, "equipment": equipment_list}
    return reservation_id


def cancel_reservation(reservation_id):
    """Cancel a reservation and return its equipment to the pool."""
    reservation = reservations.pop(reservation_id, None)
    if reservation is None:
        print(f"No reservation with id {reservation_id} to cancel")
        return
    for e in reservation["equipment"]:
        equipment_pool[e] += 1


def export_schedule(file="schedule.json"):
    """Write all reservations to a JSON file."""
    with open(file, "w", encoding="utf-8") as f:
        f.write(json.dumps(reservations))


def log_conflicts(file="conflicts.log"):
    """Append new conflicts to a log file once, then print the whole log."""
    with open(file, "a", encoding="utf-8") as f:
        for c in conflicts:
            f.write(f"{datetime.now()} {c}\n")
    conflicts.clear()
    with open(file, encoding="utf-8") as f:
        print(f.read(), end="")


def try_schedule(room_id, time_slot, equipment_list=None):
    """Book a room; print the reason and return None if it is rejected."""
    try:
        return schedule_room(room_id, time_slot, equipment_list)
    except ValueError as exc:
        print(f"Could not book {room_id} for {time_slot!r}: {exc}")
        return None


def main():
    """Run a short demonstration of the scheduler."""
    try_schedule("Board-1", "09-11")
    try_schedule("Board-1", "09-11")
    b = try_schedule("Huddle-3", "14-16")
    try_schedule("Huddle-3", "14-12")
    try_schedule("Huddle-3", 1530)
    print("Slot length for b:", slot_hours(reservations[b]["slot"]))
    cancel_reservation(77)
    slot = input("Slot for Board-2, like 10-12 (Enter for 10-12): ") or "10-12"
    try_schedule("Board-2", slot, ["projector", "webcam"])
    try_schedule("Board-3", "13-14", ["webcam"])
    export_schedule()
    log_conflicts()
    print("Equipment left:", equipment_pool)
    print("Reservations:", reservations)


if __name__ == "__main__":
    main()
