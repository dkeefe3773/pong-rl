# pong-rl
This is a python reinforcement learning project. The framework provides a server side pong game engine and client side player controllers.  There are three separate applications.
1. Server Game Engine
2. Player Left Client
3. Player Right Client

The server-client communication is through grpc.  The proto definitions for messages and services are within the *proto_idl* folder.
To generate the compiled proto code run the *scripts/proto_builder.sh* bash script.  This will generate artifacts within the *proto_gen* package.

## Setting up your environment
All conda / pip dependencies are contained within the *pong_rl_env.yaml* file.
To create your virtual conda environement for this project:

`> conda env create -f pong_rl_env.yaml`

`> conda activate pong_rl`

If you need to add dependencies to your environment be sure to export the dependencies and check them into the project.
`> conda env export > pong_rl_env.yaml`

To refresh your environment:

`> conda env update -f pong_rl_env.yaml`


## Running the system
To run the system, you must instantiate the game server and both player clients.  This is achieved by invoking the python applications for each.
1. To start the game server: python apps/game_master_start.py
2: To start player left: python apps/left_player_start.py
3: To start player right: python apps/right_player_start.py

**NOTE** You must start the server before the clients.  Otherwise, it doesn't matter the order of client start up.

The game server and player clients processes will stay alive until terminated.

## Injection Framework
This project uses [dependency-injector](https://pypi.org/project/dependency-injector/) for the inversion-of-control pattern. The behaviour of the the game engine and player clients is controlled via the configuration file *config/config.ini* and the 
injection providers within *injections/providers.py*  Please place all injection dependencies into this file.  

## Providing your own paddle controller
The *paddles* package contains paddle controller implementations.  Add your implmementations here. A paddle contoller processes a GameState object and produces a 
PaddleAction object.  The GameState is provided by the game engine via a continuous stream and the produced PaddleAction is provided 
back to the game engine also in a continous stream.

A PaddleController implementation does not know these details, but is simply provided a GameState and is expected to produce a PaddleAction.
When a new PaddleController is created, it should be added to the injection framework.  Here, you will see that PaddleControllers are 
injected into the right and left hand player objects.

