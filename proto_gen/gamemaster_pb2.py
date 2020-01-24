# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: gamemaster.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='gamemaster.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x10gamemaster.proto\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1fgoogle/protobuf/timestamp.proto\"g\n\x10PlayerIdentifier\x12\x13\n\x0bplayer_name\x18\x01 \x01(\t\x12\x1c\n\x14paddle_strategy_name\x18\x02 \x01(\t\x12 \n\x0bpaddle_type\x18\x03 \x01(\x0e\x32\x0b.PaddleType\"\x1d\n\x05\x43oord\x12\t\n\x01x\x18\x01 \x01(\x05\x12\t\n\x01y\x18\x02 \x01(\x05\"?\n\x05\x41\x63tor\x12\x1e\n\nactor_type\x18\x01 \x01(\x0e\x32\n.ActorType\x12\x16\n\x06\x63oords\x18\x02 \x03(\x0b\x32\x06.Coord\"?\n\nImageFrame\x12\r\n\x05image\x18\x01 \x01(\x0c\x12\x10\n\x08num_rows\x18\x02 \x01(\r\x12\x10\n\x08num_cols\x18\x03 \x01(\r\"}\n\tScoreCard\x12!\n\x06player\x18\x01 \x01(\x0b\x32\x11.PlayerIdentifier\x12\x1b\n\x13\x63urrent_game_points\x18\x02 \x01(\r\x12\x1a\n\x12total_match_points\x18\x03 \x01(\r\x12\x14\n\x0ctotal_points\x18\x04 \x01(\r\"\xa7\x01\n\tGameState\x12\x17\n\x0fstate_iteration\x18\x02 \x01(\x04\x12\x16\n\x06\x61\x63tors\x18\x03 \x03(\x0b\x32\x06.Actor\x12 \n\x0b\x61rena_frame\x18\x04 \x01(\x0b\x32\x0b.ImageFrame\x12\"\n\x0eleft_scorecard\x18\x05 \x01(\x0b\x32\n.ScoreCard\x12#\n\x0fright_scorecard\x18\x06 \x01(\x0b\x32\n.ScoreCard\"h\n\x0cPaddleAction\x12,\n\x11player_identifier\x18\x01 \x01(\x0b\x32\x11.PlayerIdentifier\x12*\n\x10paddle_directive\x18\x02 \x01(\x0e\x32\x10.PaddleDirective*.\n\nPaddleType\x12\x0b\n\x07NOT_SET\x10\x00\x12\x08\n\x04LEFT\x10\x01\x12\t\n\x05RIGHT\x10\x02*W\n\tActorType\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x0f\n\x0bLEFT_PADDLE\x10\x01\x12\x10\n\x0cRIGHT_PADDLE\x10\x02\x12\x10\n\x0cPRIMARY_BALL\x10\x03\x12\x08\n\x04WALL\x10\x04*3\n\x0fPaddleDirective\x12\x06\n\x02UP\x10\x00\x12\x08\n\x04\x44OWN\x10\x01\x12\x0e\n\nSTATIONARY\x10\x02\x32\xc8\x01\n\nGameMaster\x12\x36\n\x11stream_game_state\x12\x11.PlayerIdentifier\x1a\n.GameState\"\x00\x30\x01\x12>\n\x0fregister_player\x12\x11.PlayerIdentifier\x1a\x16.google.protobuf.Empty\"\x00\x12\x42\n\x15submit_paddle_actions\x12\r.PaddleAction\x1a\x16.google.protobuf.Empty\"\x00(\x01\x62\x06proto3')
  ,
  dependencies=[google_dot_protobuf_dot_empty__pb2.DESCRIPTOR,google_dot_protobuf_dot_timestamp__pb2.DESCRIPTOR,])

_PADDLETYPE = _descriptor.EnumDescriptor(
  name='PaddleType',
  full_name='PaddleType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='NOT_SET', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='LEFT', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='RIGHT', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=751,
  serialized_end=797,
)
_sym_db.RegisterEnumDescriptor(_PADDLETYPE)

