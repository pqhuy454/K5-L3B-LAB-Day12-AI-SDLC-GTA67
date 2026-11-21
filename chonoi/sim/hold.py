"""Giỏ nguyên liệu buổi sáng: một lượt nhặt được thêm nguyên vẹn hoặc không thêm."""


def free_slots(sim) -> int:
    return sim.t["hold_capacity"] - len(sim.hold)


def push_all(sim, kinds: list) -> bool:
    if len(kinds) > free_slots(sim):
        return False
    sim.hold.extend(kinds)
    return True


def clear(sim) -> None:
    sim.hold.clear()
