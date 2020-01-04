import time
from concurrent import futures

import grpc

from proto_gen import gamemaster_pb2_grpc
from proto_gen.gamemaster_pb2_grpc import GameMasterServicer
from utils import measures
from utils.measures import ureg


class PongServer:
    """
    Sets up and starts the grpc server
    """

    def __init__(self, servicer: GameMasterServicer, max_workers: int, thread_prefix: str, port: str):
        """
        :param servicer:      An implementation of GameMasterServicer that provides the API behaviour
        :param max_workers:   Each rpc request is handled by a server thread.  This specifies the size of that
                              thread pool.  Once a thread pool is exhausted, calls to the server will be blocked
                              until a thread becomes available
        :param thread_prefix: For logging, the name of the server thread
        :param port:          The listen port for client connections
        """

        # the grpc.so_reuseport option makes it so multiple servers, if instantiated on the same host, can
        # all use the same listen port -- somehow.  Apparently, this is a feature not a bug.
        #  However, this feature isn't compatible with the python grpc package available
        # from the anaconda repository.  You will notice an error when the server is started about SO_RESUSEPORT unavailable.
        # This is because the c-binary provided with the anaconda python grpc was compiled with this option not supported.
        # (You could re-compile from source , but meh)
        # So .. lets formally set the option to zero here so that the server itself knows to throw an error if
        # it detects it is sharing a listen port with another server, just as a safety safeguard
        server_options = [('grpc.so_reuseport', 0), ]
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers,
                                                             thread_name_prefix=thread_prefix),
                                  handlers=None,
                                  interceptors=None,
                                  options=server_options,
                                  maximum_concurrent_rpcs=None)

        # add our handler for the service apis
        gamemaster_pb2_grpc.add_GameMasterServicer_to_server(servicer, self.server)

        # specify the listen port.  insecure means no authentication is done
        self.server.add_insecure_port("{}:{}".format('localhost', port))

    def start_server_blocking(self):
        self.server.start()

        # this is needed because gameserver.start() doesn't block
        seconds_per_day = measures.seconds_per_min.to(ureg.sec / ureg.day)
        try:
            while True:
                time.sleep(seconds_per_day.magnitude)
        except KeyboardInterrupt:
            self.server.stop(0)
