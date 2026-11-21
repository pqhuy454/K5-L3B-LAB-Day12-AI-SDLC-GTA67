"""Lát 1 — Lặn sống sót (bơi, chuyển vùng mặt nước/dưới nước, oxy, ngạt, Máu, ngất).

Chủ: Trần Duy Thành (thanh289).
Triển khai đúng US1 (FR-011..FR-014):
  - Mặt nước: d <= surface_depth (tính theo vị trí CUỐI bước) -> hồi oxygen_refill_per_tick, zero_oxy_ticks = 0.
  - Dưới nước: oxy -1/tick; từ dương về 0 phát 'oxygen_empty'; đếm zero_oxy_ticks (tính cả bước vừa chạm 0).
  - Đủ choke_interval_ticks (60) -> -1 Máu, phát 'choke', đặt zero_oxy_ticks = 0.
  - Máu == 0 -> xóa giỏ qua hold.clear(sim), phát 'faint', trả True để GatherSim kết thúc reason='fainted'.
"""

from . import hold


def zone_change(sim, was_surface: bool, events: list) -> None:
    now_surface = sim._at_surface()
    if was_surface and not now_surface:
        events.append(("dive", {"pos": list(sim.pos)}))
    elif not was_surface and now_surface:
        events.append(("surface", {"pos": list(sim.pos)}))


def update_oxygen(sim, events: list) -> bool:
    if sim._at_surface():
        sim.oxygen_ticks = min(sim.oxygen_max, sim.oxygen_ticks + sim.t["oxygen_refill_per_tick"])
        sim.zero_oxy_ticks = 0
        return False

    was_positive = sim.oxygen_ticks > 0
    sim.oxygen_ticks = max(0, sim.oxygen_ticks - 1)
    if was_positive and sim.oxygen_ticks == 0:
        events.append(("oxygen_empty", {}))

    if sim.oxygen_ticks == 0:
        sim.zero_oxy_ticks += 1
        if sim.zero_oxy_ticks >= sim.t["choke_interval_ticks"]:
            sim.zero_oxy_ticks = 0
            sim.hp = max(0, sim.hp - 1)
            events.append(("choke", {"hp": sim.hp}))
            if sim.hp == 0:
                hold.clear(sim)
                events.append(("faint", {}))
                return True
    else:
        sim.zero_oxy_ticks = 0
    return False
