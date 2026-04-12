import re
from datetime import datetime, timezone
from freezegun import freeze_time
from uc3m_consulting.project_document import ProjectDocument
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException

class Validator:
    """Contains all validation rules for CIF and Dates."""

    @staticmethod
    def validate_cif(cif_code: str):
        if not isinstance(cif_code, str):
            raise EnterpriseManagementException("CIF code must be a string")

        cif_regex = re.compile(r"^[ABCDEFGHJKNPQRSUVW]\d{7}[0-9A-J]$")
        if not cif_regex.fullmatch(cif_code):
            raise EnterpriseManagementException("Invalid CIF format")

        # Calculate sums
        digits_body = cif_code[1:8]
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

        # Validate control char
        letter_prefix = cif_code[0]
        control_char = cif_code[8]
        control_letter_mapping = "JABCDEFGHI"

        if letter_prefix in ('A', 'B', 'E', 'H'):
            if str(control_digit) != control_char:
                raise EnterpriseManagementException("Invalid CIF character control number")
        elif letter_prefix in ('P', 'Q', 'S', 'K'):
            if control_letter_mapping[control_digit] != control_char:
                raise EnterpriseManagementException("Invalid CIF character control letter")
        else:
            raise EnterpriseManagementException("CIF type not supported")
        return True

    @staticmethod
    def check_date_format(date_str):
        date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        if not date_pattern.fullmatch(date_str):
            raise EnterpriseManagementException("Invalid date format")

    @staticmethod
    def validate_starting_date(date_str):
        Validator.check_date_format(date_str)
        try:
            my_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError as ex:
            raise EnterpriseManagementException("Invalid date format") from ex

        if my_date < datetime.now(timezone.utc).date():
            raise EnterpriseManagementException("Project's date must be today or later.")
        if not (2025 <= my_date.year <= 2050):
            raise EnterpriseManagementException("Invalid date format")
        return date_str

    @staticmethod
    def validate_document_integrity(document_data):
        """Checks if a single document's signature is valid."""
        timestamp = document_data["register_date"]
        doc_dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        with freeze_time(doc_dt_utc):
            p_doc = ProjectDocument(document_data["project_id"], document_data["file_name"])
            if p_doc.document_signature != document_data["document_signature"]:
                raise EnterpriseManagementException("Inconsistent document signature")
        return True


    @staticmethod
    def validate_registration_inputs(acronym, description, dept, budget):
        """Validates various input formats for project registration."""
        if not re.fullmatch(r"^[a-zA-Z0-9]{5,10}", acronym):
            raise EnterpriseManagementException("Invalid acronym")
        if not re.fullmatch(r"^.{10,30}$", description):
            raise EnterpriseManagementException("Invalid description format")
        if not re.fullmatch(r"(HR|FINANCE|LEGAL|LOGISTICS)", dept):
            raise EnterpriseManagementException("Invalid department")

        try:
            val = float(budget)
            if not (50000 <= val <= 1000000) or (len(str(val).split('.')[-1]) > 2 if '.' in str(val) else False):
                raise EnterpriseManagementException("Invalid budget amount")
        except ValueError as exc:
            raise EnterpriseManagementException("Invalid budget amount") from exc