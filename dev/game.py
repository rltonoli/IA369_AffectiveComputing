# -*- coding: utf-8 -*-
"""
Created on Oct 2019

@authors: Giancarlo Schaffer Torres Junior; Liz Mercedes Falcón Rivadulla; Rodolfo Luis Tonoli
"""
import numpy as np
from random import shuffle, choice, uniform
from copy import deepcopy
import matplotlib.pyplot as plt


class Random:
    def get(value):
        """
        Chance. Value = 0.8 = 80% chance
        """
        if value < 0 or value > 1:
            raise ValueError
        else:
            value = 1-value
            return choice(np.clip([int(i/(value*10)) for i in range(10)],0,1))


def clamp(value, minvalue, maxvalue):
    return max(min(maxvalue, value), minvalue)


class Personality:
    def __init__(self, haste, memory, selfcontrol):
        self.haste = haste
        self.memory = memory
        self.selfcontrol = selfcontrol


class Emotion:
    def __init__(self, valence, arousal, frozen=False):
        self.valence = valence
        self.arousal = arousal
        self.frozen = frozen

    def update(self, selfcontrol, event):
        if not self.frozen:
            self.valence = clamp(self.valence + event.valence, -1, 1)
            self.arousal = clamp(self.arousal + event.arousal * (1 - selfcontrol), -1, 1)

class Event:
    events = []

    def __init__(self, name, description, valence, arousal):
        self.name = name
        self.description = description
        self.valence = valence
        self.arousal = arousal
        self.events.append(self)

    @classmethod
    def getEvent(cls, name):
        for event in cls.events:
            if name == event.name:
                return event
        raise Exception


