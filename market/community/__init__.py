import protobuf_to_dict

from google.protobuf.descriptor import FieldDescriptor

protobuf_to_dict.TYPE_CALLABLE_MAP[FieldDescriptor.TYPE_BYTES] = str
protobuf_to_dict.REVERSE_TYPE_CALLABLE_MAP.pop(FieldDescriptor.TYPE_BYTES)
