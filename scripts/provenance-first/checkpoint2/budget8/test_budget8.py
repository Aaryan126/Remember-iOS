import unittest
from approved_run8 import accounting, GIB


class BudgetTests(unittest.TestCase):
    def test_approved_range(self):
        self.assertEqual(accounting(34*GIB, 42*GIB, GIB, GIB)["conservativeGrowthBytes"], 8*GIB)

    def test_over_cap_rejected(self):
        with self.assertRaisesRegex(ValueError, "above 8 GiB"):
            accounting(34*GIB-1, 42*GIB, GIB, GIB)

    def test_reserve_not_relaxed(self):
        with self.assertRaisesRegex(ValueError, "below 10 GiB"):
            accounting(10*GIB-1, 10*GIB, 0, 0)

    def test_scoped_growth_cannot_be_hidden_by_freeing_disk(self):
        with self.assertRaisesRegex(ValueError, "above 8 GiB"):
            accounting(50*GIB, 40*GIB, 5*GIB, 4*GIB)

    def test_baseline_not_reset(self):
        self.assertEqual(accounting(40*GIB, 44*GIB, GIB, GIB)["conservativeGrowthBytes"], 4*GIB)

    def test_invalid_accounting_rejected(self):
        with self.assertRaises(ValueError): accounting(40*GIB, 44*GIB, -1, 0)


if __name__ == "__main__": unittest.main()
