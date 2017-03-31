from storm.properties import SimpleProperty
from storm.variables import Variable


class EnumVariable(Variable):

    def __init__(self, *args, **kwargs):
        self._enum = kwargs.pop('enum')
        super(EnumVariable, self).__init__(*args, **kwargs)


    def parse_set(self, value, from_db):
        if from_db:
            return value
        if value in self._enum:
            return value.value
        raise ValueError("Invalid enum value: %s" % repr(value))

    def parse_get(self, value, to_db):
        if to_db:
            return value
        try:
            return self._enum(value)
        except ValueError:
            raise ValueError("Invalid enum value: %s" % repr(value))


class Enum(SimpleProperty):
    variable_class = EnumVariable

    def __init__(self, enum=None, **kwargs):
        SimpleProperty.__init__(self, enum=enum, **kwargs)
