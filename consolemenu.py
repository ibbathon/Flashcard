"""consolemenu.py
Author = Richard D. Fears
Created = 2017-07-20
LastModified = 2017-07-21
Description = Provides the class ConsoleMenu, which provides a quick console-input-based menu
	to gather user input. Options are available to allow (for example) manually-entered choices
	and choice refusal.
"""

class ConsoleMenu:
	"""ConsoleMenu class
	Creates a quick menu from a dictionary of choices and a dictionary of
	options. The menu can then be displayed and user-input gathered.
	"""
	DEFAULT_OPTIONS = {
		'manual':False,
		'abstain':False,
		'ignore_case':True,
		'choice_suffix':') ',
		'intro_text':'Choose an option from below',
		'input_text':'Enter your choice: ',
		'abstain_key':'998',
		'abstain_value':'No choice',
		'manual_key':'999',
		'manual_value':'Manually enter value',
		'manual_prompt':'Enter a value: ',
		'invalid_entry_error':'Not a valid choice. Please choose from the keys on the left.'
	}
	OPTIONS_TYPES = {
		'manual':type(True),
		'abstain':type(True),
		'ignore_case':type(True),
		'choice_suffix':type(''),
		'intro_text':type(''),
		'input_text':type(''),
		'abstain_value':type(''),
		'manual_value':type(''),
		'manual_prompt':type(''),
		'invalid_entry_error':type('')
	}

	DEFAULT_CHOICE_KEY = '1'
	DEFAULT_CHOICE_VALUE = 'Nothing'

	def __init__ (self, choices={}, options={}):
		"""ConsoleMenu constructor
		Creates internal choices and options dictionaries based on the parameters.
		There must always be at least one choice, and this constructor will add a default one
		if none is present. Options have defaults defined at the class level.
		See ConsoleMenu.DEFAULT_OPTIONS for the list of valid options and their defaults.

		choices must be a dictionary mapping user-input keys to values. The keys will
		be converted to strings before storing in the internal choices, for ease of comparison
		to the user input. When the user makes a choice, both the key and value will be returned
		in a tuple. Note that the values will not be converted to strings.

		options is a dictionary of the particular options for this menu. e.g.
		{'manual':True}
		Only valid options will be read from the dictionary, and any invalid values will be
		converted to the defaults.

		CAUTION: If you are allowing the user to enter a manual choice or skip the choices,
		either make sure the choices you're passing in do not conflict with the default keys
		for those choices, or pass in alternative keys for said choices. The manual/skip key/value
		pairs *will* overwrite whatever you passed in for the choices.
		"""
		# Parameters can be defaulted, but don't accept non-dictionaries
		if type(choices) != type({}):
			raise TypeError("First parameter for ConsoleMenu constructor must be a dictionary")
		if type(options) != type({}):
			raise TypeError("Second parameter for ConsoleMenu constructor must be a dictionary")

		# Initialize the user's choice tuple
		self.userchoice = None

		# Initialize the internal choices/options
		self._choices = {}
		self._options = {}

		# Run through the choices, converting the keys to strings and storing them in the internal
		for choice,description in choices.items():
			self._choices[str(choice)] = description

		# Run through all the possible options (defined in DEFAULT_OPTIONS), check if they're
		# in the options parameter, add them to the internal options if they are, and set them
		# to default if they're not
		for option,default in ConsoleMenu.DEFAULT_OPTIONS.items():
			# We'll also want to make sure the option is the right type,
			# if we're concerned about that
			optiontype = None
			if option in ConsoleMenu.OPTIONS_TYPES.items():
				optiontype = ConsoleMenu.OPTIONS_TYPES[option]

			# If the options parameter contains the option, and it's the right type,
			# then add it to the internal options
			if option in options and (optiontype == None or type(options[option]) == optiontype):
				self._options[option] = options[option]
			# Otherwise, set it to the default
			else:
				self._options[option] = default

		# Check the options for required/manual and add the appropriate keys to the internal
		# choices dictionary
		if self._options['manual']:
			choice = self._options['manual_key']
			description = self._options['manual_value']
			self._choices[choice] = description
		if self._options['abstain']:
			choice = self._options['abstain_key']
			description = self._options['abstain_value']
			self._choices[choice] = description

		# It's possible to pass in a blank dictionary; if that is the case, then toss in a
		# default choice. We wait until now, because abstain or manual may be options.
		if len(self._choices) == 0:
			self._choices[ConsoleMenu.DEFAULT_CHOICE_KEY] = ConsoleMenu.DEFAULT_CHOICE_VALUE

	def displayChoices (self):
		for choice in self._choices:
			print(choice+self._options['choice_suffix']+str(self._choices[choice]))

	def gatherUserChoice (self):
		"""gatherUserChoice function
		Presents user with a list of choices and asks them to input one of them. Depending
		on the options set, the user may be required to answer, may be able to enter a custom
		choice, and may not need to enter case sensitive choices. After user input has been
		gathered and validated, it will be stored in the self.userchoice attribute.
		"""
		donechoosing = False
		while not donechoosing:
			# Print out the choices and gather the user input
			print(self._options['intro_text'])
			self.displayChoices()
			textchoice = input(self._options['input_text'])
			# If it's not valid, print out an error
			if textchoice not in self._choices:
				print(self._options['invalid_entry_error'])
			# Otherwise, the user chose a valid choice
			else:
				# If it's the manual entry choice, ask the user for input, and store their text
				if self._options['manual'] and textchoice == self._options['manual_key']:
					manualtext = input(self._options['manual_prompt'])
					self.userchoice = (textchoice,manualtext)
				# If it's the abstain choice, just set the userchoice to null
				elif self._options['abstain'] and textchoice == self._options['abstain_key']:
					self.userchoice = None
				# Otherwise, set the userchoice to the tuple of the key and value
				else:
					self.userchoice = (textchoice,self._choices[textchoice])
				# Regardless of choice, it's valid, so we're done
				donechoosing = True

	@staticmethod
	def static_quickChoice (choices={}, options={}):
		consolemenu = ConsoleMenu(choices,options)
		consolemenu.gatherUserChoice()
		return consolemenu.userchoice
