
from typing import Set


class Squares:
    __squares: Set[str] = set()
    
    SQUARE_ADMINS = [
        'thelatesupremeleadersnoop',
        'aves0115'
    ]
    
    @classmethod
    def add_square(cls, author:str, name: str):
        # if author in cls.SQUARE_ADMINS:
        cls.__squares.add(name)
    
    @classmethod
    def is_square(cls, name:str):
        return name in cls.__squares
    
    @classmethod
    def remove_square(cls, author:str, name: str):
        # if author in cls.SQUARE_ADMINS
        if name in cls.__squares:
            cls.__squares.remove(name)
    
    @classmethod
    def list_squares(cls):
        messages = [f'{name} rn: 🟨👉👈' for name in cls.__squares]
        if not messages:
            return "Square free since '63 💪🏿"
        return '\n'.join(messages)
