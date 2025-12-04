from enum import Enum

class Organism(Enum):
    """
    Represents an organism.
    """
    HUMAN = ('Homo sapiens', 9606)
    MOUSE = ('Mus musculus', 10090)
    ALPACA = ('Vicugna pacos', 30538)
    CYNO = ('Macaca fascicularis', 9541)
    CHICKEN = ('Gallus gallus', 9031)
    RABBIT = ('Oryctolagus cuniculus', 9986)
    LLAMA = ('Lama glama', 9844)
    
    @property
    def tax_id(self):
        return self.value[1]