import os

from random import randint, choice

from sqlalchemy import create_engine, Column, Integer, String, Sequence, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv

load_dotenv()

USER = os.getenv('DB_USER')
PASS = os.getenv('DB_PASS')
HOST = os.getenv('DB_HOST')
NAME = os.getenv('DB_NAME')

engine = create_engine(f'mysql://{USER}:{PASS}@{HOST}/{NAME}?charset=utf8', encoding='utf8')
#engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)


Base = declarative_base()


class Adventurer(Base):
    __tablename__ = 'adventurers'
    session = Session()
    id = Column(Integer, Sequence('adv_id_seq'), primary_key=True)
    owner_id = Column(BigInteger)
    name = Column(String(50))
    description = Column(String(500))
    #Stats
    might = Column(Integer)
    #might substats
    strength = Column(Integer)
    endurance = Column(Integer)
    #-----------
    mobility = Column(Integer)
    #mobility substats
    dexterity = Column(Integer)
    speed = Column(Integer)
    #------------
    mind = Column(Integer)
    #substats
    perception = Column(Integer)
    logic = Column(Integer)
    #--------------------
    soul = Column(Integer)
    #substats
    empathy = Column(Integer)
    creativity = Column(Integer)
    #--------------------
    #Variables
    life = Column(Integer)
    luck = Column(Integer)
    wealth = Column(Integer)
    exp = Column(Integer)
    #--------------
    def get_stat(self, stat):
        stats = {
            'might'     : self.might,
            'strength'  : self.strength + self.might,
            'endurance' : self.endurance + self.might,
            'mobility'  : self.mobility,
            'dexterity' : self.dexterity + self.mobility,
            'speed'     : self.speed + self.mobility,
            'mind'      : self.mind,
            'perception': self.perception + self.mind,
            'logic'     : self.logic + self.mind,
            'soul'      : self.soul,
            'empathy'   : self.empathy + self.soul,
            'creativity': self.creativity + self.soul
            }
        return stats[stat]

    def make_check(self, stat):
        iterations  = self.get_stat(stat)
        rolls = []
        for i in range(iterations):
            rolls.append(randint(1,6))
        return (sum(rolls),tuple(rolls))

    def profile_russian(self):
        return (
            f'```'
            f'Имя: {self.name}\n'
            f'Жизнь: {self.life} Удача: {self.luck} Богатство: {self.wealth} Опыт: {self.exp}\n'
            f'============ОПИСАНИЕ=============\n'
            f'{self.description}\n'
            f'=========ХАРАКТЕРИСТИКИ==========\n'
            f'Мощь: {self.might}\n'
            f'  Сила: {self.strength}\n'
            f'  Выносливость: {self.endurance}\n'
            f'Подвижность: {self.mobility}\n'
            f'  Ловкость: {self.dexterity}\n'
            f'  Скорость: {self.speed}\n'
            f'Разум: {self.mind}\n'
            f'  Логика: {self.logic}\n'
            f'  Внимательность: {self.perception}\n'
            f'Душа: {self.mobility}\n'
            f'  Эмпатия: {self.empathy}\n'
            f'  Креативность: {self.creativity}'
            f'```'
            )

    @classmethod
    def get(cls, **kwargs):

        query = cls.session.query(cls)
        for key in kwargs:
            query = query.filter(cls.__dict__[key]==kwargs[key])
        return query

    @classmethod
    def name_exists(cls, name):
        query = cls.session.query(cls)
        query = query.filter(cls.name.ilike(name))
        cnt = query.count()
        return cnt>0

    @classmethod
    def name_search(cls, name):
        query = cls.session.query(cls)
        query = query.filter(cls.name.ilike(f'%{name}%'))
        return query

    @classmethod
    def refresh_session(cls):
        cls.session.close()





