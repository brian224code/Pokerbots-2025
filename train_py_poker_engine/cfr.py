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

    def update_cumulative_regret(self, hashable_info_set, action, actual_utility, expected_utility, opp_reach_prob):
        regret = opp_reach_prob * (actual_utility - expected_utility)
        self.cumulative_regret[hashable_info_set][action] += regret
        self.regrets.append(regret)

    def update_cumulative_strategy(self, hashable_info_set, action, my_reach_prob, action_weight):           
        self.cumulative_strategy[hashable_info_set][action] += my_reach_prob * action_weight

    def generate_uniform_strategy(self, history):
        legal_actions = history.get_legal_actions()

        return [
            1.0/sum(legal_actions) if legal else 0
            for legal in legal_actions
        ]

    def update_current_profile(self, hashable_info_set, history):
        positive_regrets = [max(regret, 0) for regret in self.cumulative_regret[hashable_info_set]]
        
        if sum(positive_regrets) > 0:
            self.current_profile[hashable_info_set] = [
                float(regret) / sum(positive_regrets)
                for regret in positive_regrets
            ]
        else:
            self.current_profile[hashable_info_set] = self.generate_uniform_strategy(history)

    def CFR(self, history, player, t, reach_probs):
        # TODO docstrings (reach_probs is a tuple of pi_0, pi_1)
        if history.get_node_type() == 'T':
            return history.get_utility(player)
        elif history.get_node_type() == 'C':
            new_history = history.generate_chance_outcome()
            return self.CFR(new_history, player, t, reach_probs)
        
        information_set = history.get_player_info(player)
        hashable_info_set = str(information_set)
        if hashable_info_set not in self.current_profile:
            self.current_profile[hashable_info_set] = self.generate_uniform_strategy(history)
        if hashable_info_set not in self.cumulative_regret:
            self.cumulative_regret[hashable_info_set] = [0] * NUM_ACTIONS
        if hashable_info_set not in self.cumulative_strategy:
            self.cumulative_strategy[hashable_info_set] = [0] * NUM_ACTIONS

        expected_utility = 0
        actual_utilities = [0] * NUM_ACTIONS
        legal_actions = history.get_legal_actions() # TODO Does it matter what player it is
        for action, legal in enumerate(legal_actions):
            if not legal:
                continue

            new_history = history.generate_action_outcome(action)
            action_weight = self.current_profile[hashable_info_set][action]
            
            if history.get_active_player() == 0:
                actual_utilities[action] = self.CFR(new_history, player, t, (action_weight*reach_probs[0], reach_probs[1]))
            else:
                actual_utilities[action] = self.CFR(new_history, player, t, (reach_probs[0], action_weight*reach_probs[1]))

            expected_utility += action_weight*actual_utilities[action]

        if history.get_active_player() == player:
            for action, legal in enumerate(legal_actions):
                if not legal:
                    continue

                action_weight = self.current_profile[hashable_info_set][action]

                self.update_cumulative_regret(hashable_info_set, action, actual_utilities[action], expected_utility, reach_probs[1-player])
                self.update_cumulative_strategy(hashable_info_set, action, reach_probs[player], action_weight)
            self.update_current_profile(hashable_info_set, history)
        
        return expected_utility
                
    def solve(self, iters):
        # TODO add tqdm
        for t in range(iters):
            for player in [0, 1]:
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