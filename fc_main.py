"""fc_main.py
Author = Richard D. Fears
Created = 2017-07-20
LastModified = 2017-07-25
Description = Main file of the Flashcard program, which allows creation of flashcard decks,
	running through said decks, and running through the decks intelligently (i.e. based on how
	well you answer each of the flashcards).
"""

import os
import re, pickle, csv, random
from consolemenu import ConsoleMenu
from fc_set import FlashcardSet
from fc_card import FlashcardCard

def setnameToFilename (setname):
	"""setnameToFilename helper function
	Just a helper function so that I don't have to change 5 places when I change my
	mind about how the filenames are built.
	"""
	return setname+'.flashcards'

def setnameToQuestionFilename (setname):
	"""setnameToQuestionFilename helper function
	Just a helper function so that I don't have to change 5 places when I change my
	mind about how the filenames are built.
	"""
	return setname+'-questions.csv'

class FlashcardMain:
	"""FlashcardMain class
	Driver class for Flashcard program.
	"""

	def __init__ (self):
		pass

	def run (self):
		"""run function
		Main driver function for Flashcard program. Reads flashcard JSON files from script
		directory and presents them in a menu for the user, along with an option to create a new
		one. Once the flashcard file is loaded, the user is presented with the options to run,
		smart run, or edit the flashcards.
		"""
		# Choose a file and load the flashcard set
		self._chooseFile()
		print()

		# Now the state machine, largely run by the states themselves
		mainstate = FCStateMainMenu(self._set)
		currstate = mainstate
		while currstate != None:
			currstate.enter()
			while currstate.next == currstate:
				currstate.run()
			# Swap to the new state before running the old state's exit function,
			# in case it changes the next
			oldstate = currstate
			currstate = oldstate.next
			oldstate.exit()
			oldstate = None

		# Done with program, spit out the file
		with open(setnameToFilename(self._set.getSetName()),'wb') as picklefile:
			pickle.dump(self._set,picklefile)

	def _chooseFile (self):
		"""_chooseFile internal function
		Presents the user with a list of flashcard files in the current directory and asks
		them to select one of them. It then loads that file into a FlashcardSet and sets
		that internal variable.
		"""
		# Find all the flashcard files in the current directory
		validfilepattern = re.compile(setnameToFilename('(.*)'))
		allfiles = os.listdir()
		validfiles = []
		for f in allfiles:
			match = validfilepattern.match(f)
			if match:
				validfiles.append(match.group(1))
		filechoices = dict(enumerate(validfiles,1))

		# Ask the user which file to load, providing an option for adding a new file
		choice = ConsoleMenu.static_quickChoice(filechoices,
			{'manual':True,'manual_value':'Create new file','manual_prompt':'New file name: '})
		setname = choice[1]
		filename = setnameToFilename(setname)

		# Now unpickle the file, or initialize a default flashcard set
		if setname not in validfiles:
			self._set = FlashcardSet(setname)
		else:
			with open(filename,'rb') as pickledfile:
				self._set = pickle.load(pickledfile)

class FCState:
	"""FCState class
	A simple state for use in the main driver's state machine. Intended as a base class for
	the various states defined below.
	Each state class should define the functions init, enter, run, and exit, and should set
	the object attribute 'next' to the next state object (if run should be run again, set next
	to self). If next is set to None, the program will exit.
	"""

	def __init__ (self):
		"""FCState constructor
		This should setup any object attributes needed for the state to properly function.
		It should also initialize next.
		"""
		self.next = None

	def enter (self):
		"""enter function
		This runs once when the state machine transitions to this state.
		Default behavior is to set next to self, so that run actually runs.
		"""
		self.next = self

	def run (self):
		"""run function
		This runs until the next state is not this state. Note that this will never run
		if the init or enter functions do not set next to this state.
		"""
		pass

	def exit (self):
		"""exit function
		This runs once when the state machine transitions away from this state.
		Default behavior is to print a blank line (to space state menus) and set the next
		to None, to clean up memory.
		"""
		print()
		self.next = None

