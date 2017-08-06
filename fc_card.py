"""fc_card.py
Author = Richard D. Fears
Created = 2017-07-21
LastModified = 2017-07-26
Description = Defines the FlashcardCard class, which stores information on a single flashcard.
Version 1.1 = Added instance versioning.
"""

from versionexception import VersionException

class FlashcardCard:
	"""FlashcardCard class
	Stores information on a single flashcard, including the question, type of question, answer(s),
	and statistics (e.g. number of times answered, number of times answered correctly, etc.).
	"""

	CLASS_VERSION=[1,1]

	def __init__ (self, question, valid_answers, answer_type=None, override_confirms=None):
		"""FlashcardCard constructor
		Sets the question, answer type, valid answer(s), and confirmation override from the
		parameters. Also initializes statistics to 0/0.
		Note that question and answer_type should be strings, valid answers should be a
		list of strings, and override_confirms should be a boolean.
		"""
		self._instance_version = self.CLASS_VERSION[:]

		self._question = question
		self._valid_answers = valid_answers

		# If the answer type was not provided, guess it
		if answer_type == None:
			answer_type = self._guessAnswerType()

		self._answer_type = answer_type
		self._override_confirms = override_confirms

		self._attempts = 0
		self._correct = 0

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

	def __eq__ (self, other):
		"""FlashcardCard equality comparison
		Two cards are considered equal if they have the same question.
		"""
		return self._question == other._question

	def ranking (self):
		"""ranking function
		Returns a number which can be ranked to sort the cards, so that the user sees questions
		they need more practice on.
		At the moment, this returns correct*correct/attempts, which should float some of the
		low-attempt, high-correct questions to the top of the list, while keeping most of the
		low-success questions in rotation.
		"""
		if self._attempts == 0:
			return 0
		return self._correct*self._correct/self._attempts

	def score (self):
		"""score function
		Returns the success percentage.
		"""
		if self._attempts == 0:
			return 0
		return 100.0 * self._correct/self._attempts

	def checkAnswer (self, answer_text, confirmed = None):
		"""checkAnswer function
		Handles incrementing the correct and attempts counters, based on whether or not the
		answer_text is correct. If confirmed is provided (and a boolean), then it skips
		checking the answer and just uses the value of confirmed to determine whether or not
		it increments correct.
		Returns True if correct was incremented; False otherwise.
		"""
		increment_correct = False
		# Always increment attempts
		self._attempts += 1
		# Check confirmed first so we don't waste time on the rest
		if type(confirmed) == type(bool()):
			if confirmed:
				increment_correct = True
		# If confirmed was not provided, we need to check the answer ourselves
		# The first item in valid_answers is always the correct answer
		elif answer_text == self._valid_answers[0]:
			increment_correct = True

		if increment_correct:
			self._correct += 1
			return True
		else:
			return False

	def _guessAnswerType (self):
		"""_guessAnswerType internal function
		Guesses the answer type based on the valid answers.
		"""
		# Check if the first answer is a number, for later use
		isnum = False
		try:
			float(self._valid_answers[0])
			isnum = True
		except:
			pass
		# Now interpret the answer list to guess the answer type
		if len(self._valid_answers) > 1:
			answer_type = 'multiple_choice'
		elif self._valid_answers[0] == 'True' or self._valid_answers[0] == 'False':
			answer_type = 'boolean'
		elif isnum:
			answer_type = 'numeric'
		elif ' ' not in self._valid_answers[0]:
			answer_type = 'word'
		else:
			# If none of the above are true, go with the generic text
			answer_type = 'text'

		return answer_type
