'''
Simple example pokerbot, written in Python.
'''

import sys
import os

# Get the absolute path of the parent directory (one level up)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the parent directory to sys.path
sys.path.append(parent_dir)

from python_skeleton.skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from python_skeleton.skeleton.states import GameState, TerminalState, RoundState
from python_skeleton.skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from python_skeleton.skeleton.bot import Bot
from python_skeleton.skeleton.runner import parse_args, run_bot
from python_skeleton.buckets import get_bucket

from train_py_poker_engine.information_set import InformationSet

import random
import math
import eval7

NUM_ACTIONS = 10
BOUNTY_RATIO = 1.5
BOUNTY_CONSTANT = 10

class History():
    '''
    Representation of history in poker game for CFR training.
    Based on RoundState (states.py) used in Pokerbots python skeleton.

    @param active Either 0 or 1 to indicate the active player
    @param roundState Representation of round state used by states.py and runner.py
        TODO: can maybe use engine.py? figure out engine.py vs states.py
    '''

    def __init__(self, active, round_state):
        self.active = active # 0 or 1
        self.round_state = round_state
        # RoundState: ['button', 'street', 'pips', 'stacks', 'hands', 'bounties', 'deck', 'previous_state']

    def generate_initial_node(start_player):
        '''
        Return History representative of beginning of round
        '''
        # deal hands at random
        full_deck = eval7.Deck()
        full_deck.shuffle()

        # Deal two hands with 2 cards each
        hand0 = [str(full_deck.cards.pop()), str(full_deck.cards.pop())]
        hand1 = [str(full_deck.cards.pop()), str(full_deck.cards.pop())]
        hands = [hand0, hand1]

        # pick bounties at random
        bounty_chars = [str(i) for i in range(2, 10)] + ['T', 'J', 'Q', 'K', 'A']
        bounties = [bounty_chars[random.randint(0, 12)], bounty_chars[random.randint(0, 12)]]

        deck = [] # unlike engine structure, we fill this as we reach chance nodes
        pips = [SMALL_BLIND, BIG_BLIND] if start_player == 0 else [BIG_BLIND, SMALL_BLIND]
        stacks = [STARTING_STACK - pips[0], STARTING_STACK - pips[1]]
        round_state = RoundState(0, 0, pips, stacks, hands, bounties, deck, None)

        return History(start_player, round_state)

    def get_active_player(self):
        '''
        Return ID of active player (either 0 or 1)
        '''
        return self.active

    def get_node_type(self):
        '''
        Returns char denoting current round state:
          'T': terminal
          'C': chance
          'D': decision
        '''
        if isinstance(self.round_state, TerminalState):
            return 'T'
        elif self.round_state.street != len(self.round_state.deck): # proceed_street was just called
            return 'C'
        else:
            return 'D'
    
    def get_utility(self, player_id):
        '''
        Returns utility of respective player if state is terminal node

        @param player_id Either 0 or 1
        '''
        assert isinstance(self.round_state, TerminalState)

        deltas = self.round_state.deltas
        bounty_hits = self.round_state.bounty_hits

        # terminal state is result of showdown, not fold, we need to calculate delta and bounty hits
        if bounty_hits == None:
            previous_state = self.round_state.previous_state
            hand0 = [eval7.Card(s) for s in previous_state.hands[0] + previous_state.deck]
            hand1 = [eval7.Card(s) for s in previous_state.hands[1] + previous_state.deck]
            score0 = eval7.evaluate(hand0)
            score1 = eval7.evaluate(hand1)
            if score0 > score1:
                delta = self.get_delta(0)
            elif score0 < score1:
                delta = self.get_delta(1)
            else:
                # split the pot
                delta = self.get_delta(2)
        else:
            delta = self.get_delta(1 if deltas[0] > deltas[1] else 0)
        
        return delta if player_id == 0 else -delta

    def get_delta(self, winner_index: int) -> int: # copy paste from engine.py
        '''Returns the delta after bounty rules are applied.

        Args:
            winner_index (int): Index of the winning player. Must be 0 (player A),
                1 (player B), or 2 (split pot).

        Returns:
            int: The delta value after applying bounty rules.
        '''
        assert winner_index in [0, 1, 2]
        assert isinstance(self.round_state, TerminalState)
        state = self.round_state.previous_state

        bounty_hit_0, bounty_hit_1 = state.get_bounty_hits()

        delta = 0
        if winner_index == 2:
            # Case of split pots
            assert(state.stacks[0] == state.stacks[1]) # split pots only happen on the river + equal stacks
            delta = STARTING_STACK - state.stacks[0]
            if bounty_hit_0 and not bounty_hit_1:
                delta = delta * (BOUNTY_RATIO - 1) / 2 + BOUNTY_CONSTANT
            elif not bounty_hit_0 and bounty_hit_1:
                delta = -(delta * (BOUNTY_RATIO - 1) / 2 + BOUNTY_CONSTANT)
            else:
                delta = 0
        else:
            # Case of one player winning
            if winner_index == 0:
                delta = STARTING_STACK - state.stacks[1]
                if bounty_hit_0:
                    delta = delta * BOUNTY_RATIO + BOUNTY_CONSTANT
            else:
                delta = state.stacks[0] - STARTING_STACK
                if bounty_hit_1:
                    delta = delta * BOUNTY_RATIO - BOUNTY_CONSTANT

        # if delta is not an integer, round it down or up depending on who's in position
        if abs(delta - math.floor(delta)) > 1e-6:
            delta = math.floor(delta) if state.button % 2 == 0 else math.ceil(delta)
        return int(delta)

    def generate_chance_outcome(self):
        '''
        Returns new History representative of sampling an outcome if state is chance node
        '''
        dealt_cards = self.round_state.hands[0] + self.round_state.hands[1] + self.round_state.deck

        # get deck of remaining cards
        full_deck = eval7.Deck()
        full_deck.shuffle()
        for card in dealt_cards:
            full_deck.cards.remove(eval7.Card(card))

        # update community cards (deck)
        new_deck = list(self.round_state.deck)
        if self.round_state.street == 3:
            for _ in range(3):
                new_deck.append(str(full_deck.cards.pop()))
        else:
            new_deck.append(str(full_deck.cards.pop()))

        new_pips = list(self.round_state.pips)
        new_stacks = list(self.round_state.stacks)
        state = RoundState(1, self.round_state.street, new_pips, new_stacks, self.round_state.hands, self.round_state.bounties, new_deck, self.round_state)
        return History(1, state) # active = button % 2

    def get_legal_actions(self):
        '''
        Returns 1x10 array representing 10 action buckets for active player, where indexed value is:
            True if action is legal
            False if action is not legal

        Actions:
            0 - Fold
            1 - Call
            2 - Check
            3 - Raise (min)
            4 - Raise (max raise/all in)
            5 - Raise (1/3 pot)
            6 - Raise (1/2 pot)
            7 - Raise (full pot)
            8 - Raise (1.5 pot)
            9 - Raise (2 pot)
        '''
        output = [False for _ in range(10)]

        legal_actions = self.round_state.legal_actions()
        min_raise, max_raise = self.round_state.raise_bounds()

        for i, action in enumerate((FoldAction, CallAction, CheckAction)):
            if action in legal_actions:
                output[i] = True

        if RaiseAction in legal_actions:
            output[3] = True
            output[4] = True

            pot_fractions = self.calculate_pot_fractions()

            for i, pot_frac in enumerate(pot_fractions):
                if min_raise < pot_frac and max_raise > pot_frac:
                    output[i+5] = True

        return output
    
    def calculate_pot_fractions(self):
        '''
        Return list of numbers corresponding to these fractions of pot: [1/3, 1/2, 1, 1.5, 2]
        All decimal raises are floored
        '''
        my_stack = self.round_state.stacks[self.active]  # the number of chips you have remaining
        opp_stack = self.round_state.stacks[1-self.active]  # the number of chips your opponent has remaining
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        pot = my_contribution + opp_contribution

        return [pot // 3, pot // 2, pot, (pot * 3) // 2, pot * 2]
    
    def generate_action_outcome(self, action_index):
        '''
        Returns new History representative of player doing action on current history

        @param player_id
        @param action Action of input player as follows:
            0 - Fold
            1 - Call
            2 - Check
            3 - Raise (min)
            4 - Raise (max raise/all in)
            5 - Raise (1/3 pot)
            6 - Raise (1/2 pot)
            7 - Raise (full pot)
            8 - Raise (1.5 pot)
            9 - Raise (2 pot)
        '''

        min_raise, max_raise = self.round_state.raise_bounds()
        actions = [FoldAction, CallAction, CheckAction, min_raise, max_raise] + self.calculate_pot_fractions()

        # sb call bb
        if action_index == 1 and self.round_state.button == 0:
            rs = RoundState(1, 3, [BIG_BLIND] * 2, [STARTING_STACK - BIG_BLIND] * 2, self.round_state.hands, self.round_state.bounties, self.round_state.deck, self.round_state)
            return History(1-self.active, rs)

        # TODO: should maybe check if input action is legal when debugging
        if action_index < 3:
            return History(1-self.active, self.round_state.proceed(actions[action_index]()))
        else:
            return History(1-self.active, self.round_state.proceed(RaiseAction(actions[action_index])))

    def get_player_info(self, player_id):
        '''
        Returns information set for input player to use in CFR algorithm
        '''
        rs = self.round_state
        bucket = get_bucket(rs.hands[player_id] + rs.deck)

        return InformationSet(bucket, rs.button, rs.street, rs.pips, rs.stacks, rs.bounties[player_id])

    def __str__(self):
        if isinstance(self.round_state, TerminalState):
            return 'Deltas: ' + str(self.round_state.deltas) + '\nBounty Hits: ' + str(self.round_state.bounty_hits) + "\n_____________"
        return 'Acti  ve: ' + str(self.active) +'\nButton: ' + str(self.round_state.button) + '\nStreet: ' + str(self.round_state.street) + '\nPips: ' + str(self.round_state.pips)  + '\nStacks: ' + str(self.round_state.stacks)  + '\nHands: ' + str(self.round_state.hands)  + '\nBounties: ' + str(self.round_state.bounties)  + '\nCommunity: ' + str(self.round_state.deck) + "\n_____________"
