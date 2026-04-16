"""Module for attribute validation classes using inheritance"""
import re
from datetime import datetime, timezone
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
    """Class for CIF validation including regex and checksum"""
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^[ABCDEFGHJKNPQRSUVW]\d{7}[0-9A-J]$"
        self._error_message = "Invalid CIF format"
        self.value = value

    def _validate(self, value):
        """Performs regex validation followed by the CIF checksum"""
        super()._validate(value)

        digits_body = value[1:8]
        even_sum = 0
        odd_sum = 0
        for i, digit_str in enumerate(digits_body):
            current_digit = int(digit_str)
            if i % 2 == 0:
                multiplied = current_digit * 2
                even_sum += (multiplied // 10) + (multiplied % 10) if multiplied > 9 else multiplied
            else:
                odd_sum += current_digit

        total_sum = even_sum + odd_sum
        control_digit = (10 - (total_sum % 10)) % 10
        letter_prefix = value[0]
        control_char = value[8]
        control_letter_mapping = "JABCDEFGHI"

        if letter_prefix in ('A', 'B', 'E', 'H'):
            if str(control_digit) != control_char:
                raise EnterpriseManagementException("Invalid CIF character control number")
        elif letter_prefix in ('P', 'Q', 'S', 'K'):
            if control_letter_mapping[control_digit] != control_char:
                raise EnterpriseManagementException("Invalid CIF character control letter")
        else:
            raise EnterpriseManagementException("CIF type not supported")
        return value

class DateAttribute(Attribute):
    """Class for Date validation including format, year range, and past-date check"""
    def __init__(self, value):
        super().__init__()
        self._validation_pattern = r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$"
        self._error_message = "Invalid date format"
        self.value = value

    def _validate(self, value):
        """Performs regex validation followed by date range/past logic"""
        super()._validate(value)
        try:
            my_date = datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError as ex:
            raise EnterpriseManagementException("Invalid date format") from ex

        # Order of logic to satisfy specific test case error messages
        if not 2025 <= my_date.year <= 2050:
            raise EnterpriseManagementException("Invalid date format")
        if my_date < datetime.now(timezone.utc).date():
            raise EnterpriseManagementException("Project's date must be today or later.")
        return value

class BudgetAttribute(Attribute):
    """Class for Budget validation and float conversion"""
    def __init__(self, value):
        super().__init__()
        self.value = value

    def _validate(self, value):
        """Validates numerical range and decimal precision"""
        try:
            val = float(value)
        except (ValueError, TypeError) as exc:
            raise EnterpriseManagementException("Invalid budget amount") from exc

        if '.' in str(value) and len(str(value).rsplit('.', maxsplit=1)[-1]) > 2:
            raise EnterpriseManagementException("Invalid budget amount")
        if not 50000 <= val <= 1000000:
            raise EnterpriseManagementException("Invalid budget amount")
        return value

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