PaddleType = enum_type_wrapper.EnumTypeWrapper(_PADDLETYPE)
_ACTORTYPE = _descriptor.EnumDescriptor(
  name='ActorType',
  full_name='ActorType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='UNKNOWN', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='LEFT_PADDLE', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='RIGHT_PADDLE', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PRIMARY_BALL', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='WALL', index=4, number=4,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=799,
  serialized_end=886,
)
_sym_db.RegisterEnumDescriptor(_ACTORTYPE)

ActorType = enum_type_wrapper.EnumTypeWrapper(_ACTORTYPE)
_PADDLEDIRECTIVE = _descriptor.EnumDescriptor(
  name='PaddleDirective',
  full_name='PaddleDirective',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='UP', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DOWN', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='STATIONARY', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=888,
  serialized_end=939,
)
_sym_db.RegisterEnumDescriptor(_PADDLEDIRECTIVE)

PaddleDirective = enum_type_wrapper.EnumTypeWrapper(_PADDLEDIRECTIVE)
NOT_SET = 0
LEFT = 1
RIGHT = 2
UNKNOWN = 0
LEFT_PADDLE = 1
RIGHT_PADDLE = 2
PRIMARY_BALL = 3
WALL = 4
UP = 0
DOWN = 1
STATIONARY = 2



_PLAYERIDENTIFIER = _descriptor.Descriptor(
  name='PlayerIdentifier',
  full_name='PlayerIdentifier',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='player_name', full_name='PlayerIdentifier.player_name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='paddle_strategy_name', full_name='PlayerIdentifier.paddle_strategy_name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='paddle_type', full_name='PlayerIdentifier.paddle_type', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=82,
  serialized_end=185,
)


_COORD = _descriptor.Descriptor(
  name='Coord',
  full_name='Coord',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='Coord.x', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y', full_name='Coord.y', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=187,
  serialized_end=216,
)


_ACTOR = _descriptor.Descriptor(
  name='Actor',
  full_name='Actor',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='actor_type', full_name='Actor.actor_type', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='coords', full_name='Actor.coords', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=218,
  serialized_end=281,
)


_IMAGEFRAME = _descriptor.Descriptor(
  name='ImageFrame',
  full_name='ImageFrame',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='image', full_name='ImageFrame.image', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='num_rows', full_name='ImageFrame.num_rows', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='num_cols', full_name='ImageFrame.num_cols', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=283,
  serialized_end=346,
)


_SCORECARD = _descriptor.Descriptor(
  name='ScoreCard',
  full_name='ScoreCard',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='player', full_name='ScoreCard.player', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='current_game_points', full_name='ScoreCard.current_game_points', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='total_match_points', full_name='ScoreCard.total_match_points', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='total_points', full_name='ScoreCard.total_points', index=3,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=348,
  serialized_end=473,
)


_GAMESTATE = _descriptor.Descriptor(
  name='GameState',
  full_name='GameState',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='state_iteration', full_name='GameState.state_iteration', index=0,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='actors', full_name='GameState.actors', index=1,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='arena_frame', full_name='GameState.arena_frame', index=2,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='left_scorecard', full_name='GameState.left_scorecard', index=3,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='right_scorecard', full_name='GameState.right_scorecard', index=4,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=476,
  serialized_end=643,
)


_PADDLEACTION = _descriptor.Descriptor(
  name='PaddleAction',
  full_name='PaddleAction',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='player_identifier', full_name='PaddleAction.player_identifier', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='paddle_directive', full_name='PaddleAction.paddle_directive', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=645,
  serialized_end=749,
)

