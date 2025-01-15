'''
Simple example pokerbot, written in Python.
'''
from python_skeleton.skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from python_skeleton.skeleton.states import GameState, TerminalState, RoundState
from python_skeleton.skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from python_skeleton.skeleton.bot import Bot
from python_skeleton.skeleton.runner import parse_args, run_bot
from information_set import InformationSet
from python_skeleton.buckets import get_bucket

from python_skeleton.calculate_winrates import *

import random
import math
import eval7

NUM_ACTIONS = 10

class History():
    '''
    Representation of history in poker game for CFR training.
    Based on RoundState (states.py) used in Pokerbots python skeleton.

    @param active Either 0 or 1 to indicate the active player
    @param roundState Representation of round state used by states.py and runner.py
        TODO: make sure that grabbing "illegal information" works
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
        bounties = [bounty_chars(random.randint(0, 12)), bounty_chars(random.randint(0, 12))]

        deck = [] # unlike engine structure, we fill this as we reach chance nodes
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]
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

        # terminal state is result of showdown, not fold, we need to calculate delta and bounty hits
        if self.round_state.bounty_hits == None:
            # get deltas
            previous_state = self.round_state.previous_state
            hand0 = [eval7.Card(s) for s in previous_state.hands[0] + previous_state.deck]
            hand1 = [eval7.Card(s) for s in previous_state.hands[1] + previous_state.deck]
            winner = eval7.evaluate(hand0) < eval7.evaluate(hand1)
            delta = previous_state.stacks[0] - STARTING_STACK if winner == 1 else STARTING_STACK - previous_state.stacks[1]
            self.round_state.deltas = [delta, -delta]

            # get bounty hits
            self.round_state.bounty_hits = previous_state.get_bounty_hits()

        player_delta = self.round_state.deltas[player_id]

        if self.round_state.bounty_hits[0] and self.round_state.deltas[0] > 0 or self.round_state.bounty_hits[1] and self.round_state.deltas[1] > 0:
            return player_delta * 1.5 + 10
        else:
            return player_delta

    def generate_chance_outcome(self):
        '''
        Returns new History representative of sampling an outcome if state is chance node

        Should only be called if street < 5
        '''
        dealt_cards = self.hands[0] + self.hands[1] + self.deck

        # get deck of remaining cards
        full_deck = eval7.Deck()
        full_deck.shuffle()
        for card in dealt_cards:
            full_deck.cards.remove(eval7.Card(card))

        assert(self.round_state.street < 5)

        # update community cards (deck)
        if self.round_state.street == 0:
            for _ in range(3):
                self.round_state.deck.append(str(full_deck.cards.pop()))
        else:
            self.round_state.deck.append(str(full_deck.cards.pop()))


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
