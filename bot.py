import os

import discord
import requests

from io import BytesIO
from dotenv import load_dotenv
from PIL import Image
from random import shuffle, randint

from adventures import HeroCreator, Adventurer, Room


load_dotenv(override= True)
TOKEN = os.getenv('DISCORD_TOKEN')
CARDS = int(os.getenv('CARDS_ID'))
THEORIES = int(os.getenv('THEORIES_ID'))
GMNOTES = int(os.getenv("GMNOTES_ID"))
INGAME = int(os.getenv('INGAME_ID'))
ADVENTURE = int(os.getenv('ADVENTURE_ID'))
OWNER = int(os.getenv('OWNER_ID'))

HERO_LIMIT = 10


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



client = discord.Client(intents = discord.Intents.default())
game  =None

class Hooks:
    creation_hook = None
    adventure_hook = None

class Adv:
    creator = None
    num_test_msg = None
    hero_picker_msgs = {}
    hero_picker_stats = {}

@client.event
async def on_ready():
    print("Card-bot: Successfully logged in.",flush=True)
    adv_channel = client.get_channel(ADVENTURE)
    hooks = await adv_channel.webhooks()
    for hook in hooks:
        if hook.name == 'Adventure':
            Hooks.adventure_hook = hook
        if hook.name == 'Hero Creation':
            Hooks.creation_hook = hook


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
    if message.channel.id==ADVENTURE:
        if message.author.id == OWNER and message.content.lower().startswith('webhook test'):
            await Hooks.creation_hook.send('Test successful')
            await Hooks.adventure_hook.send('Test successful')
        if message.author.id == OWNER and message.content.lower().startswith('reaction test'):
            await message.add_reaction('0️⃣')
            msg = await Hooks.creation_hook.send('reaction number: - ', wait = True)
            print(f'===just sent===\n{msg}')
            Adv.num_test_msg = msg
            print(f'===before react===\n{Adv.num_test_msg}')
        if message.content.lower().startswith('создать героя'):
            already_owned = Adventurer.get(owner_id = message.author.id).count()
            if already_owned>=HERO_LIMIT:
                await Hooks.creation_hook.send(f'Лимит героев: {HERO_LIMIT}, Уже в наличии: {already_owned}')
            else:
                if Adv.creator is not None and not Adv.creator.done:
                    await Hooks.creation_hook.send(f'Кто-то (может даже ты) уже создаёт героя. Подожди своей очереди.')
                else:
                    Adv.creator = HeroCreator(message.author, Hooks.creation_hook)
                    await Adv.creator.start()
        elif message.content.lower().startswith('отмена'):
            if Adv.creator is not None and not Adv.creator.done and Adv.creator.user == message.author:
                Adv.creator = None
                await Hooks.creation_hook.send(f'Создание героя отменено.')
        elif Adv.creator is not None and not Adv.creator.done and Adv.creator.user.id == message.author.id:
            print(Adv.creator.stage)
            await Adv.creator.add_text(message.content)
        elif message.content.lower().startswith('список героев'):
            heroes = Adventurer.get()
            if heroes.count()==0:
                await Hooks.adventure_hook.send('Герои отсутствуют!')
            else:
                msg = ''
                for hero in heroes.all():
                    user = await client.fetch_user(hero.owner_id)
                    msg += f'{hero.name} ({user.display_name})\n'
                await Hooks.adventure_hook.send(msg)
        elif message.content.lower().startswith('герой:'):
            name = message.content[7:].strip()
            heroes = Adventurer.name_search(name)
            if heroes.count()==0:
                await Hooks.adventure_hook.send('Герой не найден!')
            elif heroes.count()==1:
                await Hooks.adventure_hook.send(f'{heroes.first().profile_russian()}')
            else:
                msg = 'Найдено несколько, уточните:\n'
                for hero in heroes.all():
                    user = await client.fetch_user(hero.owner_id)
                    msg += f'{hero.name} ({user.display_name})\n'
                await Hooks.adventure_hook.send(msg)
        elif (message.content.lower().startswith('проверка ') or
        message.content.lower().startswith('ролл ') or
        message.content.lower().startswith('roll ')):
            attr = message.content.lower().split()[1]
            russian_to_tech = {
                'мощь':'might',
                'сила':'strength',
                'выносливость':'endurance',
                'подвижность':'mobility',
                'ловкость':'dexterity',
                'скорость':'speed',
                'разум':'mind',
                'внимательность':'perception',
                'логика':'logic',
                'душа':'soul',
                'эмпатия':'empathy',
                'креативность':'creativity',
                'фэйт': 'fate',
                }
            tech = russian_to_tech[attr]
            if tech=='fate':
                rolls = []
                for i in range(4):
                    rolls.append(randint(1,6))
                s = 0
                for r in rolls:
                    if r>4:
                        s+=1
                    if r<3:
                        s-=1
                msg= f'Фэйт ролл {message.author.mention}: {s} {rolls}'
                await Hooks.adventure_hook.send(msg)
            else:
                heroes = Adventurer.get(owner_id = message.author.id)
                if heroes.count()==0:
                    await Hooks.adventure_hook.send('Герой не найден!')
                elif heroes.count()==1:
                    hero = heroes.first()
                    roll = hero.make_check(tech)
                    await Hooks.adventure_hook.send(f'{hero.name.capitalize()} ({attr.capitalize()}): {roll[0]} ({roll[1]})')
                else:
                    msg = "Несколько героев:\n"
                    i=0
                    for h in heroes:
                       msg+=f'{i} {h.name}'
                    _msg = await Hooks.creation_hook.send('reaction number: - ', wait = True)
                    Adv.hero_picker_msgs[_msg.id] = _msg
                    Adv.hero_picker_stats[_msg.id] = (tech,attr)
                    Adv.creator.add_numbers(_msg,0,heroes.count())

        if message.content.lower().startswith('комната'):
            if message.author.guild_permissions.manage_roles:
                room = Room.random()
                await Hooks.adventure_hook.send(room.public_message())
                await message.author.send(room.gm_message())
            else:
                await Hooks.adventure_hook.send('Недостаточно прав!')
    elif (message.content.lower().startswith('проверка фэйт') or
        message.content.lower().startswith('ролл фэйт')):
            rolls = []
            for i in range(4):
                rolls.append(randint(1,6))
            s = 0
            for r in rolls:
                if r>4:
                    s+=1
                if r<3:
                    s-=1
            msg= f'Фэйт ролл {message.author.mention}: {s} {rolls}'
            await Hooks.adventure_hook.send(msg)


