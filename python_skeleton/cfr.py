from information_set import InformationSet
from history import History, NUM_ACTIONS
import csv
import os
from datetime import datetime
import pandas as pd
from tqdm import tqdm

class CFR_Trainer:
    def __init__(self, cumulative_regret_filename='', cumulative_strategy_filename='', current_profile_filename=''):
        """
        Initializes trainer for CFR algo. Can either continue training on existing weights or train from scratch
        Dict tables are key = hashed info set, value = list of 10 numbers indexed by action

        Args:
            cumulative_regret_filename: csv file containing existing cumulative regret table, or empty to train from scratch
            cumulative_strategy_filename: csv file containing existing cumulative strategy table, or empty to train from scratch
            current_profile_filename: csv file containing existing current profile table, or empty to train from scratch
        """
        if cumulative_regret_filename and cumulative_strategy_filename and current_profile_filename:
            print('Loading existing weights...')
            self.cumulative_regret = CFR_Trainer.load_from_csv(cumulative_regret_filename)
            self.cumulative_strategy = CFR_Trainer.load_from_csv(cumulative_strategy_filename)
            self.current_profile = CFR_Trainer.load_from_csv(current_profile_filename)
        elif cumulative_strategy_filename or cumulative_strategy_filename or current_profile_filename:
            raise Exception('Need all 3 files to continue training on existing weights.')
        else:
            self.cumulative_regret = {}
            self.cumulative_strategy = {} 
            self.current_profile = {}

        self.regrets = [] # used for checking if we converged

    def update_cumulative_regret(self, hashable_info_set, action, actual_utility, expected_utility, opp_reach_prob):
        """
        Line 25 in Algo 1

        Args:
            hashable_info_set: string rep of info set
            action: index of action being taken
            actual_utility: utility of taking this action
            expected_utility: utility of the current info set (expected value of all legal actions)
            opp_reach_prob: probability of opponent getting to this info set        
        """
        regret = opp_reach_prob * (actual_utility - expected_utility)

        self.cumulative_regret[hashable_info_set][action] += regret
        self.regrets.append(regret)

    def update_cumulative_strategy(self, hashable_info_set, action, my_reach_prob, action_weight):           
        """
        Line 26 in Algo 1

        Args:
            hashable_info_set: string rep of info set
            action: index of action being taken
            my_reach_prob: probability of getting to this info set
            action_weight: probability of taking this action
        """
        self.cumulative_strategy[hashable_info_set][action] += my_reach_prob * action_weight

    def generate_uniform_strategy(self, history):
        """
        Args:
            history: History object

        Returns:
            list of 10 weights corresponding to the strategy for a given info set
            such that the legal actions are taken with uniform probability
        """
        legal_actions = history.get_legal_actions()

        return [
            1.0/sum(legal_actions) if legal else 0.0
            for legal in legal_actions
        ]

    def update_current_profile(self, hashable_info_set, history):
        """
        Line 28 in Algo 1

        Args:
            hashable_info_set: string representation of the information set
            history: History object (used for determining legal actions when generating uniform strategy)

        Returns:
            normalized strategy if sum of cumulative regrets is > 0, else uniform strategy
        """
        positive_regrets = [max(regret, 0.0) for regret in self.cumulative_regret[hashable_info_set]]
        
        if sum(positive_regrets) > 0:
            self.current_profile[hashable_info_set] = [
                float(regret) / sum(positive_regrets)
                for regret in positive_regrets
            ]
        else:
            self.current_profile[hashable_info_set] = self.generate_uniform_strategy(history)

    def CFR(self, history, player, t, reach_probs):
        """
        CFR algorithm described in Algo 1

        Args:
            history: History object (encodes the poker game)
            player: 0 or 1, the player currently learning
            t: timestep
            reach_probs: tuple of reach probabilities for the given info_set for each player
                         (pi_0, pi_1)
        
        Returns:
            utility of current node (actual utility if terminal node, expected utility if decision node)
        """
        # Deal with terminal and chance nodes
        if history.get_node_type() == 'T':
            return history.get_utility(player)
        elif history.get_node_type() == 'C':
            new_history = history.generate_chance_outcome()
            return self.CFR(new_history, player, t, reach_probs)
        
        # Get information set and set it up in the cumulative tables if not seen yet
        information_set = history.get_player_info(player)
        hashable_info_set = str(information_set)

        # print('---------------------------------')

        # print(f'Info set: {hashable_info_set}')
        # print(f'Street: {history.round_state.street}')
        # print(f'Hands: {history.round_state.hands}')
        # print(f'Comm cards: {history.round_state.deck}')
        # print(f'Pot: {sum(history.round_state.stacks)}')
                
        # print(f'Cumulative Regrets: {self.cumulative_regret}')
        # print(f'Cumulative Strategy: {self.cumulative_strategy}')
        # print(f'Current Profile: {self.current_profile}')
        # print(f'Regrets: {self.regrets}')

        if hashable_info_set not in self.current_profile:
            self.current_profile[hashable_info_set] = self.generate_uniform_strategy(history)
        if hashable_info_set not in self.cumulative_regret:
            self.cumulative_regret[hashable_info_set] = [0.0] * NUM_ACTIONS
        if hashable_info_set not in self.cumulative_strategy:
            self.cumulative_strategy[hashable_info_set] = [0.0] * NUM_ACTIONS

        # Calculate utilities
        expected_utility = 0
        actual_utilities = [0.0] * NUM_ACTIONS
        legal_actions = history.get_legal_actions()
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
        
        # Update strategies if learning player is currently taking the action
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
        """
        Runs the CFR algorithm

        Args:
            iters: num iterations of self-play
        """
        for t in tqdm(range(iters), desc='Training', unit='iteration', total=iters):
            for player in [0, 1]:
                self.CFR(History.generate_initial_node(player), player, t, (1.0, 1.0))

    def get_equilibrium_strategy(self):
        """
        Returns:
            average strategy in the form of a dict with key = info set as string 
            and value = list of weights for each of the 10 actions
        """
        return {
            information_set: [weight / sum(strategy) if weight else 0.0 for weight in strategy]
            for information_set, strategy in self.cumulative_strategy.items()
        }
    
    @classmethod
    def load_from_csv(cls, filename):
        df = pd.read_csv(filename)

        table = {
            str(row['information set']) : [float(row[f'action {i}']) for i in range(NUM_ACTIONS)]
            for _, row in df.iterrows()
        }

        return table

    @classmethod
    def save_to_csv(cls, filename, data):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            header = ['information set'] + [f'action {i}' for i in range(NUM_ACTIONS)]
            writer.writerow(header)
            for info_set, values in data.items():
                writer.writerow([info_set] + values)
        print(f'Saved data to {filename}.')

if __name__ == '__main__':
    trainer = CFR_Trainer('./CFR_TRAIN_DATA/1.16/cumulative_regret.csv','./CFR_TRAIN_DATA/1.16/cumulative_strategy.csv','./CFR_TRAIN_DATA/1.16/current_profile.csv')
    trainer.solve(1)
    strategy = trainer.get_equilibrium_strategy()
    
    data_folder = './CFR_TRAIN_DATA'
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)
    # save_directory = f'{data_folder}/{datetime.now()}'
    # os.mkdir(save_directory)
    save_directory = data_folder

    # Save equilibrium strategy
    CFR_Trainer.save_to_csv(f'{save_directory}/strategy.csv', strategy)

    # Save tables for future training
    CFR_Trainer.save_to_csv(f'{save_directory}/cumulative_strategy.csv', trainer.cumulative_strategy)
    CFR_Trainer.save_to_csv(f'{save_directory}/cumulative_regret.csv', trainer.cumulative_regret)
    CFR_Trainer.save_to_csv(f'{save_directory}/current_profile.csv', trainer.current_profile)

    # Save regrets to see if it converged
    with open(f'{save_directory}/regrets.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(trainer.regrets)
    print(f'Saved data to {save_directory}\regrets.csv')
    