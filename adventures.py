import os

from random import randint

from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

USER = os.getenv('DB_USER')
PASS = os.getenv('DB_PASS')
HOST = os.getenv('DB_HOST')
NAME = os.getenv('DB_NAME')



Base = declarative_base()


class Adventurer(Base):
    __tablename__ = 'adventurers'

    id = Column(Integer, Sequence('adv_id_seq'), primary_key=True)
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
            f'**{self.name}**\n'
            f'Жизнь: {self.life} Удача: {self.luck} Богатство: {self.wealth}\n'
            f'============ОПИСАНИЕ=============\n'
            f'{self.decription}\n'
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
            )




engine = create_engine(f'mysql://{USER}:{PASS}@{HOST}/{NAME}')
session = sessionmaker(bind=engine)


class Room:
    pass


class AdventureManager:
    def __init__(self, channel):
        self.channel = channel
        self.heroes = []





