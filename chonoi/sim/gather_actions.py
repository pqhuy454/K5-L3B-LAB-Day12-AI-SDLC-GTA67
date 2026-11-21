"""Hành động Lát 2 cho buổi sáng (`gather`): hái nút mặt nước và bắt đàn cá dưới nước.

Tách riêng khỏi `chonoi/sim/gather.py` để giảm xung đột Git với Lát 1 (bơi, oxy, ngạt, giỏ).
Mọi hằng số đọc từ `sim.t` (`game.contract.json`); sắp tie-break bằng `id_key` (`N2 < N10`, `F2 < F10`).
"""

import math
from typing import Literal, Protocol, TypedDict

from ..ids import id_key

TICK_HZ: float = 60.0


class NodeEntity(TypedDict):
    id: str
    kind: str
    pos: list[float]
    regrow_ticks: int


class FishEntity(TypedDict):
    id: str
    kind: str
    pos: list[float]
    heading_deg: float


class GatherTuning(TypedDict):
    hold_capacity: int
    interact_radius: float
    node_yield: int
    regrow_s: float
    catch_radius: float
    catch_cooldown_s: float
    fish_yield: dict[str, int]


EventPayload = dict[str, str | int]
EventTuple = tuple[str, EventPayload]


class GatherSimPort(Protocol):
    t: GatherTuning
    pos: list[float]
    hold: list[str]
    nodes: list[NodeEntity]
    fish: list[FishEntity]
    catch_cd_ticks: int

    def _at_surface(self) -> bool: ...


def _emit_hold_full(
    events: list[EventTuple],
    source: Literal["node", "fish"],
    target_id: str,
    kind: str,
    needed: int,
    free: int,
) -> None:
    events.append(
        (
            "hold_full",
            {
                "source": source,
                "id": target_id,
                "kind": kind,
                "needed": needed,
                "free": free,
            },
        )
    )


def try_harvest(sim: GatherSimPort, events: list[EventTuple], tick_hz: float = TICK_HZ) -> bool:
    """Hái nút `ready` gần nhất trong `interact_radius` khi đang ở mặt nước.

    - Không fallback sang nút khác nếu nút gần nhất không đủ chỗ trong giỏ.
    - Không hái một phần: toàn bộ `node_yield` phải vừa sức chứa còn lại.
    """
    if not sim._at_surface():
        return False

    radius = float(sim.t["interact_radius"])
    candidates: list[tuple[float, tuple[str, int, str], NodeEntity]] = []
    for node in sim.nodes:
        if node["regrow_ticks"] != 0:
            continue
        dist = math.dist(sim.pos, node["pos"])
        if dist <= radius:
            candidates.append((dist, id_key(node["id"]), node))

    if not candidates:
        return False

    candidates.sort(key=lambda item: (item[0], item[1]))
    target = candidates[0][2]
    qty = int(sim.t["node_yield"])
    free = int(sim.t["hold_capacity"]) - len(sim.hold)
    if qty > free:
        _emit_hold_full(events, "node", target["id"], target["kind"], qty, free)
        return False

    sim.hold.extend([target["kind"]] * qty)
    target["regrow_ticks"] = int(round(float(sim.t["regrow_s"]) * tick_hz))
    events.append(
        (
            "gather",
            {
                "node_id": target["id"],
                "kind": target["kind"],
                "count": qty,
            },
        )
    )
    return True


def try_catch(sim: GatherSimPort, events: list[EventTuple], tick_hz: float = TICK_HZ) -> bool:
    """Bắt đàn cá gần nhất trong `catch_radius` khi đang dưới nước và hết hồi chiêu.

    - Cấm bắt một phần: toàn bộ `fish_yield[kind]` phải vừa chỗ trống còn lại.
    - Không fallback sang đàn cá khác nếu đàn gần nhất không vừa giỏ.
    - Chỉ đặt `catch_cd_ticks` khi bắt trúng cá thành công.
    """
    if sim.catch_cd_ticks > 0 or sim._at_surface():
        return False

    radius = float(sim.t["catch_radius"])
    candidates: list[tuple[float, tuple[str, int, str], FishEntity]] = []
    for fish in sim.fish:
        dist = math.dist(sim.pos, fish["pos"])
        if dist <= radius:
            candidates.append((dist, id_key(fish["id"]), fish))

    if not candidates:
        return False

    candidates.sort(key=lambda item: (item[0], item[1]))
    target = candidates[0][2]
    kind = target["kind"]
    qty = int(sim.t["fish_yield"][kind])
    free = int(sim.t["hold_capacity"]) - len(sim.hold)
    if qty > free:
        _emit_hold_full(events, "fish", target["id"], kind, qty, free)
        return False

    sim.hold.extend([kind] * qty)
    sim.fish = [fish for fish in sim.fish if fish["id"] != target["id"]]
    sim.catch_cd_ticks = int(round(float(sim.t["catch_cooldown_s"]) * tick_hz))
    events.append(
        (
            "fish_caught",
            {
                "fish_id": target["id"],
                "kind": kind,
                "count": qty,
            },
        )
    )
    return True
