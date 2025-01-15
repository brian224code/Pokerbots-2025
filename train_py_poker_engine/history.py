'''
Simple example pokerbot, written in Python.
'''
from python_skeleton.skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from python_skeleton.skeleton.states import GameState, TerminalState, RoundState
from python_skeleton.skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from python_skeleton.skeleton.bot import Bot
from python_skeleton.skeleton.runner import parse_args, run_bot

from python_skeleton.calculate_winrates import *

import random
import math
import eval7

class History():
    '''
    Representation of history in poker game for CFR training.
    Based on RoundState (states.py) used in Pokerbots python skeleton.

    Player 0 always goes first, followed by Player 1.

    @param active Either 0 or 1 to indicate the active player
    @param...
    '''

    def __init__(self, active, round_state):
        self.active = active # 0 or 1
        self.round_state = round_state
        # RoundState: ['button', 'street', 'pips', 'stacks', 'hands', 'bounties', 'deck', 'previous_state']

    def generateInitialNode():
        '''
        Return History representative of beginning of round
        '''
        # deal hands at random
        full_deck = eval7.Deck()
        full_deck.shuffle()

        # Deal two hands with 2 cards each
        hand1 = [str(full_deck.cards.pop()), str(full_deck.cards.pop())]
        hand2 = [str(full_deck.cards.pop()), str(full_deck.cards.pop())]
        hands = [hand1, hand2]

        # pick bounties at random
        bounty_chars = [str(i) for i in range(2, 10)] + ['T', 'J', 'Q', 'K', 'A']
        bounties = [bounty_chars(random.randint(0, 12)), bounty_chars(random.randint(0, 12))]

        deck = [] # unlike engine structure, we fill this as we reach chance nodes
        pips = [SMALL_BLIND, BIG_BLIND]
        stacks = [STARTING_STACK - SMALL_BLIND, STARTING_STACK - BIG_BLIND]
        round_state = RoundState(0, 0, pips, stacks, hands, bounties, deck, None)

        return History(0, round_state) # active = 0 because Player 0 always goes first
    
    
    def getActivePlayer(self):
        '''
        Return ID of active player (either 0 or 1)
        '''
        return self.active

    def getNodeType(self):
        '''
        Returns char denoting current round state:
          'T': terminal
          'C': chance
          'D': decision
        '''
        if type(self.round_state) == TerminalState:
            return 'T'
        elif (self.street == 0 and self.button > 0) or self.button > 1:  # both players acted
            return 'C' # TODO: might be more logic that would be chance; see runner.py
        else:
            return 'D'
    
    def getPayout(self, playerId):
        '''
        Returns utility of respective player if state is terminal node

        @param playerId Either 0 or 1
        '''
        assert type(self.round_state) == TerminalState

        my_delta = self.round_state.deltas[playerId]  # input player's bankroll change from this round

        return my_delta


    def generateChanceOutcome(self):
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


    def getLegalActions(self):
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
        Return tuple with following fractions of pot [1/3, 1/2, 1, 1.5, 2]
        All decimal raises are floored
        '''
        my_stack = self.round_state.stacks[self.active]  # the number of chips you have remaining
        opp_stack = self.round_state.stacks[1-self.active]  # the number of chips your opponent has remaining
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        pot = my_contribution + opp_contribution

        return [pot // 3, pot // 2, pot, (pot * 3) // 2, pot * 2]
    
    def generateActionOutcome(self, action_index):
        '''
        Returns new History representative of player doing action on current history

        @param playerId
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
        # check that it is playerId's turn

        min_raise, max_raise = self.round_state.raise_bounds()
        actions = [FoldAction(), CallAction(), CheckAction(), min_raise, max_raise] + self.calculate_pot_fractions()

        if action_index < 3:
            return History(1-self.active, self.round_state.proceed(actions[action_index]))
        else:
            return History(1-self.active, self.round_state.proceed(RaiseAction(actions[action_index])))

    def getPlayerInfo(self, playerId):
        '''
        Returns information set for input player to use in CFR algorithm
        '''
