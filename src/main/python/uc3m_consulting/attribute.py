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

class CifAttribute(Attribute):
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^[ABCDEFGHJKNPQRSUVW]\d{7}[0-9A-J]$"
        self._error_message = "Invalid CIF format"
        self.value = value

class AcronymAttribute(Attribute):
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^[a-zA-Z0-9]{5,10}"
        self._error_message = "Invalid acronym"
        self.value = value

class DescriptionAttribute(Attribute):
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^.{10,30}$"
        self._error_message = "Invalid description format"
        self.value = value

class DepartmentAttribute(Attribute):
    def __init__(self, value):
        super().__init__()
        # Validates that the department is one of the four allowed strings
        self._validation_pattern = r"^(HR|FINANCE|LEGAL|LOGISTICS)$"
        self._error_message = "Invalid department"
        self.value = value

class DateAttribute(Attribute):
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$"
        self._error_message = "Invalid date format"
        self.value = value

class BudgetAttribute(Attribute):
    """Class for Budget validation and float conversion"""
    def __init__(self, value):
        super().__init__()
        # We don't use a regex here because we need numerical comparison
        self.value = value

    def _validate(self, value):
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise EnterpriseManagementException("Invalid budget amount")

        # Check decimals
        if '.' in str(value) and len(str(value).split('.')[-1]) > 2:
            raise EnterpriseManagementException("Invalid budget amount")

        # Check range
        if not (50000 <= val <= 1000000):
            raise EnterpriseManagementException("Invalid budget amount")

        return value