class FCStateMainMenu (FCState):
	"""FCStateMainMenu class
	The state which handles the main menu of the program. Displays a menu for the user,
	along with the name of the currently-loaded set, gathers the choice from the user,
	and then directs to the appropriate state. This state object is expected to persist until
	the end of the program.
	"""

	def __init__ (self, cardset):
		"""FCStateMainMenu constructor
		This constructor accepts a FlashcardSet, which it stores in an internal variable for
		future reference.
		"""
		super().__init__()
		self._set = cardset

	def enter (self):
		"""enter function
		Prints a simple message that this is the main menu and that setname set is loaded.
		Also writes out the flashcard file each time we enter, so that we don't have to quit
		to save our progress.
		"""
		super().enter()
		print("***Main Menu***")
		print("Flashcard set: "+self._set.getSetName())

		# Done with program, spit out the file
		with open(setnameToFilename(self._set.getSetName()),'wb') as picklefile:
			pickle.dump(self._set,picklefile)

	def run (self):
		"""run function
		Displays a menu of a few possible options and allows the user to pick among them.
		Includes importing a CSV, manually editing cards, running the cards, and displaying
		stats.
		"""
		choices = {
			'i':"Import Cards",
			'e':"Export Cards",
			'c':"Edit cards",
			'o':"Edit options",
			'r':"Run cards",
			's':"Show stats"
		}
		options = {
			'abstain':True,
			'abstain_key':'q',
			'abstain_value':"Quit"
		}

		choice = ConsoleMenu.static_quickChoice(choices,options)

		# If the user wants to exit, set the next to None and do nothing else
		if choice == None:
			self.next = None
		else:
			# Call the appropriate state, based on the user's choice
			if choice[0] == 'i':
				self.next = FCStateImportCSV(self._set,self)
			elif choice[0] == 'e':
				self._exportCSV()
			elif choice[0] == 'c':
				self.next = FCStateEditCardsMain(self._set,self)
			elif choice[0] == 'o':
				print('Go to '+choice[1])
			elif choice[0] == 'r':
				self.next = FCStateRunCardsMenu(self._set,self)
			elif choice[0] == 's':
				self._showStats()

	def _exportCSV (self):
		"""_exportCSV internal function
		Exports all the questions and answers to a file with filename [setname]-questions.csv.
		This will overwrite any existing file with the same name.
		"""
		cardsExported = 0
		cards = self._set.getAllCards()
		# Write to [setname]-questions.csv; make sure to use newline='' to help with multi-line
		# questions/answers
		filename = setnameToQuestionFilename(self._set.getSetName())
		with open(filename,'w',newline='') as qfile:
			csvwriter = csv.writer(qfile,delimiter='~')
			# For each card, write out the question and all answers, then increment the number
			# of cards exported
			for card in cards:
				csvwriter.writerow([card._question]+card._valid_answers)
				cardsExported += 1
		# Let the user know how many questions were exported and where
		print("{} questions exported to {}".format(cardsExported,filename))

	def _showStats (self):
		"""_showStats internal function
		Called when the user selects the 's' option. Prints out the stats to both a file and
		the screen.
		"""
		totalScore = 0
		totalAttempts = 0
		cardCountAdjustment = 0
		minScore = None
		cardsWithMinScore = 0
		minRank = None
		cardsWithMinRank = 0
		statsfilename = self._set.getSetName()+'-fcstats.csv'
		with open(statsfilename,'w') as statsfile:
			# Print a header before going through the cards
			statsfile.write("Question~Successes~Attempts~Score~Ranking (for debug)\n")
			for card in self._set.getAllCards():
				# Add the score and attempts to the running total
				totalScore += card.score()
				totalAttempts += card._attempts
				# If we haven't attempted the card yet, don't count it for averages
				if card._attempts == 0:
					cardCountAdjustment += 1
				# Increment the minscore and minrank counts
				if minScore == None:
					minScore = card.score()
					cardsWithMinScore = 1
				elif card.score() == minScore:
					cardsWithMinScore += 1
				elif card.score() < minScore:
					minScore = card.score()
					cardsWithMinScore = 1
				if minRank == None:
					minRank = card.ranking()
					cardsWithMinRank = 1
				elif card.ranking() == minRank:
					cardsWithMinRank += 1
				elif card.ranking() < minRank:
					minRank = card.ranking()
					cardsWithMinRank = 1
				# Print the question and its stats to the file
				statsfile.write("{}~{}~{}~{}%~{}\n".format(card._question,card._correct,
					card._attempts,int(card.score()),card.ranking()))
		# Calculate the averages (weighting all cards the same)
		attemptedCards = len(self._set.getAllCards())-cardCountAdjustment
		if attemptedCards == 0:
			averageScore = 0
			averageAttempts = 0
		else:
			averageScore = totalScore/(len(self._set.getAllCards())-cardCountAdjustment)
			averageAttempts = totalAttempts/(len(self._set.getAllCards())-cardCountAdjustment)
		# And tell the user about the averages and file
		print()
		print("Full stats written to "+statsfilename)
		print("Average Score, Attempts: {:0.2f}%, {:0.2f}".format(
			averageScore,averageAttempts))
		print("{} question(s) with minimum score of {:0.2f}%".format(
			cardsWithMinScore,minScore))
		print("{} question(s) with minimum rank of {:0.4f}".format(
			cardsWithMinRank,minRank))
		print()

