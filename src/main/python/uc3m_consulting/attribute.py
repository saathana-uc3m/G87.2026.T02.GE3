"""Module for attribute validation classes using inheritance"""
import re
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException

# pylint: disable=too-few-public-methods
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
        """Getter for the attribute value"""
        return self._attr_value

    @value.setter
    def value(self, attr_value):
        """Setter that triggers validation"""
        self._attr_value = self._validate(attr_value)

class CifAttribute(Attribute):
    """Class for CIF validation"""
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^[ABCDEFGHJKNPQRSUVW]\d{7}[0-9A-J]$"
        self._error_message = "Invalid CIF format"
        self.value = value

class AcronymAttribute(Attribute):
    """Class for Acronym validation"""
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^[a-zA-Z0-9]{5,10}"
        self._error_message = "Invalid acronym"
        self.value = value

class DescriptionAttribute(Attribute):
    """Class for Description validation"""
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^.{10,30}$"
        self._error_message = "Invalid description format"
        self.value = value

class DepartmentAttribute(Attribute):
    """Class for Department validation"""
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^(HR|FINANCE|LEGAL|LOGISTICS)$"
        self._error_message = "Invalid department"
        self.value = value

class DateAttribute(Attribute):
    """Class for Date validation"""
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$"
        self._error_message = "Invalid date format"
        self.value = value

class BudgetAttribute(Attribute):
    """Class for Budget validation and float conversion"""
    def __init__(self, value):
        super().__init__()
        self.value = value

    def _validate(self, value):
        """Specific validation for numerical budget values"""
        try:
            val = float(value)
        except (ValueError, TypeError) as exc:
            raise EnterpriseManagementException("Invalid budget amount") from exc

        # Check decimals using rsplit as recommended by Pylint
        if '.' in str(value) and len(str(value).rsplit('.', maxsplit=1)[-1]) > 2:
            raise EnterpriseManagementException("Invalid budget amount")

        # Check range (removed unnecessary parentheses)
        if not 50000 <= val <= 1000000:
            raise EnterpriseManagementException("Invalid budget amount")

        return value
