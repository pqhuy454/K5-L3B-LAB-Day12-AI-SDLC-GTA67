"""Luật lặn sống sót, gọi từ bộ điều phối buổi sáng."""

from . import hold


def zone_change(sim, was_surface, events):
    at_surface = sim._at_surface()
    if was_surface != at_surface:
        events.append(("surface" if at_surface else "dive", {"pos": sim.pos.copy()}))


def update_oxygen(sim, events) -> bool:
    if sim._at_surface():
        sim.oxygen_ticks = min(sim.oxygen_max,
                               sim.oxygen_ticks + sim.t["oxygen_refill_per_tick"])
        sim.zero_oxy_ticks = 0
        return False

    had_oxygen = sim.oxygen_ticks > 0
    sim.oxygen_ticks = max(0, sim.oxygen_ticks - 1)
    if had_oxygen and sim.oxygen_ticks == 0:
        events.append(("oxygen_empty", {"pos": sim.pos.copy()}))
    if sim.oxygen_ticks > 0:
        sim.zero_oxy_ticks = 0
        return False

    # Bước vừa chạm 0 cũng là bước ngạt đầu tiên.
    sim.zero_oxy_ticks += 1
    if sim.zero_oxy_ticks >= sim.t["choke_interval_ticks"]:
        sim.zero_oxy_ticks = 0
        sim.hp -= 1
        events.append(("choke", {"hp": sim.hp}))
        if sim.hp == 0:
            hold.clear(sim)
            events.append(("faint", {"pos": sim.pos.copy()}))
            return True
    return False
