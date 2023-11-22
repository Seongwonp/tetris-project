import unittest
from tetris.bag import SevenBag


class TestSevenBag(unittest.TestCase):

    def test_first_bag_has_all_seven(self):
        bag = SevenBag()
        drawn = [bag.pop() for _ in range(7)]
        self.assertEqual(sorted(drawn), list(range(1, 8)))

    def test_second_bag_also_has_all_seven(self):
        bag = SevenBag()
        for _ in range(7):
            bag.pop()
        drawn = [bag.pop() for _ in range(7)]
        self.assertEqual(sorted(drawn), list(range(1, 8)))

    def test_no_same_piece_twice_in_bag(self):
        bag = SevenBag()
        drawn = [bag.pop() for _ in range(7)]
        self.assertEqual(len(drawn), len(set(drawn)))

    def test_peek_does_not_consume(self):
        bag = SevenBag()
        peeked = bag.peek(3)
        self.assertEqual(len(peeked), 3)
        first = bag.pop()
        self.assertEqual(first, peeked[0])

    def test_distribution_over_many_draws(self):
        bag = SevenBag()
        counts = {i: 0 for i in range(1, 8)}
        for _ in range(700):
            counts[bag.pop()] += 1
        # 700번 뽑으면 각 피스는 정확히 100번
        for piece_id, count in counts.items():
            self.assertEqual(count, 100, f"Piece {piece_id} count: {count}")


if __name__ == "__main__":
    unittest.main()
