import random

class SeededRNG:
    def __init__(self, seed):
        self.seed = int(seed)
        self._rng = random.Random(self.seed)

    def random(self):
        return self._rng.random()

    def randint(self, a, b):
        return self._rng.randint(a, b)

    def choice(self, seq):
        return self._rng.choice(seq)

    def sample(self, seq, k):
        return self._rng.sample(seq, k)

    def chance(self, probability):
        return self._rng.random() < probability
