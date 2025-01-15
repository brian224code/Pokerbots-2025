from information_set import InformationSet
from history import History, NUM_ACTIONS
import csv
import tqdm

class CFR_Trainer:
    def __init__(self):
        # key = hashed info set, value = list of 10 numbers indexed by action
        self.cumulative_regret = {} 
        self.cumulative_strategy = {} 
        self.current_profile = {}
        self.regrets = [] # used for checking if we converged

    def update_cumulative_regret(self, information_set, action, actual_utility, expected_utility, opp_reach_prob):
        hashable_info_set = str(information_set)

        if hashable_info_set not in self.cumulative_regret:
            self.cumulative_regret[hashable_info_set] = [0] * NUM_ACTIONS

        regret = opp_reach_prob * (actual_utility - expected_utility)
        self.cumulative_regret[hashable_info_set][action] += regret
        self.regrets.append(regret)

    def update_cumulative_strategy(self, information_set, action, my_reach_prob, action_prob):
        hashable_info_set = str(information_set)

        if hashable_info_set not in self.cumulative_strategy:
            self.cumulative_strategy[hashable_info_set] = [0] * NUM_ACTIONS
            
        self.cumulative_strategy[hashable_info_set][action] += my_reach_prob * action_prob

    def generate_uniform_strategy(self, history):
        legal_actions = history.get_legal_actions()

        return [
            1.0/sum(legal_actions) if legal else 0
            for legal in legal_actions
        ]

    def update_current_profile(self, information_set, history):
        hashable_info_set = str(information_set)

        if hashable_info_set not in self.cumulative_regret:
            self.cumulative_regret[hashable_info_set] = [0] * NUM_ACTIONS

        positive_regrets = [max(regret, 0) for regret in self.cumulative_regret[hashable_info_set]]
        
        if sum(positive_regrets) > 0:
            self.current_profile[hashable_info_set] = [
                float(regret) / sum(positive_regrets)
                for regret in positive_regrets
            ]
        else:
            self.current_profile[hashable_info_set] = self.generate_uniform_strategy(history)

    def CFR(history, player, t, pi_1, pi_2):
        # TODO Implement exactly like Algorithm 1 from design doc
        pass

    def solve(self, iters):
        # TODO add tqdm
        for t in range(iters):
            for player in [1, 2]:
                self.CFR('empty history', player, t, 1, 1) # TODO Initialize history

    def get_equilibrium_strategy(self):
        # TODO need to make sure 1/|A(I)| is also factored in??? Is this right???
        return {
            information_set: [weight / sum(strategy) for weight in strategy]
            for information_set, strategy in self.cumulative_strategy.items()
        }


if __name__ == '__main__':
    trainer = CFR_Trainer()
    trainer.solve(100,000)
    strategy = trainer.get_equilibrium_strategy()

    print('Saving strategy and regrets...')

    # Save strategy as csv
    with open('strategy.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        header = ['information set'] + [f'action {i}' for i in range(10)]
        writer.writerow(header)
        for info_set, weights in strategy.items():
            writer.writerow([info_set] + weights)
    print('Saved equilibrium strategy to strategy.csv')

    # Save regrets as csv
    with open('regrets.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(trainer.regrets)
    print('Saved regrets to regrets.csv')