class Player:

    def __init__(self, name, personality=Personality(1,1,1), emotion=Emotion(0,0), amountstrategy='random', willtodoubt=0.1, willtobluff=0.5):
        self.name = name
        self.hand = [] #list of cards

        self.emotion = emotion
        self.personality = personality

        #Emotions/sort of
        self.handvisible = [] #list of cards that may be visible to other players
        self.hvcardround = [] #the round number when the card was added to the hand visible
        self.roundmemory = 0
        self.amountstrategy = amountstrategy
        self.willtodoubt = willtodoubt
        self.willtobluff = willtobluff

        #Stats
        self.won = 0
        self.gamewin = 0
        self.roundswin = 0
        self.doubts = 0
        self.rightdoubts = 0
        self.bluffs = 0
        self.bluffslost = 0
        self.log_arousal = []
        self.log_valence = []

    def reset(self):
        self.won = 0
        self.gamewin = 0
        self.roundswin = 0
        self.doubts = 0
        self.rightdoubts = 0
        self.bluffs = 0
        self.bluffslost = 0

    # reset player game state when a new game start
    def start(self):
        self.hand = []
        self.handvisible = []

    def react2event(self, event):
        """
        Update emotions accordingly to the event.

        Parameters
        ----------
        event : Event
            Event object

        Returns
        -------
        None.

        """
        self.log_valence.append(event.valence)
        self.log_arousal.append(event.arousal)
        self.emotion.update(self.personality.selfcontrol, event)

    def pickcard(self):
        #Pick a card of the hand
        return choice(self.hand)

    def chooseamount(self, card, printstats=True):

        total = self.hand.count(card)
        count = 1

        # if the amount of cards in hand is greater that 1: calculate, else play 1 card
        if total > 1:
            if not self.emotion.frozen:
                count = total * (self.personality.haste + self.emotion.arousal * (1 - self.personality.selfcontrol))
                # the amount of cards to play has to be in the range of 1 and the total amount of this card, and has to be integer
                count = round(clamp(count, 1, total))
            # if the emotions are frozen pick a random amount of card
            else:
                count = choice(np.arange(total)) + 1

        if printstats:
            print("True cards count: %s with haste: %s, selfcontrol: %s and arousal %s" % (
            count, self.personality.haste, self.personality.selfcontrol, self.emotion.arousal))

        return count

        # #Choose the amount of cards to play
        # if self.amountstrategy=='aggressive':
        #     return self.hand.count(card)
        # elif self.amountstrategy=='cautious':
        #     return 1
        # elif self.amountstrategy=='random':
        #     return choice(np.arange(self.hand.count(card)))+1
        # else:
        #     raise Exception

    def chooseamountbluff(self, printstats=True):

        total = len(self.hand)
        max = min(total, 4)
        count = 1

        # # if the amount of cards in hand is greater that 1: calculate, else play 1 card
        if total > 1:
            if not self.emotion.frozen:
                count = max * (self.personality.haste + self.emotion.arousal * (1 - self.personality.selfcontrol))
                # the amount of cards to play has to be in the range of 1 and the total amount of this card, and has to be integer
                count = round(clamp(count, 1, max))
            # if the emotions are frozen pick a random amount of card
            else:
                count = choice(np.arange(max)) + 1

        if printstats:
            print("Bluff cards count: %s with haste: %s, selfcontrol: %s and arousal %s" %(count, self.personality.haste, self.personality.selfcontrol, self.emotion.arousal))

        return count


    def gamble(self, currentcard, printstats = True):
        #Pick a card (if it is the first npc to play)
        #and choose the amount of cards
        if not currentcard: #pick a card
            currentcard = self.pickcard()

        if not currentcard in self.hand: #bluff
            amount = self.chooseamountbluff(printstats)
            cardstostack = []
            for i in range(amount):
                # todo change the way is selected the card to play (tomada de decisao quais cartas jogar no blefe)
                bluffcard = self.hand.pop(choice(np.arange(len(self.hand)))) #pick one randomly
                cardstostack.append(bluffcard)
        else:

            #choose amount
            amount = self.chooseamount(currentcard, printstats)
            #remove from hand
            cardstoremove = [i for i,n in enumerate(self.hand) if n==currentcard] #creats a list with indexes of the card chosen
            cardstoremove = cardstoremove[:amount] #prohibits to remove from the list more cards than decided
            for i in cardstoremove[::-1]:
                self.hand.pop(i)
                cardstostack = [currentcard]*amount
        return cardstostack,currentcard

    def evaluatedoubt(self, currentcard, turn, lenHand=None):
        #Check if it will doubt
        if turn == 0: #its turn

            if currentcard:
                #if not currentcard in self.hand:
                doubt = Random.get(1-self.willtobluff)
                if doubt==0:
                    return False
                else:
                    return True
        else: #some other player's turn
            if lenHand == 0: #if the player don't have cards left, doubt it
                return True
            else:
                doubt = Random.get(self.willtodoubt)
                if doubt==0:
                    return False
                else:
                    return True

    def doubtorgamble(self, currentcard, printstats):
        #Decide wether to doubt or play
        if self.evaluatedoubt(currentcard,turn=0):
            return [],currentcard #doubt
        else:
            return self.gamble(currentcard, printstats) #gamble

    def add2hand(self, cards):
        self.hand += cards

    def add2handvisible(self, cards, roundnumber, addall = True):
        """
        Add cards recently received to the visible list.
        If addall is set to True it will add all cards from the last hand received (not the whole stack!). 
        This occurs when the current player doubted some other player that was telling the truth
        If addall is set to False it will add only the cards not previously stored in the visible list.
        This occurs when the current player bluffed and other player doubted. Example: Player had the card number 3
        in the visible list, then lost bluff with the couple of cards numbered 3 and 4. Only the card number 4 will
        be added to the list.
        """
        if addall:
            self.handvisible += cards
            self.hvcardround += [roundnumber]*len(cards)
        else:
            for card in cards:
                amountincards = cards.count(card)
                amountvisible = self.handvisible.count(card)
                if amountincards > amountvisible:
                    self.handvisible += [card]*(amountincards-amountvisible)
                    self.hvcardround += [roundnumber]*(amountincards-amountvisible)

    def removefromhandvisible(self, cards):
        """
        Remove from the visible hand the cards passed as input.
        This will occur when other player doubted but the current player was telling the truth
        """
        for card in cards:
            try:
                index = self.handvisible.index(card)
                self.handvisible.pop(index)
                self.hvcardround.pop(index)
            except:
                pass

    def totalcards(self):
        return len(self.hand)

    def printhand(self):
        print(self.hand)

    def printvisiblehand(self):
        print(self.handvisible)