class FCStateImportCSV (FCState):
	"""FCStateImportCSV class
	Displays a list of CSV files in the directory for the user to choose. Then imports
	questions/answers from the CSV file. It works by appending, not replacing.
	"""

	def __init__ (self, cardset, mainmenu):
		"""FCStateImportCSV constructor
		This constructor accepts a FlashcardSet, which it stores in an internal variable for
		future reference. It also stores the mainmenu, so it can go back there.
		"""
		super().__init__()
		self._set = cardset
		self._mainmenu = mainmenu

	def enter (self):
		"""enter function
		Just displays a header
		"""
		super().enter()
		print("***Import Cards***")

	def run (self):
		"""run function
		Displays a list of .csv files in the directory, allows the user to choose one of them,
		and then imports the questions from that .csv.
		"""
		# Provide the user with instructions
		print("This process imports a list of questions and valid/correct answers from a CSV")
		print("file. Columns should be separated by the ~ symbol. The first column is the")
		print("question. The second column is the correct answer. For multiple-choice questions,")
		print("you can specify the other choices in the 3rd, 4th, 5th, etc. columns.")
		print("The question type (boolean, word, freeform, multiple-choice, etc.) is")
		print("automatically determined based on the form of the answers, but it can be manually")
		print("changed later by editing the cards.")
		print()

		# Find all the CSV files in the current directory
		validfilepattern = re.compile('.*\.[Cc][Ss][Vv]')
		allfiles = os.listdir()
		validfiles = []
		for f in allfiles:
			match = validfilepattern.match(f)
			if match:
				validfiles.append(f)
		filechoices = dict(enumerate(validfiles,1))

		# Ask the user which file to load, providing an option to cancel
		choice = ConsoleMenu.static_quickChoice(filechoices,
			{'abstain':True,'abstain_key':'q','abstain_value':'Cancel Card Import'})
		if choice == None:
			self.next = self._mainmenu
			return

		# Now that we have a filename, let's read it in
		filename = choice[1]
		with open(filename,'r') as csvfile:
			csvreader = csv.reader(csvfile,delimiter='~')
			linenumber = 0
			questionsimported = 0
			for row in csvreader:
				linenumber += 1
				if len(row) < 2:
					print("Error on line "+str(linenumber)+": Not enough fields. Need at " \
						+"least 2 (question and correct answer).")
					continue
				else:
					question = row[0].strip()
					valid_answers = []
					for answer in row[1:]:
						if answer.strip() != "":
							valid_answers.append(answer.strip())
					cardadded = self._set.addCard(FlashcardCard(question,valid_answers))
					if cardadded:
						questionsimported += 1
					else:
						print("Warning on line "+str(linenumber)+": Question already exists " \
							+"in flashcard set: "+question)
			print(str(questionsimported)+" questions successfully imported")

		# We're done importing, return to the main menu
		self.next = self._mainmenu

