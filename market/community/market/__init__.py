import hashlib

from market.models.user import Role


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
                for message in reversed(messages):
                    user_public_key = message.candidate.get_member().public_key
                    user_id = community.public_key_to_id(user_public_key)
                    user = community.data_manager.get_user(user_id)
                    if user is not None and user.role != remote:
                        community.logger.warning('Dropping %s (sender has incorrect role)', message.meta.name)
                        messages.remove(message)
                    elif remote == Role.FINANCIAL_INSTITUTION and community.get_stake(user_public_key) < 1:
                        community.logger.warning('Dropping %s (sender has <1 stake)', message.meta.name)
                        messages.remove(message)

            return f(community, messages, *args[2:], **kwargs)
        return invoke_func
    return wrap