class Game:

    def __init__(self, players, deck):
        """
        Parameters
        ----------
        players : list
            List of players in the game.
        deck : Deck
            Object Deck with all cards.

        Returns
        -------
        None.

        """
        self.rounds = 0
        self.players = players
        self.deck = deck
        self.roundspergame = []

        self.lastPlayer = None




    def playgame(self, maxrounds=1000, printstats=True):
        gameover = False
        while self.rounds < maxrounds and not gameover:
            if printstats:
                print(' ')
                print('Round number %i:' %(self.rounds+1))

                gameover = self.playround(printstats)

                print('-------------------------------')
                self.printhands()
                print('End of round number %i' %(self.rounds))
                if gameover:
                    self.lastPlayer.won += 1
                    print('%s won.' %self.lastPlayer.name)
                print('-------------------------------')
            else:
                gameover = self.playround(printstats)
                if gameover:
                    self.lastPlayer.won += 1
        self.roundspergame.append(self.rounds)
        print('Total rounds %i:' % self.rounds)
            # soma = 0
            # for player in self.players:
            #     soma += len(player.hand)
            # print('TOTAL CARDS IN HANDS = %i'%soma)

    def printhands(self, printvisibles=True):
        for player in self.players:
            print('%s hand:'%(player.name))
            player.printhand()
            if printvisibles:
                player.printvisiblehand()

    def printmovestats(self, player1, cards, currentcard, player2=None, doubtwinner=None):
        if not player2:
            print('%s played cards %s. Current card: %i' %(player1.name, cards, currentcard))
        else:
            print('%s doubted %s' %(player1.name, player2.name))
            if doubtwinner==player1:
                print('%s bluffed, %s was right' %(player2.name, player1.name))
            else:
                print('%s was telling the truth, %s was wrong' %(player2.name, player1.name))


    def playround(self, printstats=True):
        over = False #flag for round over (someone doubted)
        gameover = False #flag for game over (someone won)
        if self.rounds == 0:
            # Give cards
            cards = self.deck.shuffledeck()
            while len(cards) > 0:
                for player in self.players:
                    if len(cards) > 0:
                        player.hand.append(cards.pop())
            if printstats: self.printhands()

        lastHand = []
        stack = []
        currentcard = None

        #Keeps playing until someone doubts or win
        while not over:
            #Creates the list of player starting from the next player (the first round starts with Player 1, than 2, 3,...)
            if self.lastPlayer:
                currentPlayerIndex = self.players.index(self.lastPlayer) + 1
                orderPlayerList = [self.players[currentPlayerIndex+i] if i+currentPlayerIndex < len(self.players) else self.players[(currentPlayerIndex+i)%len(self.players)] for i in range(len(self.players))]
            else: #First round
                orderPlayerList = self.players

            #Performs each player's move
            for orderedIndex,player in enumerate(orderPlayerList):
                #Decide wether to gamble or to doubt
                cards, currentcard = player.doubtorgamble(currentcard, printstats)

                #If player doubted, check if the last player bluffed
                if len(cards) == 0: #doubted
                    player.doubts += 1

                    if lastHand == [currentcard]*len(lastHand): #Last player was telling the truth
                        player.add2hand(stack)
                        player.add2handvisible(lastHand, self.rounds, addall = False)
                        self.lastPlayer.removefromhandvisible(lastHand)
                        if printstats: self.printmovestats(player, [], currentcard, self.lastPlayer, self.lastPlayer)
                        self.lastPlayer.roundswin += 1
                        self.lastPlayer.react2event(Event.getEvent('RoundWon'))
                        player.react2event(Event.getEvent('RoundLost'))
                        
                        
                    else: #Last player was bluffing
                        player.rightdoubts += 1
                        self.lastPlayer.bluffslost += 1
                        self.lastPlayer.add2hand(stack)
                        self.lastPlayer.add2handvisible(lastHand, self.rounds, addall = False)
                        player.removefromhandvisible(lastHand)
                        self.lastPlayer.react2event(Event.getEvent('RoundLost'))
                        player.react2event(Event.getEvent('RoundWon'))
                        if printstats: self.printmovestats(player, [], currentcard, self.lastPlayer, player)
                        player.roundswin += 1
                    over = True
                    self.lastPlayer = player
                    break

                #If the player decided to gamble, add cards to stack and check if the other players want to doubt the move
                else: #played
                    #Just raises the confidence of the last player if he bluffed and no one noticed
                    if lastHand != [currentcard]*len(lastHand):
                        self.lastPlayer.react2event(Event.getEvent('BluffOK'))
                    if printstats: self.printmovestats(player, cards, currentcard, None)
                    lastHand = deepcopy(cards)
                    stack += lastHand
                    if lastHand != [currentcard]*len(lastHand):
                        player.bluffs += 1
                    #Get the list of players that is not the current player
                    doubting_player = [d_player for d_player in self.players if d_player != player]
                    #Get who is the next player
                    if orderedIndex+1 == len(orderPlayerList):
                        nextPlayer = orderPlayerList[0]
                    else:
                        nextPlayer = orderPlayerList[orderedIndex+1]
                    #Shuffle the list (so that not the same player doubts every time)
                    shuffle(doubting_player)
                    #Check if player from the list wants to doubt
                    for d_player in doubting_player:
                        #Get list of players that are NOT the current player and NOT the player evaluating the doubt
                        otherPlayers = [other for other in doubting_player if other != d_player]
                        doubt = False
                        doubt = d_player.evaluatedoubt(currentcard,  turn=1, lenHand=len(player.hand)) #If the player has no cards left, someone must doubt
                        if doubt:
                            d_player.doubts += 1
                            over = True
                            if lastHand == [currentcard]*len(lastHand):
                                if printstats: self.printmovestats(d_player, [], currentcard, player, player)
                                d_player.add2hand(stack)
                                d_player.add2handvisible(lastHand, self.rounds, addall = False)
                                player.removefromhandvisible(lastHand)
                                player.roundswin += 1
                                player.react2event(Event.getEvent('RoundWon'))
                                d_player.react2event(Event.getEvent('RoundLost'))
                            else:
                                if printstats: self.printmovestats(d_player, [], currentcard, player, d_player)
                                player.add2hand(stack)
                                player.add2handvisible(lastHand, self.rounds, addall = False)
                                player.bluffslost += 1
                                d_player.rightdoubts += 1
                                d_player.roundswin += 1
                                d_player.react2event(Event.getEvent('RoundWon'))
                                player.react2event(Event.getEvent('RoundLost'))
                            break #Someone already doubted, leave FOR

                self.lastPlayer = player
                if len(self.lastPlayer.hand)==0:
                    self.rounds += 1
                    return True #Gameover
                if over: #If someone doubted, the round is over
                    for player in orderPlayerList:
                        player.react2event(Event.getEvent('TimePass'))
                    break
        
        for player in orderPlayerList:
            player.react2event(Event.getEvent('TimePass'))
        self.rounds += 1
        return gameover