class FCStateRunCardsMenu (FCState):
	"""FCStateRunCardsMenu class
	The main menu for running flashcards. Provides a few hard-coded options as well as an
	option to build your own.
	"""

	def __init__ (self, cardset, mainmenu):
		"""FCStateRunCardsMenu constructor
		This constructor accepts a FlashcardSet, which it stores in an internal variable for
		future reference. It also stores the mainmenu, so it can go back there.
		"""
		super().__init__()
		self._set = cardset
		self._mainmenu = mainmenu

	def enter (self):
		"""enter function
		Just displays a header.
		"""
		super().enter()
		print("***Run Cards Menu***")

	def run (self):
		"""run function
		Displays the number of cards in the set. Displays a menu of possible runs, with an
		option to customize. Then switches to the RunCardList state to actually run.
		"""
		choices = {
			'1':"Run the lowest-scoring card",
			'5':"Run 5 lowest-scoring cards",
			'10':"Run 10 lowest-scoring cards",
			'10r':"Run 10 random cards",
			'15':"Run 10 lowest-scoring cards with 5 random cards",
			'third':"Run the lowest-scoring 1/3rd of the cards",
			'half':"Run the lowest-scoring 1/2 of the cards",
			'all':"Run all the cards in the order they were added",
			'endless':"Run the lowest-ranking card in the set until you quit",
			'custom':"Define a custom run of the cards"
		}
		options = {
			'abstain':True, 'abstain_key':'q', 'abstain_value':'Return to main menu',
			'intro_text':str(len(self._set.getAllCards()))+" cards in set. " \
				+"Choose a run from the list below"
		}
		choice = ConsoleMenu.static_quickChoice(choices,options)

		if choice == None:
			self.next = self._mainmenu
			return

		# Put together a list of cards to run, based on the user choice
		cardlist = []
		if choice[0] == '1':
			cardlist = self._set.getSortedCards()
		elif choice[0] == '5':
			cardlist = self._set.getSortedCards(5)
		elif choice[0] == '10':
			cardlist = self._set.getSortedCards(10)
		elif choice[0] == '10r':
			cardlist = self._set.getSortedCards(0,10)
		elif choice[0] == '15':
			cardlist = self._set.getSortedCards(10,5)
		elif choice[0] == 'third':
			cardlist = self._set.getSortedCards(int(len(self._set.getAllCards())/3))
		elif choice[0] == 'half':
			cardlist = self._set.getSortedCards(int(len(self._set.getAllCards())/2))
		elif choice[0] == 'all':
			cardlist = self._set.getAllCards()[:]
		elif choice[0] == 'endless':
			# Endless starts with just one card
			cardlist = self._set.getSortedCards()
		elif choice[0] == 'custom':
			inputranked = input("Enter the number of lowest-scoring cards to run: ")
			inputrandom = input("Enter the number of random cards to run: ")
			numranked = None
			numrandom = None
			try:
				numranked = int(inputranked)
				numrandom = int(inputrandom)
			except:
				print("ERROR: One of the inputs above was not an integer. Returning to run menu.")
				return
			cardlist = self._set.getSortedCards(numranked,numrandom)

		# Randomize the order of the cards, so we're not always going by rank
		cardlist.sort(key=lambda k: random.random())

		# We now have a cardlist, so kick off the run
		# If in endless mode, pass in the full flashcard set as well, to indicate so
		if choice[0] == 'endless':
			self.next = FCStateRunCardList(cardlist,self._mainmenu,self._set,endless)
		else:
			self.next = FCStateRunCardList(cardlist,self._mainmenu,self._set)

