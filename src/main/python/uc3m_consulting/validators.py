"""Module containing the Validator class for complex business rules"""
from datetime import datetime, timezone
from freezegun import freeze_time
from uc3m_consulting.project_document import ProjectDocument
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException
from uc3m_consulting.attribute import CifAttribute, DateAttribute

class Validator:
    """Coordinates complex business validation logic."""

    @staticmethod
    def validate_cif(cif_code: str):
        """Validates the CIF format and the control character checksum"""
        # Format check via Attribute Class
        cif_attr = CifAttribute(cif_code)

        # Checksum logic remains here (Business Rule, not just Format)
        digits_body = cif_attr.value[1:8]
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

        letter_prefix = cif_attr.value[0]
        control_char = cif_attr.value[8]
        control_letter_mapping = "JABCDEFGHI"

        if letter_prefix in ('A', 'B', 'E', 'H'):
            if str(control_digit) != control_char:
                raise EnterpriseManagementException("Invalid CIF character control number")
        elif letter_prefix in ('P', 'Q', 'S', 'K'):
            if control_letter_mapping[control_digit] != control_char:
                raise EnterpriseManagementException("Invalid CIF character control letter")
        else:
            raise EnterpriseManagementException("CIF type not supported")

    @staticmethod
    def validate_starting_date(date_str):
        """Validates date format via Attribute and checks range/current date"""
        DateAttribute(date_str) # Regex check
        try:
            my_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError as ex:
            raise EnterpriseManagementException("Invalid date format") from ex

        if not 2025 <= my_date.year <= 2050:
            raise EnterpriseManagementException("Invalid date format")

        if my_date < datetime.now(timezone.utc).date():
            raise EnterpriseManagementException("Project's date must be today or later.")

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
    def check_for_duplicate_project(new_project, projects_list):
        """Checks if the project already exists in the repository"""
        if any(existing == new_project.to_json() for existing in projects_list):
            raise EnterpriseManagementException("Duplicated project in projects list")

    @staticmethod
    def check_if_documents_found(count):
        """Raises an exception if no documents were found for the query"""
        if count == 0:
            raise EnterpriseManagementException("No documents found")
