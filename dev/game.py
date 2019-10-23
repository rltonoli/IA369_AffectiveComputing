# -*- coding: utf-8 -*-
"""
Created on Oct 2019

@authors: Giancarlo Schaffer Torres Junior; Liz Mercedes Falcón Rivadulla; Rodolfo Luis Tonoli
"""
import numpy as np
from random import shuffle, choice
from copy import deepcopy


class Player:

    def __init__(self, name):
        self.name = name
        self.hand = []

    def pickcard(self):
        #Pick a card of the hand
        return choice(self.hand)

    def chooseamount(self, card, strategy='aggresive'):
        #Choose the amount of cards to play
        if strategy=='aggressive':
            return self.hand.count(card)
        elif strategy=='cautious':
            return 1
        elif strategy=='random':
            return choice(np.arange(self.hand.count(card)))+1

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
                if not currentcard in self.hand:
                    doubt = choice([0,0,0,0,0,1,1,1,1,1])
                    if doubt==0:
                        return False
                    else:
                        return True
        else: #some other player's turn
            if lenHand == 0: #if the player don't have cards left, doubt it
                return True
            else:
                doubt = choice([0,0,0,0,0,0,0,0,0,1])
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


    def totalcards(self):
        return len(self.hand)

    def printhand(self):
        print(self.hand)



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


    def playgame(self, maxrounds=1000):
        gameover = False
        while self.rounds < maxrounds and not gameover:
            print(' ')
            print('Round number %i:' %(self.rounds+1))

            gameover = self.playround()

            print('-------------------------------')
            self.printhands()
            print('End of round number %i' %(self.rounds))
            if gameover:
                print('%s won.' %self.lastPlayer.name)
            print('-------------------------------')

            # soma = 0
            # for player in self.players:
            #     soma += len(player.hand)
            # print('TOTAL CARDS IN HANDS = %i'%soma)

    def printhands(self):
        for player in self.players:
            print('%s hand:'%(player.name))
            player.printhand()

    def printmovestats(self, player1, cards, currentcard, player2=None, doubtwinner=None):
        if not player2:
            print('%s played cards %s. Current card: %i' %(player1.name, cards, currentcard))
        else:
            print('%s doubted %s' %(player1.name, player2.name))
            if doubtwinner==player1:
                print('%s bluffed, %s was right' %(player2.name, player1.name))
            else:
                print('%s was telling the truth, %s was wrong' %(player2.name, player1.name))


    def playround(self):
        over = False #flag for round over (someone doubted)
        gameover = False #flag for game over (someone won)
        if self.rounds == 0:
            # Give cards
            cards = deck.shuffledeck()
            while len(cards) > 0:
                for player in self.players:
                    if len(cards) > 0:
                        player.hand.append(cards.pop())
            self.printhands()

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
                #Prints the player's decision

                #If player doubted, check if the last player bluffed
                if len(cards) == 0: #doubted

                    if lastHand == [currentcard]*len(lastHand):
                        player.hand += stack
                        self.printmovestats(player, [], currentcard, self.lastPlayer, self.lastPlayer)
                    else:
                        self.lastPlayer.hand += stack

                        self.printmovestats(player, [], currentcard, self.lastPlayer, player)
                    over = True
                    self.lastPlayer = player
                    break

                #If the player decided to gamble, add cards to stack and check if the other players want to doubt the move
                else: #played
                    self.printmovestats(player, cards, currentcard, None)
                    lastHand = deepcopy(cards)
                    stack += lastHand
                    #Get the list of players that is not the current player
                    doubting_player = [d_player for d_player in players if d_player != player]
                    #Shuffle the list (so that not the same player doubts every time)
                    shuffle(doubting_player)
                    #Check if player from the list wants to doubt
                    for d_player in doubting_player:
                        doubt = d_player.evaluatedoubt(currentcard,  turn=1, lenHand=len(player.hand)) #If the player has no cards left, someone must doubt
                        if doubt:
                            over = True
                            if lastHand == [currentcard]*len(lastHand):
                                self.printmovestats(d_player, [], currentcard, player, player)
                                d_player.hand += stack
                            else:
                                #doubting_player.hand += stack
                                self.printmovestats(d_player, [], currentcard, player, d_player)
                                player.hand += stack
                            break

                self.lastPlayer = player
                if len(self.lastPlayer.hand)==0:
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


deck = Deck(1)
deck.printdeck()
players = [Player('Player' + str(i+1)) for i in range(4)]
print(players)
game = Game(players, deck)
game.playgame()
