'''
Information set for CFR algorithm
'''

class InformationSet():
   '''
   Representation of InformationSet in poker game for CFR training.

   @param handBucket Bucket() object representattive of player hole cards + community cards
   @param pips Number of chips bet by each player this round, rounded by 10
   @param stacks Number of chips left in each player stack, rounded by 10
   '''

   def __init__(self, bucket, pips, stacks):
      '''
      Constructor
      '''
      self.handBucket = bucket
      self.pips = tuple([round(pip/40) * 40 for pip in pips])
      self.stacks = tuple([round(stack/40) * 40 for stack in stacks])

   # def get_index(self):
   #    '''
   #    Bucket()
   #       self.bounty
   #       self.preflop
   #       self.flop
   #       self.turn
   #       self.river
   #    '''

   #    flags = [self.handBucket.bounty, self.handBucket.preflop, self.handBucket.flop, self.handBucket.turn, self.handBucket.river, self.pips[0], self.pips[1], self.stacks[0], self.stacks[1]]

   #    index = 0
   #    for i, flag in enumerate(flags):
   #       index += flag * 10**i
   #    return index
   
   def bucket_pipstacks(pipstacks):
      '''
      Buckets pips and stacks into buckets of 40 (i.e. 0-39, 40-79, ...)
      '''
      return tuple([min(9, pipstack//40) for pipstack in pipstacks])
   
   def __str__(self):
      flags = [self.handBucket.bounty, self.handBucket.preflop, self.handBucket.flop, self.handBucket.turn, self.handBucket.river, self.pips[0], self.pips[1], self.stacks[0], self.stacks[1]]
      result = ''
      for flag in flags:
         result += flag + '|'
      return result
