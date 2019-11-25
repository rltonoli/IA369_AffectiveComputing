# -*- coding: utf-8 -*-
"""
Created on Oct 2019

@authors: Giancarlo Schaffer Torres Junior; Liz Mercedes Falcón Rivadulla; Rodolfo Luis Tonoli
"""
import numpy as np
from random import shuffle, choice, uniform
from copy import deepcopy
import matplotlib.pyplot as plt

#colors for make styled prints
class Color:
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    purple = '\033[35m'
    cyan = '\033[36m'
    grey = '\033[37m'
    clear = '\033[m'

class Random:
    def get(value):
        """
        Chance. Value = 0.8 = 80% chance
        """
        if value < 0 or value > 1:
            raise Exception
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

    def showtraits(self):
        return ('memory: %f, haste: %f, self-control: %f' %(self.memory, self.haste, self.selfcontrol))



class Emotion:
    def __init__(self, valence, arousal):
        self.valence = valence
        self.arousal = arousal

    def update(self, selfcontrol, event):
        self.valence = clamp(self.valence + event.valence, -1, 1)
        self.arousal = clamp(self.arousal + event.arousal * (1 - selfcontrol), -1, 1)


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

    def reset(self):
        self.won = 0
        self.gamewin = 0
        self.roundswin = 0
        self.doubts = 0
        self.rightdoubts = 0
        self.bluffs = 0
        self.bluffslost = 0

    def pickcard(self):
        #Pick a card of the hand
        return choice(self.hand)

    def chooseamount(self, card, strategy='aggresive'):
        #Choose the amount of cards to play
        if self.amountstrategy=='aggressive':
            return self.hand.count(card)
        elif self.amountstrategy=='cautious':
            return 1
        elif self.amountstrategy=='random':
            return choice(np.arange(self.hand.count(card)))+1
        else:
            raise Exception

    def gamble(self, currentcard):
        #Pick a card (if it is the first npc to play)
        #and choose the amount of cards
        if not currentcard: #pick a card
            currentcard = self.pickcard()

        if not currentcard in self.hand: #bluff
            bluffcard = self.hand.pop(choice(np.arange(len(self.hand)))) #pick one randomly
            cardstostack = [bluffcard]
        else:

            #choose amount
            amount = self.chooseamount(currentcard, choice(['aggressive','cautious','random']))
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
            print('%s traits -> %s' % (self.name, self.personality.showtraits()))
            if lenHand == 0: #if the player don't have cards left, doubt it
                return True
            else:
                doubt = Random.get(self.willtodoubt)
                if doubt==0:
                    return False
                else:
                    return True

    def doubtorgamble(self, currentcard):
        #Decide wether to doubt or play
        if self.evaluatedoubt(currentcard,turn=0):
            return [],currentcard #doubt
        else:
            return self.gamble(currentcard) #gamble

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

        self.lastPlayer = None


    def playgame(self, maxrounds=2, printstats=True):
        gameover = False
        while self.rounds < maxrounds and not gameover:
            if printstats:
                print(' ')
                print('%sRound number %i:%s' %(Color.purple, self.rounds+1, Color.clear))
    
                gameover = self.playround(printstats)
    
                print('-=-'*20)
                self.printhands()
                print('%sEnd of round number %i%s' %(Color.purple, self.rounds, Color.clear))
                if gameover:
                    self.lastPlayer.won += 1
                    print('%s won.' %self.lastPlayer.name)
                print('-=-'*20)
            else:
                gameover = self.playround(printstats)
                if gameover:
                    self.lastPlayer.won += 1

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
            for player in orderPlayerList:
                #Decide wether to gamble or to doubt
                cards, currentcard = player.doubtorgamble(currentcard)

                #If player doubted, check if the last player bluffed
                if len(cards) == 0: #doubted
                    player.doubts += 1

                    if lastHand == [currentcard]*len(lastHand):
                        player.add2hand(stack)
                        player.add2handvisible(lastHand, self.rounds, addall = False)
                        self.lastPlayer.removefromhandvisible(lastHand)
                        if printstats: self.printmovestats(player, [], currentcard, self.lastPlayer, self.lastPlayer)
                        self.lastPlayer.roundswin += 1
                    else:
                        player.rightdoubts += 1
                        self.lastPlayer.bluffslost += 1
                        self.lastPlayer.add2hand(stack)
                        self.lastPlayer.add2handvisible(lastHand, self.rounds, addall = False)
                        player.removefromhandvisible(lastHand)
                        if printstats: self.printmovestats(player, [], currentcard, self.lastPlayer, player)
                        player.roundswin += 1
                    over = True
                    self.lastPlayer = player
                    break

                #If the player decided to gamble, add cards to stack and check if the other players want to doubt the move
                else: #played
                    if printstats: self.printmovestats(player, cards, currentcard, None)
                    lastHand = deepcopy(cards)
                    stack += lastHand
                    if lastHand != [currentcard]*len(lastHand):
                        player.bluffs += 1
                    #Get the list of players that is not the current player
                    doubting_player = [d_player for d_player in self.players if d_player != player]
                    #Shuffle the list (so that not the same player doubts every time)
                    shuffle(doubting_player)
                    #Check if player from the list wants to doubt
                    for d_player in doubting_player:
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
                            else:
                                if printstats: self.printmovestats(d_player, [], currentcard, player, d_player)
                                player.add2hand(stack)
                                player.add2handvisible(lastHand, self.rounds, addall = False)
                                player.bluffslost += 1
                                d_player.rightdoubts += 1
                                d_player.roundswin += 1
                            break

                self.lastPlayer = player
                if len(self.lastPlayer.hand)==0:
                    self.rounds += 1
                    return True #Gameover
                if over: #If someone doubted, the round is over
                    break
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


def simulategames(games=100, printstats=False):
    deck = Deck(2)
    #deck.printdeck()
    players = [Player('Player' + str(i+1), personality = Personality(uniform(0, 1), uniform(0, 1), uniform(0, 1)), amountstrategy = strat, willtodoubt=doubt, willtobluff=bluff) for i,strat, doubt, bluff in zip(range(6),['random','random','cautious','cautious','aggressive','aggressive'], [0.3,0.3,0.3,0.3,0.3,0.3], [0.9,0.7,0.9,0.7,0.9,0.7])]

    game = Game(players, deck)
    for i in range(games):
        shuffle(players)
        game = Game(players, deck)
        game.playgame(printstats=printstats)

    fig, ax = plt.subplots(figsize=(8,8), dpi=150)

    #plt.scatter(np.arange(1,7), [player.won for player in players])
    # plt.scatter([player.name for player in players], [player.won for player in players])
    # plt.show()
    showresults(players)
    return players
    #showresults(players)
    
players = simulategames(1, True)

print()
# deck = Deck(2)
# deck.printdeck()
# players = [Player('Player' + str(i+1), amountstrategy = j) for i,j in zip(range(6),['random','random','cautious','cautious','aggressive','aggressive'])]
# shuffle(players)
# print(players)
# game = Game(players, deck)
# game.playgame()
# showresults(players)