class LcdAnimation:
    """
    Classe base per gestire le animazioni sul display.
    Contiene una lista di frame (oggetti PIL Image).
    """
    def __init__(self):
        self.frames = []

    def get_frames(self):
        return self.frames