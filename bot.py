import os

import discord
import requests

from io import BytesIO
from dotenv import load_dotenv
from PIL import Image
from random import shuffle




load_dotenv(override= True)
TOKEN = os.getenv('DISCORD_TOKEN')
CARDS = int(os.getenv('CARDS_ID'))
THEORIES = int(os.getenv('THEORIES_ID'))
GMNOTES = int(os.getenv("GMNOTES_ID"))
INGAME = int(os.getenv('INGAME_ID'))






class Game:
    def __init__(self,initiator,channel):
        self.initiator = initiator
        self.players = [initiator,]
        self.hands= []
        symbols = ['heart','pitchfork','hammer','jester','saw','bag']
        elements =  ['aether','earth','fire','water','wind']
        self.deck = [s+'-'+e for s in symbols for e in elements]
        self.turn = -1
        self.started = False
        self.finished = False
        self.channel = channel
        self.scores=[]
    async def join(self,player):
        if not self.started:
            if not player in self.players:
                self.players.append(player)
                await self.channel.send("Успешно!")

    async def start(self):
        self.started = True
        self.finished = False
        shuffle(self.deck)
        shuffle(self.players)
        self.hands = [Hand(p) for p in self.players]
        self.scores = [0 for p in self.players]
        await self.nextturn(0)
    async def cancel(self):
        self.finished = True
        await self.channel.send("Игра отменена")
    async def nextturn(self,iters):
        if iters==len(self.players):
            result = [player.mention+': {0}'.format(score) for player,score
                      in zip(self.players,self.scores)]
            text = 'Игра окончена!\n'+'\n'.join(result)
            self.finished = True
            await self.channel.send(text)
            return
        iters+=1
        self.turn+=1
        if self.turn>=len(self.players):
            self.turn = 0
        empty = False
        if len(self.deck)==0 and len(self.hands[self.turn].cards)==0:
            self.scores[self.turn]=self.hands[self.turn].countpoints()
            empty = True
        if self.scores[self.turn]==0 and not empty:
            await self.channel.send('Ход '+self.players[self.turn].mention)
        else:
            await self.nextturn(iters)
    async def playcard(self,player,idx):
        if player!=self.players[self.turn]:
            return
        hand = self.hands[self.turn]
        if len(hand.showing)==5:
            await self.channel.send(player.mention+' Уже 5 карт!')
            points = hand.countpoints()
            hand.genimg(False)
            file = discord.File('temp.png','hand.png')
            await self.channel.send('Points: {0}'.format(points),file = file)
            await self.nextturn(0)
            return
        if idx>=len(hand.cards):
            return
        hand.play(idx)
        points = hand.countpoints()
        hand.genimg(False)
        file = discord.File('temp.png','hand.png')
        await self.channel.send('Points: {0}'.format(points),file = file)
        await hand.remind()
        if len(hand.showing)==5:
            self.scores[self.turn]=points

        await self.nextturn(0)
    async def drawcard(self,player):
        print('Draw started...',flush=True)
        if player!=self.players[self.turn]:
            print('Wrong player',flush=True)
            return
        if len(self.deck)==0:
            print('Empty deck',flush=True)
            await self.channel.send("Колода пуста!")
            return
        hand = self.hands[self.turn]
        if len(hand.cards)>4:
            print('Hand is full',flush=True)
            await self.channel.send('Максимум карт в руке!')
            return
        await hand.addcard(self.deck.pop())
        await self.channel.send("Карт осталось: {0}".format(len(self.deck)))
        await self.nextturn(0)



class Hand:
    def __init__(self,player):
        self.cards = []
        self.showing = []
        self.player=player
    async def addcard(self, card):
        self.cards.append(card)
        print('Card added.',flush=True)
        await self.remind()
    async def remind(self):
        print('Reminding...',flush=True)
        if self.genimg(True):
            file = discord.File('temp.png','hand.png')
            await self.player.send('Ваша рука',file=file)
            return
        await self.player.send('Ваша рука пуста')
    def play(self,index):
        self.showing.append(self.cards.pop(index))
    def genimg(self, secret):
        try:
            lst = self.showing
            if secret == True:
                lst = self.cards
            if len(lst)==0:
                return False
            img = Image.new("RGBA",(38*len(lst),48),(255,255,255,0))
            x=2
            for card in lst:
                cim = Image.open(card+'.png')
                img.paste(cim,(x,0))
                x+=38
            img = img.resize((img.size[0]*2,img.size[1]*2),resample=Image.NEAREST)
            img.save('temp.png','PNG')
        except Exception as e:
            print("Image generation failed",flush = True)
            print(e,flush=True)
        return True
    def countpoints(self):
        counts = {'heart':0,'pitchfork':0,'hammer':0,'jester':0,'saw':0,'bag':0,
                  'aether':0,'earth':0,'fire':0,'water':0,'wind':0}
        for card in self.showing:
            symbol,element = card.split('-')
            counts[symbol]+=1
            counts[element]+=1
        s = 0
        for val in counts.values():
            s+=val**2
        return s


class NotFound(Exception):
    pass



client = discord.Client()
game  =None
@client.event
async def on_ready():
    print("Card-bot: Successfully logged in.",flush=True)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    print(message.author,':',message.content,flush=True)
    global game
    if message.content.lower().startswith('теория:'):
        await client.get_channel(THEORIES).send('Теория '+message.author.mention+': '+message.content[7:])
    if message.channel.id==CARDS:
        if message.content.lower().startswith('новая игра'):
            if game is None or game.finished==True:
                game=Game(message.author,message.channel)
                await message.channel.send('Игра создана')
        elif message.content.lower().startswith('присоединяюсь'):
            if game is not None and game.started==False:
                await game.join(message.author)
        elif message.content.lower().startswith('начинаем'):
            if (game is not None and
            game.started==False and
            game.initiator==message.author):
                await game.start()
        elif message.content.lower().startswith('отбой'):
            if (game is not None and
            game.started==False and
            game.initiator==message.author):
                await game.cancel()
        elif message.content.lower().startswith('тяну'):
            if (game is not None
            and game.started==True
            and game.finished==False):
                await game.drawcard(message.author)
        elif message.content.lower().startswith('играю'):
            if (game is not None
            and game.started==True
            and game.finished==False):
                splitted = message.content.split(' ')
                try:
                    index = int(splitted[1])-1
                    await game.playcard(message.author,index)
                except IndexError or ValueError as ex:
                    print(ex)
                    await message.channel.send(message.author.mention+
                                               ', нужно выбрать карту!'+
                                               ' 1 — самая левая')
    if message.channel.id==GMNOTES:
        pass




client.run(TOKEN)
