from abc import ABC, abstractmethod

class AbstractLocation(ABC):
    @abstractmethod
    def render(self):
        pass