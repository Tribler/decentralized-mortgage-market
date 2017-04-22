import protobuf_to_dict

from google.protobuf.descriptor import FieldDescriptor
from market.models.user import Role

protobuf_to_dict.TYPE_CALLABLE_MAP[FieldDescriptor.TYPE_BYTES] = str
protobuf_to_dict.REVERSE_TYPE_CALLABLE_MAP.pop(FieldDescriptor.TYPE_BYTES)


def accept(local=None, remote=None):
    def wrap(f):
        def invoke_func(*args, **kwargs):
            community = args[0]
            messages = args[1][:]

            if local in Role and community.my_role != local:
                for message in messages:
                    community.logger.warning('Dropping %s (receiver has incorrect role)', message.meta.name)
                while messages:
                    messages.pop()

            if remote in Role:
                num_messages = len(messages)
                for index, message in enumerate(reversed(messages)):
                    user = community.data_manager.get_user(message.candidate.get_member().public_key)
                    if user is not None and user.role != remote:
                        community.logger.warning('Dropping %s (sender has incorrect role)', message.meta.name)
                        messages.pop(num_messages - index)

            return f(community, messages, *args[2:], **kwargs)
        return invoke_func
    return wrap
