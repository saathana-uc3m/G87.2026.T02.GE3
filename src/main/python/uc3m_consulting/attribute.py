import re
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException

class Attribute:
    """Base class for all validated project attributes."""
    def __init__(self):
        self._attr_value = ""
        self._error_message = ""
        self._validation_pattern = r""

    def _validate(self, value):
        """Standard regex validation logic."""
        my_regex = re.compile(self._validation_pattern)
        if not my_regex.fullmatch(value):
            raise EnterpriseManagementException(self._error_message)
        return value

    @property
    def value(self):
        return self._attr_value

    @value.setter
    def value(self, attr_value):
        self._attr_value = self._validate(attr_value)
