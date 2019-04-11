import os
import random

class RandomSeeder:
    seeded = False
    
    def Initialize():
        if not RandomSeeder.seeded:
            random.seed(os.urandom(256))
            RandomSeeder.seeded = True


RandomSeeder.Initialize()