_PLAYERIDENTIFIER.fields_by_name['paddle_type'].enum_type = _PADDLETYPE
_ACTOR.fields_by_name['actor_type'].enum_type = _ACTORTYPE
_ACTOR.fields_by_name['coords'].message_type = _COORD
_SCORECARD.fields_by_name['player'].message_type = _PLAYERIDENTIFIER
_GAMESTATE.fields_by_name['actors'].message_type = _ACTOR
_GAMESTATE.fields_by_name['arena_frame'].message_type = _IMAGEFRAME
_GAMESTATE.fields_by_name['left_scorecard'].message_type = _SCORECARD
_GAMESTATE.fields_by_name['right_scorecard'].message_type = _SCORECARD
_PADDLEACTION.fields_by_name['player_identifier'].message_type = _PLAYERIDENTIFIER
_PADDLEACTION.fields_by_name['paddle_directive'].enum_type = _PADDLEDIRECTIVE
DESCRIPTOR.message_types_by_name['PlayerIdentifier'] = _PLAYERIDENTIFIER
DESCRIPTOR.message_types_by_name['Coord'] = _COORD
DESCRIPTOR.message_types_by_name['Actor'] = _ACTOR
DESCRIPTOR.message_types_by_name['ImageFrame'] = _IMAGEFRAME
DESCRIPTOR.message_types_by_name['ScoreCard'] = _SCORECARD
DESCRIPTOR.message_types_by_name['GameState'] = _GAMESTATE
DESCRIPTOR.message_types_by_name['PaddleAction'] = _PADDLEACTION
DESCRIPTOR.enum_types_by_name['PaddleType'] = _PADDLETYPE
DESCRIPTOR.enum_types_by_name['ActorType'] = _ACTORTYPE
DESCRIPTOR.enum_types_by_name['PaddleDirective'] = _PADDLEDIRECTIVE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PlayerIdentifier = _reflection.GeneratedProtocolMessageType('PlayerIdentifier', (_message.Message,), dict(
  DESCRIPTOR = _PLAYERIDENTIFIER,
  __module__ = 'gamemaster_pb2'
  # @@protoc_insertion_point(class_scope:PlayerIdentifier)
  ))
_sym_db.RegisterMessage(PlayerIdentifier)

Coord = _reflection.GeneratedProtocolMessageType('Coord', (_message.Message,), dict(
  DESCRIPTOR = _COORD,
  __module__ = 'gamemaster_pb2'
  # @@protoc_insertion_point(class_scope:Coord)
  ))
_sym_db.RegisterMessage(Coord)

Actor = _reflection.GeneratedProtocolMessageType('Actor', (_message.Message,), dict(
  DESCRIPTOR = _ACTOR,
  __module__ = 'gamemaster_pb2'
  # @@protoc_insertion_point(class_scope:Actor)
  ))
_sym_db.RegisterMessage(Actor)

ImageFrame = _reflection.GeneratedProtocolMessageType('ImageFrame', (_message.Message,), dict(
  DESCRIPTOR = _IMAGEFRAME,
  __module__ = 'gamemaster_pb2'
  # @@protoc_insertion_point(class_scope:ImageFrame)
  ))
_sym_db.RegisterMessage(ImageFrame)

ScoreCard = _reflection.GeneratedProtocolMessageType('ScoreCard', (_message.Message,), dict(
  DESCRIPTOR = _SCORECARD,
  __module__ = 'gamemaster_pb2'
  # @@protoc_insertion_point(class_scope:ScoreCard)
  ))
_sym_db.RegisterMessage(ScoreCard)

GameState = _reflection.GeneratedProtocolMessageType('GameState', (_message.Message,), dict(
  DESCRIPTOR = _GAMESTATE,
  __module__ = 'gamemaster_pb2'
  # @@protoc_insertion_point(class_scope:GameState)
  ))
_sym_db.RegisterMessage(GameState)

PaddleAction = _reflection.GeneratedProtocolMessageType('PaddleAction', (_message.Message,), dict(
  DESCRIPTOR = _PADDLEACTION,
  __module__ = 'gamemaster_pb2'
  # @@protoc_insertion_point(class_scope:PaddleAction)
  ))
_sym_db.RegisterMessage(PaddleAction)



_GAMEMASTER = _descriptor.ServiceDescriptor(
  name='GameMaster',
  full_name='GameMaster',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=942,
  serialized_end=1142,
  methods=[
  _descriptor.MethodDescriptor(
    name='stream_game_state',
    full_name='GameMaster.stream_game_state',
    index=0,
    containing_service=None,
    input_type=_PLAYERIDENTIFIER,
    output_type=_GAMESTATE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='register_player',
    full_name='GameMaster.register_player',
    index=1,
    containing_service=None,
    input_type=_PLAYERIDENTIFIER,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='submit_paddle_actions',
    full_name='GameMaster.submit_paddle_actions',
    index=2,
    containing_service=None,
    input_type=_PADDLEACTION,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_GAMEMASTER)

DESCRIPTOR.services_by_name['GameMaster'] = _GAMEMASTER

# @@protoc_insertion_point(module_scope)
