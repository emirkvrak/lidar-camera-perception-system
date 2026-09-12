from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.fsm.state_manager import StateManager

class BaseState:

    def __init__(self, manager: StateManager):
        self.manager = manager

    def on_enter(self):
        pass

    def update(self):
        pass

    def on_exit(self):
        pass