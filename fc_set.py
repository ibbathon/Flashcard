"""fc_set.py
Author = Richard D. Fears
Created = 2017-07-20
LastModified = 2017-07-26
Description = Defines the FlashcardSet class, which contains information about a set of flash
	cards.
Version 1.1 = Added instance versioning.
"""

import copy, random
from versionexception import VersionException

class FlashcardSet:
	"""FlashcardSet class
	Contains all the information about a set of flash cards, including the cards, options,
	statistics, and others. It can be initialized by passing it a dict (usually read from a file).
	"""

	CLASS_VERSION=[1,1]

	ANSWER_TYPES = ['boolean','numeric','word','text','multiple_choice']

	DEFAULT_DATA = {
		'setname':'invalid',
		'options':{
			'confirms':{
				'boolean':False,
				'numeric':True,
				'word':True,
				'text':True,
				'multiple_choice':False
			}
		},
		'cards':[
		]
	}

	def __init__ (self, setname):
		"""FlashcardSet constructor
		This constructor is only called for new flashcard sets (i.e. not from a file). It
		initializes the internal data from the default data and then sets the setname from
		the parameter.
		"""
		self._instance_version = FlashcardSet.CLASS_VERSION[:]
		self._data = copy.deepcopy(FlashcardSet.DEFAULT_DATA)
		self._data['setname'] = setname

	def __setstate__ (self, state):
		"""unpickler
		This function unpacks the unpickled data into this instance, but first checks to make
		sure it is the right version. If the data is a higher version than the class (i.e. if
		the user has an older version of the program), it fires a version exception. If the
		data is a lower version than the class, the data is upgraded if possible. If it's not,
		then it fires a version exception.
		"""
		# If the instance version is not in the state, default to the lowest possible
		if '_instance_version' not in state:
			state['_instance_version'] = [0]
		# If the instance version is not comparable to my version type, exit now
		try:
			state['_instance_version'] > [0]
		except:
			raise VersionException(VersionException.BAD_TYPE,state['_instance_version'])

		# If the data is from a later version of the program, we won't know how to import it,
		# so just die
		if state['_instance_version'] > self.CLASS_VERSION:
			raise VersionException(VersionException.TOO_NEW,
				state['_instance_version'],self.CLASS_VERSION)

		# Now we need to run through each of the versions, in order, to see if we need those
		# new features for this data
		if state['_instance_version'] < [1,1]:
			# Version 1.1 just introduced the version numbering, so just update the instance v
			state['_instance_version'] = [1,1]

		# We've completed all of our version updates; time to import the data into this object
		self.__dict__.update(state)

	def getSetName (self):
		return self._data['setname']

	def getSortedCards (self, numcards=1, numrandomcards=0):
		"""getSortedCards function
		Sorts the cards by ascending success ratio and at random. Then returns numcards cards
		from the success-ratio-sorted list and numrandomcards from the random-sorted list.
		Note that the two lists of cards may have duplicates in each other.
		"""
		successlist = sorted(self._data['cards'],key=lambda k: (
			# Use the ranking function of the card, which should allow low-attempt,
			# high-correct questions to occasionally pop up
			k.ranking(),
			# Also sort at random, so that we never have the same order for cards with the
			# same success ratio
			random.random()
		))
		randomlist = sorted(self._data['cards'],key=lambda k: random.random())

		return successlist[:numcards] + randomlist[:numrandomcards]

	def getAllCards (self):
		"""getAllCards function
		Returns a reference to the full cards list. Primarily used when editing the cards.
		"""
		return self._data['cards']

	def addCard (self, newcard, replaceduplicate = False):
		"""addCard function
		Adds the provided newcard to the list of cards. If the card's question is already in
		the list, then the behavior is dependent on replaceduplicate. If False, nothing is done.
		If True, then the card in the list with that question is removed and the new card is
		added.
		Returns True if card added successfully. Returns False otherwise (i.e. if the card
		is a duplicate and we don't want to replace duplicates.
		"""
		# If the new card's question is not in the list, just go ahead and add it
		if newcard not in self._data['cards']:
			self._data['cards'].append(newcard)
			return True
		# If the new card's question is in the list, and we want to replace it,
		# then remove the old card and add the new one
		elif replaceduplicate:
			self._data['cards'].remove(newcard)
			self._data['cards'].append(newcard)
			return True
		return False

	def usesUserConfirm (self, card):
		"""usesUserConfirm function
		Gathers the card's answer type (multiple-choice, text, number, etc.) and checks the
		appropriate option for that in this set. Note that the card can override this setting.
		"""
		if card._override_confirms != None:
			return card._override_confirms
		else:
			return self._data['options']['confirms'][card._answer_type]