class FCStateRunCardList (FCState):
	"""FCStateRunCardList class
	Runs through a provided card list, using the run() loop to allow resetting the card list
	between questions, and quitting after any question.
	"""

	def __init__ (self, cardlist, mainmenu, cardset, endless=False):
		"""FCStateRunCardList constructor
		This constructor accepts a list of cards, a reference to the main menu state, the
		full flashcard set, and optionally an indication for endless mode.
		"""
		super().__init__()
		self._cardlist = cardlist
		self._mainmenu = mainmenu
		self._set = cardset
		self._endless = endless
		self._answered = 0
		self._passed = 0
		self._index = 0

	def start (self):
		"""start function
		Initializes the number of answered questions, the number of passed questions,
		and the starting card index.
		"""
		super().start()
		print("Answer each question as indicated. You may return to the main menu at any time")
		print("by entering 'q' instead of an answer.")
		self._answered = 0
		self._passed = 0
		self._index = 0

	def run (self):
		"""run function
		Uses the type of question to ask in the correct way (choice menu vs. simple input).
		Display the correct answer.
		If the answer type uses confirm, ask the user if they answered correctly.
		Then record the stats and advance to the next question (for endless mode, this means
		generating a new card list with size 1 and NOT advancing the index).
		"""
		# Let the user know how many questions remain, if not in endless mode
		if not self._endless:
			print("Questions remaining: {}".format(
				len(self._cardlist)-self._answered))
		# Gather the current card into a variable for ease of use
		card = self._cardlist[self._index]
		# Determine the type of question and call the appropriate internal function
		if card._answer_type in ('multiple_choice','boolean'):
			answer = self._askMultipleChoice(card._question,card._valid_answers)
		else:
			answer = self._askFreeform(card._question)
		# Check if the user wants to quit
		if answer == 'q':
			self.next = self._mainmenu
			return
		# Otherwise, they answered the question
		self._answered += 1
		# Print the correct answer for the user to learn
		print("The correct answer is '"+card._valid_answers[0]+"'.")
		# Check if the question uses confirmation
		confirmed = None
		if self._set.usesUserConfirm(card):
			confirmtext = input("Did you answer the question correctly? (enter 'y' for yes, " \
				+"anything else for no): ")
			if confirmtext in ('y','Y'):
				confirmed = True
			else:
				confirmed = False
		# Inform the user whether or not the question passed
		if card.checkAnswer(answer,confirmed):
			self._passed += 1
			print("Answer marked as correct")
		else:
			print("Answer marked as incorrect")
		# Place an extra line for spacing
		print()

		# If this is endless mode, generate a new cardlist and don't update the index
		if self._endless:
			self._cardlist = self._set.getSortedCards()
		# Otherwise, if we're done answering question, return to the main menu
		elif self._index == len(self._cardlist) - 1:
			self.next = self._mainmenu
		# Finally, if we're not done, and we're not in endless mode, advance the index
		else:
			self._index += 1

	def exit (self):
		"""exit function
		Displays some quick stats regarding the user's success.
		"""
		super().exit()
		# The result should look like:
		# ********************************
		# * Passed/Answered = 5/10 = 50% *
		# ********************************
		passedpct = 0
		if self._answered > 0:
			passedpct = int(100.0 * self._passed/self._answered)
		printstr = "* Passed/Answered = {}/{} = {}% *".format(self._passed,self._answered, \
			passedpct)
		borders = '*' * len(printstr)
		print(borders)
		print(printstr)
		print(borders)
		print()

	def _askFreeform (self, question):
		"""_askFreeForm internal function
		Simply presents the user with the question and a prompt for an answer.
		Returns whatever the user input.
		"""
		print("Question: "+question)
		return input("Enter your answer (or q to return to the menu): ")

	def _askMultipleChoice (self, question, answers):
		"""_askMultipleChoice internal function
		Simply presents the user with the question and a choice menu for an answer.
		Returns the answer the user chose.
		"""
		print("Question: "+question)
		# If the question is boolean, generate a choices dict of just True and False
		if len(answers) == 1 and answers[0] in ('True','False'):
			choices = {'1':'True','2':'False'}
		# Otherwise, the answers are just what was passed to us
		# Make sure to randomize the order
		else:
			choices = dict(enumerate(sorted(answers,key=lambda k: random.random()),1))
		options = {'abstain':True,'abstain_key':'q','abstain_value':'Return to menu'}
		choice = ConsoleMenu.static_quickChoice(choices,options)

		if choice == None:
			return 'q'
		return choice[1]

