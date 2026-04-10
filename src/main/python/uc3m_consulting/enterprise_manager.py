"""Module """
import re
import json

from datetime import datetime, timezone
from freezegun import freeze_time
from uc3m_consulting.enterprise_project import EnterpriseProject
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException
from uc3m_consulting.enterprise_manager_config import (PROJECTS_STORE_FILE,
                                                       TEST_DOCUMENTS_STORE_FILE,
                                                       TEST_NUMDOCS_STORE_FILE)
from uc3m_consulting.project_document import ProjectDocument

class EnterpriseManager:
    """Class for providing the methods for managing the orders"""
    def __init__(self):
        pass

    @staticmethod
    def validate_cif(cif_code: str):
        """validates a Spanish CIF number (Tax Identification Code)"""
        if not isinstance(cif_code, str):
            raise EnterpriseManagementException("CIF code must be a string")

        cif_regex_pattern = re.compile(r"^[ABCDEFGHJKNPQRSUVW]\d{7}[0-9A-J]$")
        if not cif_regex_pattern.fullmatch(cif_code):
            raise EnterpriseManagementException("Invalid CIF format")

        letter_prefix = cif_code[0]
        digits_body = cif_code[1:8]
        control_character = cif_code[8]

        even_sum = 0
        odd_sum = 0

        for i in range(len(digits_body)):
            current_digit = int(digits_body[i])
            if i % 2 == 0:
                # even indices
                multiplied_digit = current_digit * 2
                if multiplied_digit > 9:
                    # Add digits of the result
                    even_sum += (multiplied_digit // 10) + (multiplied_digit % 10)
                else:
                    even_sum += multiplied_digit
            else:
                # odd indices
                odd_sum += current_digit

        total_sum = even_sum + odd_sum
        units_digit = total_sum % 10
        control_digit_value = 10 - units_digit

        if control_digit_value == 10:
            control_digit_value = 0

        control_letter_mapping = "JABCDEFGHI"

        if letter_prefix in ('A', 'B', 'E', 'H'):
            if str(control_digit_value) != control_character:
                raise EnterpriseManagementException("Invalid CIF character control number")
        elif letter_prefix in ('P', 'Q', 'S', 'K'):
            if control_letter_mapping[control_digit_value] != control_character:
                raise EnterpriseManagementException("Invalid CIF character control letter")
        else:
            raise EnterpriseManagementException("CIF type not supported")

        return True

    def validate_starting_date(self, date_to_validate):
        """validates the date format using regex"""
        date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        pattern_match = date_pattern.fullmatch(date_to_validate)
        if not pattern_match:
            raise EnterpriseManagementException("Invalid date format")

        try:
            my_date = datetime.strptime(date_to_validate, "%d/%m/%Y").date()
        except ValueError as ex:
            raise EnterpriseManagementException("Invalid date format") from ex

        if my_date < datetime.now(timezone.utc).date():
            raise EnterpriseManagementException("Project's date must be today or later.")

        if my_date.year < 2025 or my_date.year > 2050:
            raise EnterpriseManagementException("Invalid date format")
        return date_to_validate

    #pylint: disable=too-many-arguments, too-many-positional-arguments
    def register_project(self,
                         company_cif: str,
                         project_acronym: str,
                         project_description: str,
                         department: str,
                         date: str,
                         budget: str):
        """registers a new project"""
        self.validate_cif(company_cif)

        acronym_pattern = re.compile(r"^[a-zA-Z0-9]{5,10}")
        acronym_match = acronym_pattern.fullmatch(project_acronym)
        if not acronym_match:
            raise EnterpriseManagementException("Invalid acronym")

        description_pattern = re.compile(r"^.{10,30}$")
        description_match = description_pattern.fullmatch(project_description)
        if not description_match:
            raise EnterpriseManagementException("Invalid description format")

        department_pattern = re.compile(r"(HR|FINANCE|LEGAL|LOGISTICS)")
        department_match = department_pattern.fullmatch(department)
        if not department_match:
            raise EnterpriseManagementException("Invalid department")

        self.validate_starting_date(date)

        try:
            budget_float = float(budget)
        except ValueError as exc:
            raise EnterpriseManagementException("Invalid budget amount") from exc

        budget_string = str(budget_float)
        if '.' in budget_string:
            decimal_places = len(budget_string.split('.')[1])
            if decimal_places > 2:
                raise EnterpriseManagementException("Invalid budget amount")

        if budget_float < 50000 or budget_float > 1000000:
            raise EnterpriseManagementException("Invalid budget amount")

        new_project = EnterpriseProject(company_cif=company_cif,
                                        project_acronym=project_acronym,
                                        project_description=project_description,
                                        department=department,
                                        starting_date=date,
                                        project_budget=budget)

        try:
            with open(PROJECTS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                projects_list = json.load(file)
        except FileNotFoundError:
            projects_list = []
        except json.JSONDecodeError as ex:
            raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex

        for existing_project_data in projects_list:
            if existing_project_data == new_project.to_json():
                raise EnterpriseManagementException("Duplicated project in projects list")

        projects_list.append(new_project.to_json())

        try:
            with open(PROJECTS_STORE_FILE, "w", encoding="utf-8", newline="") as file:
                json.dump(projects_list, file, indent=2)
        except FileNotFoundError as ex:
            raise EnterpriseManagementException("Wrong file or file path") from ex
        except json.JSONDecodeError as ex:
            raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex

        return new_project.project_id


    def find_documents_by_date(self, target_date_str):
        """
        Generates a JSON report counting valid documents for a specific date.

        Checks cryptographic hashes and timestamps to ensure historical data integrity.
        Saves the output to 'resultado.json'.

        Args:
            target_date_str (str): date to query.

        Returns:
            number of documents found if report is successfully generated and saved.

        Raises:
            EnterpriseManagementException: On invalid date, file IO errors,
                missing data, or cryptographic integrity failure.
        """
        date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        pattern_match = date_pattern.fullmatch(target_date_str)
        if not pattern_match:
            raise EnterpriseManagementException("Invalid date format")

        try:
            target_date = datetime.strptime(target_date_str, "%d/%m/%Y").date()
        except ValueError as ex:
            raise EnterpriseManagementException("Invalid date format") from ex


        # open documents
        try:
            with open(TEST_DOCUMENTS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                document_list = json.load(file)
        except FileNotFoundError as ex:
            raise EnterpriseManagementException("Wrong file or file path") from ex

        valid_document_count = 0

        # Loop to find
        for document_data in document_list:
            registration_timestamp = document_data["register_date"]

            # String conversion for easy match
            doc_date_str = datetime.fromtimestamp(registration_timestamp).strftime("%d/%m/%Y")

            if doc_date_str == target_date_str:
                document_datetime_utc = datetime.fromtimestamp(registration_timestamp, tz=timezone.utc)

                with freeze_time(document_datetime_utc):
                    # Check the project id (thanks to freezetime)
                    # If project_id are different then the data has been manipulated
                    document_instance = ProjectDocument(
                        document_data["project_id"],
                        document_data["file_name"]
                    )

                    if document_instance.document_signature == document_data["document_signature"]:
                        valid_document_count += 1
                    else:
                        raise EnterpriseManagementException("Inconsistent document signature")

        if valid_document_count == 0:
            raise EnterpriseManagementException("No documents found")

        # Prepare JSON report data
        current_timestamp = datetime.now(timezone.utc).timestamp()
        report_entry = {
            "Querydate": target_date_str,
            "ReportDate": current_timestamp,
            "Numfiles": valid_document_count
        }

        try:
            with open(TEST_NUMDOCS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                reports_history = json.load(file)
        except FileNotFoundError:
            reports_history = []
        except json.JSONDecodeError as ex:
            raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex

        reports_history.append(report_entry)

        try:
            with open(TEST_NUMDOCS_STORE_FILE, "w", encoding="utf-8", newline="") as file:
                json.dump(reports_history, file, indent=2)
        except FileNotFoundError as ex:
            raise EnterpriseManagementException("Wrong file or file path") from ex

        return valid_document_count
