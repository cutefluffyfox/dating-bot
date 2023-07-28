import logging
import contextlib

import sqlalchemy
from modules.database import SqlAlchemyBase
from modules.database import create_session


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    user_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, nullable=False)
    message_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.TEXT, nullable=True)
    pronouns = sqlalchemy.Column(sqlalchemy.TEXT, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.TEXT, nullable=True)
    file_id = sqlalchemy.Column(sqlalchemy.TEXT, nullable=True)
    bot_metadata = sqlalchemy.Column(sqlalchemy.TEXT, nullable=True)

    def set(self, message_id: int = None, name: str = None, pronouns: str = None,
            description: str = None, file_id: str = None, bot_metadata: str = None):
        """
        Change basic info. If parameter is None, it won't be changed
        :param message_id:    message id of current working page
        :param name:          name/username that is preferable by user
        :param pronouns:      pronouns preferable by user
        :param description:   description of a user (how they describe themselves)
        :param file_id:       in-telegram id of a file
        :param bot_metadata:  any data that requires cache for a small amount of time
        """
        with contextlib.closing(create_session()) as session:
            logging.info(f'Update info for {self} ')
            user = session.query(User).filter(User.user_id == self.user_id).first()

            if message_id is not None:
                self.message_id = user.message_id = message_id
            if name is not None:
                self.name = user.name = name
            if pronouns is not None:
                self.pronouns = user.pronouns = pronouns
            if description is not None:
                self.description = user.description = description
            if file_id is not None:
                self.file_id = user.file_id = file_id
            if bot_metadata is not None:
                self.bot_metadata = user.bot_metadata = bot_metadata

            session.commit()

    def all_filled(self) -> bool:
        """
        Check if user is already registered in the bot
        :return: True when user is registered (all data filled), False in any other case
        """
        return (self.name is not None) and (self.pronouns is not None) and (self.description is not None) and (self.file_id is not None)

    @staticmethod
    def exists(user_id: int) -> bool:
        with contextlib.closing(create_session()) as session:
            return session.query(User).filter(User.user_id == user_id).first() is not None

    @staticmethod
    def add(user_id: int):
        """
        Add user to database
        :param user_id:      in-telegram id of a user
        """
        with contextlib.closing(create_session()) as session:
            logging.info(f'Add User(id={user_id}) to database')
            session.add(User(user_id=user_id))
            session.commit()

    @staticmethod
    def get(user_id: int):
        """
        Gets User from database by user_id
        :param user_id: integer that represents user telegram id
        :return User(**kwargs) by user_id or None if id is invalid
        """
        with contextlib.closing(create_session()) as session:
            return session.query(User).filter(User.user_id == user_id).first()

    def delete(self):
        """Delete user from database"""
        with contextlib.closing(create_session()) as session:
            session.delete(session.query(User).filter(User.user_id == self.user_id).first())
            session.commit()

    def __repr__(self) -> str:
        """
        Basic representation of a class
        :return: User(**kwargs)
        """
        return f'User(id={self.user_id}, name="{self.name}", pronouns="{self.pronouns}", ' \
               f'file_id="{self.file_id}", bot_metadata="{self.bot_metadata}", message_id={self.message_id})'