class FCStateEditCardsMain (FCState):
	"""FCStateEditCardsMain class
	The main menu for editing cards. Allows the user to select a specific card or add a card.
	Future features might include filtering by type or searching by question/answer.
	"""

	def __init__ (self, cardset, mainmenu):
		"""FCStateEditCardsMain constructor
		This constructor accepts a FlashcardSet, which it stores in an internal variable for
		future reference. It also stores the mainmenu, so it can go back there.
		"""
		super().__init__()
		self._set = cardset
		self._mainmenu = mainmenu

	def enter (self):
		"""enter function
		Just displays a header, including the cardset name.
		"""
		super().enter()
		print("***Edit Cards Main Menu***")
		print("Flashcard set: "+self._set.getSetName())

	def run (self):
		"""run function
		Displays a menu of a few possible options and allows the user to pick among them.
		Includes a list of cards (shows question), an option to add a new card, and an option
		to jump back to the main menu.
		"""
		questionlist = []
		cardlist = []
		for card in self._set.getAllCards():
			questionlist.append(card._question)
			cardlist.append(card)
		choices = dict(enumerate(questionlist,1))
		options = {
			'abstain':True,
			'abstain_key':'q',
			'abstain_value':"Return to main menu",
			'manual':True,
			'manual_key':'n',
			'manual_value':"Enter a new question",
			'manual_prompt':"Enter the new question: "
		}

		choice = ConsoleMenu.static_quickChoice(choices,options)

		# If the user wants to return to main menu, set the next and do nothing else
		if choice == None:
			self.next = self._mainmenu
		else:
			# If they entered a new question
			if choice[0] == 'n':
				# Grab the new question
				question = choice[1]
				# Grab the answers from the user
				valid_answers = []
				while len(valid_answers) == 0:
					print("For freeform questions, enter the correct answer.")
					print("For True/False questions, enter 'True' or 'False' (case/spelling sensitive!).")
					print("For multiple-choice questions, enter all possible answers, starting with the correct answer.")
					print("To stop entering answers, hit enter without typing text.")
					inputtext = None
					while inputtext != "":
						inputtext = input("Enter answer: ")
						if inputtext != "":
							valid_answers.append(inputtext)
					# If the user did not enter any answers, yell at them
					if len(valid_answers) == 0:
						print("ERROR: At least one answer must be entered.")
				# From those two, we can guess the rest of the attributes to create a new card
				card = FlashcardCard(question,valid_answers)
				# Replace any existing card with the same question
				self._set.addCard(card,True)
				# We've added the card, so let's jump back to the menu again
				self.next = self
			# They chose one of the existing cards
			else:
				# Pull the card from the cardlist; note that the choice key is int by design;
				# We also need to subtract 1 because we added 1 for the choice menu
				card = cardlist[int(choice[0])-1]
				# Send the user to the Edit Card state
				self.next = FCStateEditCard(self,card)

