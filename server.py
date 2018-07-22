import logging
import socket

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


class Server(object):
    """
    An adventure game socket server
    
    An instance's methods share the following variables:
    
    * self.socket: a "bound" server socket, as produced by socket.bind()
    * self.client_connection: a "connection" socket as produced by socket.accept()
    * self.input_buffer: a string that has been read from the connected client and
      has yet to be acted upon.
    * self.output_buffer: a string that should be sent to the connected client; for
      testing purposes this string should NOT end in a newline character. When
      writing to the output_buffer, DON'T concatenate: just overwrite.
    * self.done: A boolean, False until the client is ready to disconnect
    * self.room: one of 0, 1, 2, 3. This signifies which "room" the client is in,
      according to the following map:
      
                                     3                      N
                                     |                      ^
                                 1 - 0 - 2                  |
                                 
    When a client connects, they are greeted with a welcome message. And then they can
    move through the connected rooms. For example, on connection:
    
    OK! Welcome to Realms of Venture! This room has brown wall paper!  (S)
    move north                                                         (C)
    OK! This room has white wallpaper.                                 (S)
    say Hello? Is anyone here?                                         (C)
    OK! You say, "Hello? Is anyone here?"                              (S)
    move south                                                         (C)
    OK! This room has brown wall paper!                                (S)
    move west                                                          (C)
    OK! This room has a green floor!                                   (S)
    quit                                                               (C)
    OK! Goodbye!                                                       (S)
    
    Note that we've annotated server and client messages with *(S)* and *(C)*, but
    these won't actually appear in server/client communication. Also, you'll be
    free to develop any room descriptions you like: the only requirement is that
    each room have a unique description.
    """

    game_name = 'Land of the Lost'

    def __init__(self, port=50000):
        self.input_buffer = ""
        self.output_buffer = ""
        self.done = False
        self.socket = None
        self.client_connection = None
        self.port = port

        self.room = 0

    def connect(self):
        logging.info('connecting to socket')
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP)

        address = ('127.0.0.1', self.port)
        logging.info(f'binding socket to "{address}"')
        self.socket.bind(address)
        logging.info('listening on socket')
        self.socket.listen(1)

        self.client_connection, address = self.socket.accept()

    def room_description(self, room_number):
        logging.info('generating room description')
        return [
            'You are in the white room with black curtains, a sword glistens in the corner...',
            'You are in the jungle room with many strange animal busts in here, they almost seem to be real?',
            'You are in the rancor pit, watch out!',
            'You are in the dungeon, a dimly lit torch can be seen down the hall...'
        ][room_number]

    def greet(self):
        logging.info('greeting client')
        self.output_buffer = f'Welcome to {self.game_name}! {self.room_description(self.room)}'

    def get_input(self):
        logging.info('getting client input')
        received = b''
        while b'\n' not in received:
            received += self.client_connection.recv(16)

        self.input_buffer = received.decode().strip()

    def move(self, argument):
        if self.room == 0 and argument == 'north':
            self.room = 3

        if self.room == 0 and argument == 'east':
            self.room = 2

        if self.room == 0 and argument == 'west':
            self.room = 1

        if self.room == 1 and argument == 'east':
            self.room = 0

        if self.room == 2 and argument == 'west':
            self.room = 0

        if self.room == 3 and argument == 'south':
            self.room = 0
        logging.info(f'moving the client to room "{self.room}"')
        self.output_buffer = self.room_description(self.room)

    def say(self, argument):
        logging.info(f'client says {argument}')
        self.output_buffer = f'You say, "{argument}"'

    def quit(self, argument):
        logging.info('client is quitting')
        self.done = True
        self.output_buffer = 'Goodbye Adventurer!'

    def route(self):
        received = self.input_buffer.split(' ')
        logging.info(f'received: "{received}"')
        command = received.pop(0)
        logging.info(f'command: {command}')
        arguments = ''.join(received)
        logging.info(f'arguments: {arguments}')
        {
            'quit': self.quit,
            'move': self.move,
            'say': self.say,
        }[command](arguments)

    def push_output(self):
        logging.info(self.output_buffer.encode())
        self.client_connection.sendall(b'OK! ' + self.output_buffer.encode() + b'\n')

    def serve(self):
        logging.info('starting main program')
        self.connect()
        self.greet()
        self.push_output()

        while not self.done:
            self.get_input()
            self.route()
            self.push_output()

        logging.info('closing connections and exiting')
        self.client_connection.close()
        self.socket.close()
