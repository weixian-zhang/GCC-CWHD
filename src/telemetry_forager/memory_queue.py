from collections import deque

class MemoryQueue(object):
    _instances = {}
    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            class_._instances[class_] = super(MemoryQueue, class_).__new__(class_, *args, **kwargs)
        return class_._instances[class_]
  
    def __init__(self):
        self.q = deque([])

    def __len__(self):
        return len(self.q)

    def enqueue(self, message: str ):
        if len(self.q) > 0:
            return False, 'queue has task already'
        self.q.appendleft(message)
        return True, ''

    def dequeue(self) -> str:
        if len(self.q) == 0:
            return None
        return self.q.pop()
