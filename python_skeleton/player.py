'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

from calculate_winrates import *

import random
import math
import eval7


class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        self.hole_winrates = load_csv("winrates_for_street_size_0.csv") # returns a dictionary with frozensets as keys
        self.post_turn_win_probability = 0
        self.won = False
        self.cheese = False
        self.all_in_counter = 0
        self.opp_auction_amt = []
        self.opp_auction_amt_logging = []
        self.win_prob_wo_auction = 0
        self.opp_card_strength = []
        self.bluff = False
        self.opp_bluff_called_cnt = 0 # Net Gains/Losses from bluffs
        # self.aggro_playing = False # Bool for playing tighter and more aggro when we are ahead
        self.preflop_cfr = {}
        self.preflop_action = None
        self.hole_strength = 0

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your cards
        big_blind = bool(active)  # True if you are the big blind
        my_bounty = round_state.bounties[active]  # your current bounty rank
        #print("\n=============\nnew round")
        #print(f"Round Number: {round_num}")
        #print(f"Game Clock: {game_clock}")
        #print(f"Bounty Rank: {my_bounty}")
        
        if my_bankroll > 3.6 * (1000 - round_num):
            self.won = True
        # elif my_bankroll > 0.75 * (1000 - round_num):
        #     self.aggro_playing = True

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        
        my_bounty_hit = terminal_state.bounty_hits[active]  # True if you hit bounty
        opponent_bounty_hit = terminal_state.bounty_hits[1-active] # True if opponent hit bounty
        bounty_rank = previous_state.bounties[active]  # your bounty rank

        # The following is a demonstration of accessing illegal information (will not work)
        opponent_bounty_rank = previous_state.bounties[1-active]  # attempting to grab opponent's bounty rank

        if my_bounty_hit:
            print("I hit my bounty of " + bounty_rank + "!")
        if opponent_bounty_hit:
            print("Opponent hit their bounty of " + opponent_bounty_rank + "!")

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_bounty = round_state.bounties[active]  # your current bounty rank
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot

        pot = my_contribution + opp_contribution

        opp_all_in_pct = self.all_in_counter / game_state.round_num
        min_raise, max_raise = round_state.raise_bounds()

        #print("All in pct: ", opp_all_in_pct)

        if self.won:
            if FoldAction in legal_actions:
                return FoldAction()
            return CheckAction()

        # Pre-flop
        if street == 0:
            print("Preflop")

            # Lookup strength of hole cards from pre-calculated dictionary
            self.hole_strength = self.hole_winrates[frozenset(my_cards)]

            print("Initial strength of hand: ", self.hole_strength)
            if my_cards[0][0] == my_cards[1][0]:
                hole_pair = True
            else:
                hole_pair = False

            # pookie bot strategy
            self.cheese = False
            max_preflop_bet = int((my_stack + my_pip) * .2 * self.hole_strength)

            HOLE_STRENGTH_THRESH = 0
            # if self.aggro_playing:
            #     HOLE_STRENGTH_THRESH = 0.69
            
            #TODO review this code chunk; I think there's a bug here
            if (self.hole_strength <= HOLE_STRENGTH_THRESH and continue_cost > 0 and FoldAction in legal_actions):
                if not bool(active):
                    if RaiseAction in legal_actions and min_raise <= 5 and max_raise >= 5:
                        self.cheese = True
                        self.preflop_action = RaiseAction
                        return RaiseAction(5)
                elif continue_cost <=5:
                    self.cheese = True
                    self.preflop_action = CallAction
                    return CallAction()
                return FoldAction()
            elif (self.hole_strength * 0.7 > continue_cost / (continue_cost + pot)
                    and RaiseAction in legal_actions 
                    and my_contribution < max_preflop_bet): # TODO: tweak 0.85
                
                if hole_pair:
                    bet = min(int((min_raise + ((max_raise - min_raise) * .1) ** self.hole_strength)), max_preflop_bet) * 3
                else:
                    bet = min(int((min_raise + ((max_raise - min_raise) * .1) ** self.hole_strength)), max_preflop_bet)

                if bet >= min_raise and bet <= max_raise:
                    self.preflop_action = RaiseAction
                    return RaiseAction(bet)
                elif CheckAction in legal_actions:
                    self.preflop_action = RaiseAction
                    return CheckAction()
                else:
                    self.preflop_action = CallAction
                    return CallAction()
            elif CheckAction in legal_actions:
                self.preflop_action = CheckAction
                return CheckAction()
            else:  
                # Reach here when you're not super confident but EV is high enough
                # to continue playing
                if continue_cost + my_contribution > max_preflop_bet and not hole_pair and self.hole_strength < .67:
                    if not bool(active):
                        if RaiseAction in legal_actions:
                            self.cheese = True
                            self.preflop_action = RaiseAction
                            return RaiseAction(5)
                    elif continue_cost <=5:
                        self.cheese = True
                        self.preflop_action = CallAction
                        return CallAction()
                    elif ((opp_all_in_pct > 0.6) 
                          and (self.hole_strength > 0 or (my_cards[0][0] in 'AKQJT98' and my_cards[1][0] in 'AKQJT98') or (my_cards[0][0] in 'AKQJ' or my_cards[1][0] in 'AKQJ')) 
                          and (CallAction in legal_actions)):
                        self.preflop_action = CallAction
                        return CallAction()
                    self.preflop_action = FoldAction
                    return FoldAction()
                self.preflop_action = CallAction
                return CallAction()  

        # Flop
        elif street == 3:
            print("Flop")

            # run monte carlo to estimate win rate based on hole cards and flop
            sim_iterations = 200
            win_probability = monte_carlo(my_cards + board_cards, sim_iterations)

            if win_probability > 0.9 and RaiseAction in legal_actions:
                return RaiseAction(max(min_raise, min(max_raise, int(win_probability**2 * 80))))
            if win_probability > 0.75:
                return CheckAction() if CheckAction in legal_actions else CallAction() # check-fold
            return CheckAction() if CheckAction in legal_actions else FoldAction() # check-fold

        # Turn
        elif street == 4:
            print("Turn")

            sim_iterations = 280
            win_probability = monte_carlo(my_cards + board_cards, sim_iterations)
            self.post_turn_win_probability = win_probability

            if win_probability > 0.9 and RaiseAction in legal_actions:
                return RaiseAction(max(min_raise, min(max_raise, int(win_probability**2 * 80))))
            if win_probability > 0.75:
                return CheckAction() if CheckAction in legal_actions else CallAction() # check-fold
            return CheckAction() if CheckAction in legal_actions else FoldAction() # check-fold

        # River
        elif street == 5:
            print("River")
            
            win_probability = self.post_turn_win_probability
            print("Win probability: ", win_probability)

            if win_probability > 0.9 and RaiseAction in legal_actions:
                return RaiseAction(max(min_raise, min(max_raise, int(win_probability**2 * 80))))
            return CheckAction() if CheckAction in legal_actions else FoldAction() # check-fold

if __name__ == '__main__':
    run_bot(Player(), parse_args())
