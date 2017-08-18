class RequiredInput(object):
    """
    This class represents required input that is needed from i.e. the user.
    """

    def __init__(self, name, required_fields, additional_data={}, error_text=None):
        """
        :param name: the reference name of the input.
        :type name: str
        :param required_fields: a list of required fields. Each entry in this list is a tuple with two items, namely
        the name of the input item and a human-readable string that asks for this input.
        :type required_fields: [RequiredField]
        """
        self.name = name
        self.required_fields = required_fields
        self.additional_data = additional_data
        self.error_text = error_text

    def get_index_of_field_name(self, field_name):
        cur_ind = 0
        for required_field in self.required_fields:
            if required_field.name == field_name:
                return cur_ind
            cur_ind += 1
        return -1

    def is_last_name(self, name):
        return self.required_fields[-1].name == name

    def to_dictionary(self):
        return_dict = {
            'name': self.name,
            'required_fields': [required_field.to_dictionary() for required_field in self.required_fields],
            'additional_data': self.additional_data,
        }

        if self.error_text:
            return_dict['error_text'] = self.error_text

        return return_dict