class Room:
    seeds = []
    with open('seeds.csv') as f:
        seeds = f.readlines()
    active_check_stats = ['Сила','Выносливость','Ловкость','Скорость','Логика','Креативность']
    secret_reveal_stats = ['Внимательность', 'Эмпатия']
    @classmethod
    def random_challenge(cls):
        dc = randint(7,14)
        stat = choice(cls.active_check_stats)
        seed = choice(cls.seeds)
        return f'{stat} {dc} {seed}'
    @classmethod
    def random_secret(cls):
        dc = randint(7,14)
        stat = choice(cls.secret_reveal_stats)
        seed = choice(cls.seeds)
        return f'{stat} {dc} {seed}'
    @classmethod
    def random(cls):
        r = Room()
        r.seeds = [choice(cls.seeds), choice(cls.seeds), choice(cls.seeds)]
        r.challenges = [Room.random_challenge(), Room.random_challenge()]
        r.secrets = []
        for i in range(randint(0,2)):
            r.secrets.append(cls.random_secret())
        return r
    def public_message(self):
        return (
            f'{"".join(self.seeds)}'
            'Проверки:\n'
            f'{"".join(self.challenges)}'
            )
    def gm_message(self):
        return (
            f'{"".join(self.seeds)}'
            'Проверки:\n'
            f'{"".join(self.challenges)}'
            'Секреты:\n'
            f'{"".join(self.secrets)}'
            )


