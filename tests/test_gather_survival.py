"""Kiểm các ranh giới sinh tồn của lát Movement and survival."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session
from chonoi.sim import hold


class GatherSurvival(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]
        self.inputs = LiveInputs()

    def session(self, player, hold=None):
        scenario = {"player": player}
        if hold is not None:
            scenario["hold"] = hold
        return Session("gather", self.tuning, scenario, 1)

    def step(self, session):
        return [row["name"] for row in session.step(self.inputs.advance())]

    def test_oxygen_zero_tick_counts_and_surface_resets_choking(self):
        s = self.session({"pos": [50, 1], "oxygen_ticks": 2})
        self.assertEqual(self.step(s), [])
        self.assertEqual(s.sim.oxygen_ticks, 1)
        self.assertEqual(self.step(s), ["oxygen_empty"])
        self.assertEqual(s.sim.zero_oxy_ticks, 1)
        for _ in range(self.tuning["gather"]["choke_interval_ticks"] - 2):
            self.step(s)
        self.assertEqual(s.sim.hp, 3)
        self.assertEqual(self.step(s), ["choke"])
        self.assertEqual(s.sim.hp, 2)
        self.assertEqual(s.sim.zero_oxy_ticks, 0)
        s.sim.pos[1] = self.tuning["gather"]["surface_depth"]
        self.step(s)
        self.assertEqual(s.sim.zero_oxy_ticks, 0)
        self.assertEqual(s.sim.oxygen_ticks, self.tuning["gather"]["oxygen_refill_per_tick"])

    def test_faint_clears_basket_before_end_and_preempts_interact(self):
        interval = self.tuning["gather"]["choke_interval_ticks"]
        s = self.session({"pos": [2, 1], "oxygen_ticks": 0,
                          "zero_oxy_ticks": interval - 1, "hp": 1}, ["ca_loc"])
        self.inputs.set(interact=True)
        self.assertEqual(self.step(s), ["choke", "faint", "gather_end"])
        self.assertTrue(s.done)
        self.assertEqual(s.sim.reason, "fainted")
        self.assertEqual(s.sim.inventory_items(), {})
        self.assertEqual(s.sim.hold, [])

    def test_basket_addition_is_atomic_and_preserves_order(self):
        capacity = self.tuning["gather"]["hold_capacity"]
        s = self.session({}, ["ca_loc"] * (capacity - 2))
        self.assertEqual(hold.free_slots(s.sim), 2)
        self.assertFalse(hold.push_all(s.sim, ["ca_linh"] * 3))
        self.assertFalse(s.sim.add_to_hold("ca_linh", 3))
        self.assertEqual(s.sim.hold, ["ca_loc"] * (capacity - 2))
        self.assertTrue(s.sim.add_to_hold("bong_sung", 2))
        self.assertEqual(s.sim.hold[-2:], ["bong_sung", "bong_sung"])
        self.assertFalse(s.sim.add_to_hold("ca_loc"))
        self.assertEqual(len(s.sim.hold), capacity)
        self.assertEqual(hold.free_slots(s.sim), 0)


if __name__ == "__main__":
    unittest.main()
