import unittest
import check


class ResourcePolicyTests(unittest.TestCase):
    def test_realistic_accounting(self):
        g = check.GIB
        self.assertEqual(check.accounting(20*g, 42*g, 4*g, 2*g)["conservativeGrowthBytes"], 22*g)
        self.assertEqual(check.accounting(30*g, 42*g, 20*g, 3*g)["conservativeGrowthBytes"], 23*g)

    def test_reservation_cannot_exceed_cap_or_free_reserve(self):
        g = check.GIB
        for values in [(20*g, 20*g + check.CAP, 0, 0, 1), (10*g, 10*g, 0, 0, 1), (20*g, 20*g, check.CAP + 1, 0, 0)]:
            with self.assertRaises(SystemExit): check.accounting(*values)

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError): check.accounting(-1, 0, 0, 0)


if __name__ == "__main__": unittest.main()