class FCStateEditCard (FCState):
	"""FCStateEditCard class
	Shows a menu with options to edit the properties of the card.
	"""

	def __init__ (self, editcardsmain, card):
		"""FCStateEditCard constructor
		Accepts a reference to the Edit Cards main menu, and to the card we'll be editing.
		"""
		super().__init__()
		self._editcardsmain = editcardsmain
		self._card = card

	def enter (self):
		"""enter function
		Just prints a header.
		"""
		super().enter()
		print("***Edit Card***")

	def _changeQuestionText (self):
		"""_changeQuestionText internal function
		Helper function to clean up run function. Lets user change question text.
		"""
		print('Current question text: "'+self._card._question+'"')
		print('Press enter without entering text to not change the question text.')
		newtext = input('Enter new question text: ')
		if newtext != '':
			self._card._question = newtext

	def _chooseAnswer (self):
		"""_chooseAnswer internal function
		Helper function to clean up run function. Lets user choose answer to change,
		rearrange answers, or add new answer.
		"""
		choices = dict(enumerate(self._card._valid_answers,1))
		choices['c'] = 'Change correct answer'
		choices['d'] = 'Delete an answer'
		options = {
			'manual':True,
			'manual_key':'a',
			'manual_value':'Add new answer',
			'manual_prompt':'Enter new answer: ',
			'abstain':True,
			'abstain_key':'q',
			'abstain_value':'Return to edit card menu',
			'intro_text':'Choose one of the answers, or change the correct answer'
		}
		choice = ConsoleMenu.static_quickChoice(choices,options)

		# If the user chooses to return to the edit card menu, nothing needs be done
		if choice == None:
			pass
		# If the user wants to add a new answer, just add it to the list
		elif choice[0] == 'a':
			self._card._valid_answers.append(choice[1])
		# If the user wants to change the correct answer, convert to int and rearrange list
		elif choice[0] == 'c':
			inputtext = input('Enter key for correct answer (integer between 1 and ' \
				+str(len(self._card._valid_answers))+'): ')
			# By default, do nothing (if the user entered an invalid value, screw 'em)
			newcorrect = None
			try:
				newcorrect = int(inputtext)-1
			except:
				pass
			# Move the new index to the front of the list, if it's a valid index
			if newcorrect != None and newcorrect >= 0 \
				and newcorrect < len(self._card._valid_answers):
				self._card._valid_answers.insert(0,self._card._valid_answers.pop(newcorrect))
		# If the user wants to delete an answer, remove it from the list
		elif choice[0] == 'd':
			inputtext = input('Enter key for the answer to delete: ')
			deleteindex = None
			try:
				deleteindex = int(inputtext)-1
			except:
				pass
			# Delete the item, if it's a valid index
			if deleteindex != None and deleteindex >= 0 \
				and deleteindex < len(self._card._valid_answers):
				del self._card._valid_answers[deleteindex]
		# If the user picked one of the answers, allow them to edit it
		else:
			answerindex = int(choice[0])-1
			self._changeAnswer(answerindex)

	def _changeAnswerType (self):
		"""_changeAnswerType internal function
		Helper function to clean up run function. Lets user change answer type.
		"""
		choices = dict(enumerate(FlashcardSet.ANSWER_TYPES,1))
		options = {
			'abstain':True,
			'abstain_key':'q',
			'abstain_value':'Return to edit card menu',
			'intro_text':'Choose an answer type (current: '+self._card._answer_type+')'
		}
		choice = ConsoleMenu.static_quickChoice(choices,options)

		# If the user wants to quit, nothing needs be done
		if choice == None:
			pass
		# Otherwise, set the new answer type
		else:
			self._card._answer_type = FlashcardSet.ANSWER_TYPES[int(choice[0])-1]

	def _changeOverrideConfirm (self):
		"""_changeOverrideConfirm internal function
		Helper function to clean up run function. Lets user change override confirm.
		"""
		choices = {'1':True,'2':False}
		options = {
			'abstain':True,
			'abstain_key':'q',
			'abstain_value':'Return to edit card menu',
			'intro_text':'Choose an override confirm setting (current: '+str(self._card._override_confirms)+')'
		}
		choice = ConsoleMenu.static_quickChoice(choices,options)

		# If the user wants to quit, nothing needs be done
		if choice == None:
			pass
		# Otherwise, set the new override confirm
		else:
			self._card._override_confirms = choice[1]

	def _changeAnswer (self,answerindex):
		"""_changeAnswer internal function
		Helper function to clean up run function. Lets user change answer text.
		"""
		print('Current answer text: "'+self._card._valid_answers[answerindex]+'"')
		print('Press enter without entering text to not change the answer text.')
		newtext = input('Enter new answer text: ')
		if newtext != '':
			self._card._valid_answers[answerindex] = newtext

	def run (self):
		"""run function
		Displays a menu of a few possible attributes to edit. Question, answers, confirm override,
		and answer type.
		"""
		choices = {
			'u':'Change question text (current: "'+self._card._question+'")',
			'a':'Change answers (current: "'+str(self._card._valid_answers)+'")',
			't':'Change answer type (current: "'+self._card._answer_type+'")',
			'c':'Change confirm override (current: "'+str(self._card._override_confirms)+'")'
		}
		options = {
			'abstain':True,
			'abstain_key':'q',
			'abstain_value':"Return to edit cards main menu",
		}

		choice = ConsoleMenu.static_quickChoice(choices,options)

		# If the user wants to return to main menu, set the next and do nothing else
		if choice == None:
			self.next = self._editcardsmain
		else:
			# Run a helper function based on the user choice
			if choice[0] == 'u':
				self._changeQuestionText()
			elif choice[0] == 'a':
				self._chooseAnswer()
			elif choice[0] == 't':
				self._changeAnswerType()
			elif choice[0] == 'c':
				self._changeOverrideConfirm()

if __name__ == "__main__":
	import os, sys
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	try:
		fcmain = FlashcardMain()
		fcmain.run()
	except Exception as e:
		print("ERROR!")
		print(e)
		raise e
	finally:
		input("Press enter to quit")
