

class MonteCarloSettings:

    def __init__(self, num_paths, time_steps, rng=None, **kwargs):
        self.num_paths = num_paths
        self.time_steps = time_steps
        self.rng = rng or "pseudorandom"