class Deck:

    def __init__(self, numberofdecks):
        """
        Parameters
        ----------
        numberofdecks : int
            Number of decks.

        Returns
        -------
        None.

        """
        #numbers = ['1','2','3','4','5','6','7','8','9','10','11','12','13']
        #D: Ouros, C: Paus, H: Copas, S: Espadas
        #suits = ['D', 'C', 'H', 'S']
        #cards = [n+suit for n in numbers for suit in suits]
        numbers = [1,2,3,4,5,6,7,8,9,10,11,12,13]
        cards = numbers*4
        self.cards = cards*numberofdecks
        self.numberofdecks = numberofdecks
        
    def printdeck(self):
        print(self.cards)

    def shuffledeck(self):
        """
        Returns
        -------
        shuffled : list
            Shuffled deck.

        """
        shuffled = deepcopy(self.cards)
        shuffle(shuffled)
        return shuffled


def showresults(players):
    roundswins = []
    doubts = []
    rightdoubts = []
    bluffs = []
    bluffslost = []

    for player in players:
        roundswins.append(player.roundswin)
        doubts.append(player.doubts)
        rightdoubts.append(player.rightdoubts)
        bluffs.append(player.bluffs)
        bluffslost.append(player.bluffslost)
        if player.won:
            print('%s won.' %(player.name))
    for player in players:
        print('%s: %s. doubt: %.1f. bluff: %.1f.'%(player.name, player.amountstrategy, player.willtodoubt, player.willtobluff))

    for i,k in zip(['Winnings','Doubts', 'Right doubts', 'Bluffs', 'Bluffs lost'], [roundswins,doubts,rightdoubts,bluffs,bluffslost]):
        print('%s:' %i)
        for j,player in enumerate(players):
            print('%s: %i' %(player.name, k[j]))


