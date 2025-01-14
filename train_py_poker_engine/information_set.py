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

class InformationSet():
    '''
    Representation of InformationSet in poker game for CFR training.

    TODO: update structure depending on bucketer function and what we decide to do for sigma_t

    @param player Either 0 or 1 to denote Player 0's info or Player 1's info
    @param active Either 0 or 1 to indicate the active player
    @param...
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.active = 0 # 0 or 1
        # player, handStrength (bucket), button, street, stacks, bounty