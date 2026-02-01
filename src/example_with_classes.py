import atrace


class Animal:
    def __init__(self, name):
        self.name = name


class Cat(Animal):
    pass


ivy = Cat("Ivy Megaman")
print(ivy)
