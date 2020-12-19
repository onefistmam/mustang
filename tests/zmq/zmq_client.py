from time import sleep

import zmq

PORT = 9124


def main():
    """Main.
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    print('Connect port %s' % PORT)
    socket.connect("tcp://localhost:%s" % PORT)
    socket.setsockopt(zmq.SUBSCRIBE, ''.encode('utf-8'))
    while True:
        response = socket.recv().decode('utf-8');
        print("response: %s" % response)


if __name__ == '__main__':
    main()
