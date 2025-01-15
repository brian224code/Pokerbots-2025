from information_set import InformationSet
from history import History

class CFR_Trainer:
    def __init__(self):
        # TODO Init cume regret tables, cume strategy tables, initial strat profile
        pass

    def update_cumulative_regret(self):
        # TODO line 25 in Algo 1
        pass

    def update_cumulative_strategy(self):
        # TODO line 26 in Algo 1
        pass

    def calculate_node_utility(self):
        # TODO line 21 in Algo 1
        pass

    def calculate_current_strategy(self):
        # TODO line 28 in Algo 1
        pass

    def CFR(history, player, t, pi_1, pi_2):
        # TODO Implement exactly like Algorithm 1 from design doc
        pass

    def solve(self, iters):
        for t in range(iters):
            for player in [1, 2]:
                self.CFR('empty history', player, t, 1, 1)
    
    def get_equilibrium_strategy(self):
        # TODO Return average strategy
        pass

if __name__ == '__main__':
    trainer = CFR_Trainer()
    trainer.solve(100,000)
    strategy = trainer.get_equilibrium_strategy()
    # TODO Save strategy as csv
