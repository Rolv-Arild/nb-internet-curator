from src.util import wayback
from src.action_server import start_server
from multiprocessing import Process

if __name__ == '__main__':
    wP = Process(target=wayback)
    sP = Process(target=start_server)

    wP.start()
    sP.start()

    wP.join()
    sP.join()
