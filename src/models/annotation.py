from enum import Enum

class Annotation(Enum):
    """
    Represents an annotation type.
    """
    ECD = ("Topological domain", "green", "Extracellular")
    CHAIN = ("Chain", "cyan")
    TM = ("Transmembrane", "red")
    SIGNAL = ("Signal", "yellow")
    CYTO = ("Topological domain", "magenta", "Cytoplasmic")
    GLYCOSYLATION = ("Glycosylation", "orange")

    def __init__(self, feature, color, attr=None):
        self.feature = feature
        self.color = color
        self.attr = attr