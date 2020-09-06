from collections import deque
from numpy.random import choice


class Memory:
    def __init__(self, max: int = 1):
        self._storage = deque(maxlen=max)

    def sample(self, sample_size: int = 1):
        indx = choice(len(self._storage), size=sample_size)
        return [self._storage[i] for i in indx]

    def add_memory(self, memory):
        self._storage.append(memory)

    def __len__(self):
        return len(self._storage)


if __name__ == '__main__':
    mem = Memory(5)
    mem.add_memory(('a', 'b'))
    mem.add_memory(('c', 'd'))
    mem.add_memory(('e', 'f'))
    mem.add_memory(('g', 'h'))
    mem.add_memory(('i', 'j'))
    mem.add_memory(('k', 'l'))
    print(mem.sample(3))
