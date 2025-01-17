from buckets import Bucket

'''
Information set for CFR algorithm
'''

class InformationSet():
   '''
   Representation of InformationSet in poker game for CFR training.

   @param handBucket Bucket() object representattive of player hole cards + community cards
   @param my_stack Number of chips left in my stack, in buckets of 40
   @param opp_stack Number of chips left in opp stack, in buckets of 40

   '''

   def __init__(self, bucket, my_stack, opp_stack):
      '''
      Constructor
      '''
      self.handBucket = bucket
      self.my_stack = InformationSet.bucket_stack(my_stack)
      self.opp_stack = InformationSet.bucket_stack(opp_stack)

   @classmethod
   def bucket_stack(cls, stack):
      '''
      Buckets stacks into buckets of 40 (i.e. 0-39, 40-79, ...)
      '''
      return min(9, stack//40)
   
   def __str__(self):
      flags = [self.handBucket.bounty, self.handBucket.preflop, self.handBucket.flop, self.handBucket.turn, self.handBucket.river, self.my_stack, self.opp_stack]
      return '|'.join([str(flag) for flag in flags])
   
   @classmethod
   def from_string(cls, string):
        flags = string.split('|')
        bucket = Bucket()
        bucket.bounty = int(flags[0])
        bucket.preflop = int(flags[1])
        bucket.flop = int(flags[2])
        bucket.turn = int(flags[3])
        bucket.river = int(flags[4])
        my_stack = int(flags[5])
        opp_stack = int(flags[6])
        return cls(bucket, my_stack, opp_stack)