@client.event
async def on_reaction_add(reaction, user):
    if Adv.num_test_msg is not None:
        if reaction.message.id == Adv.num_test_msg.id:
            await Adv.num_test_msg.edit(content = f'reaction number: {HeroCreator.em_to_num(reaction.emoji)}')
    if Adv.creator is not None:
        if Adv.creator.message is not None:
            if reaction.message.id == Adv.creator.message.id and user.id == Adv.creator.user.id:
                number  = HeroCreator.em_to_num(reaction.emoji)
                if number is not None:
                    await Adv.creator.add_number(number)
    if reaction.message.id in Adv.hero_picker_msgs:
        if user == Adv.hero_picker_msgs[reaction.message.id].author:
            number  = HeroCreator.em_to_num(reaction.emoji)
            if number is not None:
                heroes = Adventurer.get(owner_id = user.id)
                hero = heroes[number]
                stat = Adv.hero_picker_stats[reaction.message.id]
                roll = hero.make_check(stat[0])
                await Hooks.adventure_hook.send(f'{hero.name.capitalize()} ({stat[1].capitalize()}): {roll[0]} ({roll[1]})')
                Adv.hero_picker_msg.pop(reaction.message.id, None)
                Adv.hero_picker_stats.pop(reaction.message.id, None)








client.run(TOKEN)
