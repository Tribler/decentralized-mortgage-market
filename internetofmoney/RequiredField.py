class RequiredField(object):
    """
    This class represents a required field and is part of a required input.
    """

    def __init__(self, name, type='text', text='Please enter your input', placeholder=''):
        """
        :param name: The name of the field, used when parsing the entered input.
        :param text: A human-readable string describing what is being expected in this field.
        :param type: The type of the input, either text or password.
        :param placeholder: An optional placeholder for the input field.
        """
        self.name = name
        self.type = type
        self.text = text
        self.placeholder = placeholder

    def to_dictionary(self):
        return {
            'name': self.name,
            'type': self.type,
            'text': self.text,
            'placeholder': self.placeholder
        }