class HeroCreator:

    number_to_emoji = {
        0:'0️⃣',
        1:'1️⃣',
        2:'2️⃣',
        3:'3️⃣',
        4:'4️⃣',
        5:'5️⃣',
        6:'6️⃣',
        7:'7️⃣',
        8:'8️⃣',
        9:'9️⃣'
    }

    emoji_to_number = {
        '0️⃣':0,
        '1️⃣':1,
        '2️⃣':2,
        '3️⃣':3 ,
        '4️⃣':4 ,
        '5️⃣':5 ,
        '6️⃣':6 ,
        '7️⃣':7 ,
        '8️⃣':8,
        '9️⃣':9
    }
    @classmethod
    def em_to_num(cls, em):
        return cls.emoji_to_number.get(em, None)

    def __init__(self, user, hook):
        self.user = user
        self.hook = hook
        self.done = False
    async def start(self):
        self.hero = Adventurer(
            life = 5,luck = 5,exp = 0, wealth = 0,
            owner_id = self.user.id,
            strength = 0,
            endurance = 0,
            dexterity = 0,
            speed = 0,
            perception = 0,
            logic = 0,
            empathy = 0,
            creativity = 0
            )
        self.stage = 'name'
        self.statpoints = 10
        self.specpoints = 3
        await self.hook.send('Как зовут персонажа?')
        self.message = None
    async def add_numbers(self,message, start, stop):
        for i in range(start,stop):
            await message.add_reaction(HeroCreator.number_to_emoji[i])

    async def add_text(self, text):
        print("function fired")
        if self.stage == 'name':
            print("Name stage recognized")
            if not Adventurer.name_exists(text):
                self.hero.name = text
                self.stage = 'desc'
                await self.hook.send('Короткое описание персонажа:')
            else:
                await self.hook.send('Имя занято!')
        elif self.stage == 'desc':
            print("Description stage recognized")
            self.hero.description = text
            self.stage = 'stats-might'
            await self.send_stat_message('Мощь',1,8)
        else:
            pass
    async def add_number(self, number):
        if self.stage == 'stats-might':
            if number>0 and number<8:
                self.statpoints -= number
                self.hero.might = number
                await self.send_stat_message('Подвижность',1,self.statpoints-1)
                self.stage = 'stats-mob'
        elif self.stage == 'stats-mob':
            if number>0 and number<self.statpoints-1:
                self.statpoints -= number
                self.hero.mobility = number
                await self.send_stat_message('Разум',1,self.statpoints)
                self.stage = 'stats-mind'
                print(self.stage)
        elif self.stage == 'stats-mind':
            if number>0 and number<self.statpoints:
                self.statpoints -= number
                self.hero.mind = number
                self.hero.soul = self.statpoints
                self.statpoints = 0
                msg = (
                    f'Мощь: {self.hero.might}\n'
                    f'Подвижность: {self.hero.mobility}\n'
                    f'Разум: {self.hero.mind}\n'
                    f'Душа: {self.hero.soul}\n'
                    )
                await self.hook.send(msg)
                await self.hook.send('==Специализации==')
                await self.send_stat_message('Сила',0,self.specpoints+1, True)
                self.stage = 'specs-str'
        elif self.stage == 'specs-str':
            if number >= 0 and number <= self.specpoints:
                self.hero.strength = number
                self.specpoints -= number
                if self.specpoints<1:
                    self.done = True
                    await self.finish()
                else:
                    await self.send_stat_message('Выносливость',0,self.specpoints+1, True)
                    self.stage = 'specs-end'
        elif self.stage == 'specs-end':
            if number>=0 and number<=self.specpoints:
                self.hero.endurance = number
                self.specpoints -= number
                if self.specpoints<1:
                    self.done = True
                    await self.finish()
                else:
                    await self.send_stat_message('Ловкость',0,self.specpoints+1, True)
                    self.stage = 'specs-dex'
        elif self.stage == 'specs-dex':
            if number>=0 and number<=self.specpoints:
                self.hero.dexterity = number
                self.specpoints -= number
                if self.specpoints<1:
                    self.done = True
                    await self.finish()
                else:
                    await self.send_stat_message('Скорость',0,self.specpoints+1, True)
                    self.stage = 'specs-spd'
        elif self.stage == 'specs-spd':
            if number>=0 and number<=self.specpoints:
                self.hero.speed = number
                self.specpoints -= number
                if self.specpoints<1:
                    self.done = True
                    await self.finish()
                else:
                    await self.send_stat_message('Логика',0,self.specpoints+1, True)
                    self.stage = 'specs-log'
        elif self.stage == 'specs-log':
            if number>=0 and number<=self.specpoints:
                self.hero.logic = number
                self.specpoints -= number
                if self.specpoints<1:
                    self.done = True
                    await self.finish()
                else:
                    await self.send_stat_message('Внимательность',0,self.specpoints+1, True)
                    self.stage = 'specs-prc'
        elif self.stage == 'specs-prc':
            if number>=0 and number<=self.specpoints:
                self.hero.perception = number
                self.specpoints -= number
                if self.specpoints<1:
                    self.done = True
                    await self.finish()
                else:
                    await self.send_stat_message('Эмпатия',0,self.specpoints+1, True)
                    self.stage = 'specs-emp'
        elif self.stage == 'specs-emp':
            if number>=0 and number<=self.specpoints:
                self.hero.empathy = number
                self.specpoints -= number
                if self.specpoints<1:
                    self.done = True
                    await self.finish()
                else:
                    await self.send_stat_message('Креативность',0,self.specpoints+1, True)
                    self.stage = 'specs-crt'
        elif self.stage == 'specs-crt':
            if number>=0 and number<=self.specpoints:
                self.hero.endurance = number
                self.specpoints -= number
                if self.specpoints<1:
                    self.done = True
                    await self.finish()
                else:
                    await self.send_stat_message('Креативность',0,self.specpoints+1, True)
                    self.stage = 'specs-crt'

    async def send_stat_message(self,stat, start, stop, spec = False):
        msg = (
            f'Осталось очков: {self.specpoints if spec else self.statpoints}\n'
            f'{stat}'
            )
        self.message = await self.hook.send(msg, wait = True)
        await self.add_numbers(self.message, start, stop)

    async def finish(self):
        s = Adventurer.session
        s.add(self.hero)
        s.commit()
        s.close()
        self.message  = None
        await self.hook.send('Готово!')



class AdventureManager:
    def __init__(self, channel):
        self.channel = channel
        self.heroes = dict()