# prepare players for the next game
def prepareplayers(players):
    shuffle(players)
    for player in players:
        # reset player info from past game
        player.start()


def simulategames(games=100, printstats=False):
    deck = Deck(2)
    #deck.printdeck()
    players = [Player('Player' + str(i+1), personality = Personality(uniform(0, 1), uniform(0, 1), uniform(0, 1)), amountstrategy = strat, willtodoubt=doubt, willtobluff=bluff) for i,strat, doubt, bluff in zip(range(6),['random','random','cautious','cautious','aggressive','aggressive'], [0.3,0.3,0.3,0.3,0.3,0.3], [0.9,0.7,0.9,0.7,0.9,0.7])]



    game = Game(players, deck)
    for i in range(games):
        prepareplayers(players)
        game = Game(players, deck)
        game.playgame(printstats=printstats)

    fig, ax = plt.subplots(figsize=(8,8), dpi=150)

    #plt.scatter(np.arange(1,7), [player.won for player in players])
    plt.scatter([player.name for player in players], [player.won for player in players])
    plt.show()
    showresults(players)
    return players
    #showresults(players)

#Events definition (adding names to create the log)
Event('RoundWon','Won the round', valence = 0.2, arousal = 0.1)
Event('BluffCaught','Was caught bluffing', valence = -0.2, arousal = 0.1)
Event('CaughtSomeonesBluff','Caught someone bluffing', valence = 0.1, arousal = 0.1)
Event('RoundLost','Lost the round', valence = -0.1, arousal = -0.1)
Event('IClose2Win','Is close to win', valence = 0.1, arousal = 0.2)
Event('SomeoneClose2Win','Someone is close to win', valence = -0.1, arousal = 0.2)
Event('WonDoubt','Doubted someone and was right', valence = 0.1, arousal = 0.1) # ISSO EH A MESMA COISA QUE CaughtSomeonesBluff NEH?
Event('LostDoubt','Doubted someone and was wrong', valence = -0.1, arousal = -0.1) 
Event('BluffOK','Bluffed and no one noticed', valence = 0.05, arousal = 0)
Event('TimePass','Time passes', valence = 0, arousal = -0.05)
# e_WonRound = Event('Won the round', valence = 0.2, arousal = 0.1)
# e_WasCaughtBluffing = Event('Was caught bluffing', valence = -0.2, arousal = 0.1)
# e_CaughtSomeoneBluffing = Event('Caught someone bluffing', valence = 0.1, arousal = 0.1)
# e_LostRound = Event('Lost the round', valence = 1, arousal = 1)
# e_Close2Win = Event('Is close to win', valence = 1, arousal = 1)
# e_SomeoneClose2Win = Event('Someone is close to win', valence = 1, arousal = 1)
# e_RightDoubt = Event('Doubted someone and was right', valence = 1, arousal = 1)
# e_WrongDoubt = Event('Doubted someone and was wrong', valence = 1, arousal = 1)
# e_BluffUnnoticed = Event('Bluffed and no one noticed', valence = 1 , arousal = 1)


players = simulategames(100, False)
# deck = Deck(2)
# deck.printdeck()
# players = [Player('Player' + str(i+1), amountstrategy = j) for i,j in zip(range(6),['random','random','cautious','cautious','aggressive','aggressive'])]
# shuffle(players)
# print(players)
# game = Game(players, deck)
# game.playgame()
# showresults(players)