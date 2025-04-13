from typing import Any

class Greeter:
    """A tool that creates greetings"""
    
    def __init__(self):
        self.name = "Greeter"
        self.description = "Creates greetings"
    
    def run(self, name: str, time_of_day: str) -> str:
        if time_of_day.lower() == "morning":
            return f"Good morning, {name}!"
        elif time_of_day.lower() == "afternoon":
            return f"Good afternoon, {name}!"
        elif time_of_day.lower() == "evening":
            return f"Good evening, {name}!"
        else:
            return f"Hello, {name}!"