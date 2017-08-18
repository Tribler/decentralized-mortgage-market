import random


class ProfileUtil(object):

    @staticmethod
    def generate_profile_id():
        uuid = ProfileUtil.generate_random_uuid()
        return uuid

    @staticmethod
    def generate_random_uuid():
        return '%s-%s-%s-%s-%s' % (ProfileUtil.random_pid_part(8), ProfileUtil.random_pid_part(4),
                                   ProfileUtil.random_pid_part(4), ProfileUtil.random_pid_part(4),
                                   ProfileUtil.random_pid_part(12))

    @staticmethod
    def random_pid_part(length):
        return ''.join((random.choice('0123456789ABCDEF')
                        for i in range(length)))
