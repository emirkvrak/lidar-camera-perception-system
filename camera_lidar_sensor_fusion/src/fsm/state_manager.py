

import time
from src.app.app_context import AppContext
from src.fsm.state import BaseState


class StateManager:

    def __init__(self):
        self.current_state = None
        self.running = True
        self.ctx = AppContext()

    def change_state(self, new_state:BaseState):
        if self.current_state:
            self.current_state.on_exit()
        
        self.current_state = new_state
        self.current_state.on_enter()

    def update(self):
        if self.current_state:
            self.current_state.update()

    def run(self):
        while self.running:
            self.update()
            time.sleep(0.01)


    def stop(self):
        self.running = False