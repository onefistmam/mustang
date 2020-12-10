import multiprocessing as mp

def loopa():
    for i in [1,2,3,4,5,6]:
        print(i)

def process():
    process = mp.Process(loopa())
    return process

if __name__ == '__main__':
    processes = []

    p = process()
    processes.append(p)
    for pp in processes:
        pp.start()
        pp.join()
