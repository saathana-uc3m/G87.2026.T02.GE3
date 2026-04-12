"""Module for managing enterprise projects and documents"""
import re
from datetime import datetime, timezone
from uc3m_consulting.enterprise_project import EnterpriseProject
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException
from uc3m_consulting.enterprise_manager_config import (PROJECTS_STORE_FILE,
                                                       TEST_DOCUMENTS_STORE_FILE,
                                                       TEST_NUMDOCS_STORE_FILE)
from uc3m_consulting.json_operations import JsonRepository
from uc3m_consulting.validators import Validator

class EnterpriseManager:
    """
    Singleton Class for managing enterprise projects and documents.
    Ensures only one instance of the manager exists.
    """
    # Class variable to hold the single instance
    __instance = None

    def __new__(cls):
        """Overrides __new__ to implement the Singleton pattern."""
        if cls.__instance is None:
            cls.__instance = super(EnterpriseManager, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        """
        Constructor. Note: In a Python Singleton, __init__ will run
        every time EnterpriseManager() is called.
        Usually, setup logic is placed here or protected by a flag.
        """

    # --- CIF VALIDATION HELPERS ---
    def _calculate_cif_sums(self, digits_body):
        """Calculates even and odd sums for CIF validation."""
        even_sum = 0
        odd_sum = 0
        for i, digit_str in enumerate(digits_body):
            current_digit = int(digit_str)
            if i % 2 == 0:
                multiplied = current_digit * 2
                even_sum += (multiplied // 10) + (multiplied % 10) if multiplied > 9 else multiplied
            else:
                odd_sum += current_digit
        return even_sum + odd_sum

    def _validate_cif_control(self, letter_prefix, control_digit, control_char):
        """Validates the control character based on the CIF prefix."""
        control_letter_mapping = "JABCDEFGHI"
        if letter_prefix in ('A', 'B', 'E', 'H'):
            if str(control_digit) != control_char:
                raise EnterpriseManagementException("Invalid CIF character control number")
        elif letter_prefix in ('P', 'Q', 'S', 'K'):
            if control_letter_mapping[control_digit] != control_char:
                raise EnterpriseManagementException("Invalid CIF character control letter")
        else:
            raise EnterpriseManagementException("CIF type not supported")

    # --- DATE VALIDATION HELPERS ---
    def _check_date_regex(self, date_to_validate):
        """Checks if date string matches DD/MM/YYYY."""
        date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        if not date_pattern.fullmatch(date_to_validate):
            raise EnterpriseManagementException("Invalid date format")

    #pylint: disable=too-many-arguments, too-many-positional-arguments
    def register_project(self,
                         company_cif,
                         project_acronym,
                         project_description,
                         department,
                         date,
                         budget):
        """registers a new project"""
        Validator.validate_cif(company_cif)
        Validator.validate_registration_inputs(project_acronym,
                                               project_description,
                                               department,
                                               budget)
        Validator.validate_starting_date(date)

        new_project = EnterpriseProject(company_cif,
                                        project_acronym,
                                        project_description,
                                        department,
                                        date,
                                        budget)
        projects_list = JsonRepository.load(PROJECTS_STORE_FILE)

        if any(existing == new_project.to_json() for existing in projects_list):
            raise EnterpriseManagementException("Duplicated project in projects list")

        projects_list.append(new_project.to_json())
        JsonRepository.save(PROJECTS_STORE_FILE, projects_list)
        return new_project.project_id

    def find_documents_by_date(self, target_date_str):
        """Generates a JSON report counting valid documents for a specific date."""
        Validator.check_date_format(target_date_str)
        document_list = JsonRepository.load(TEST_DOCUMENTS_STORE_FILE)

        valid_count = 0
        for doc in document_list:
            doc_date = datetime.fromtimestamp(doc["register_date"]).strftime("%d/%m/%Y")
            if doc_date == target_date_str and Validator.validate_document_integrity(doc):
                valid_count += 1

        if valid_count == 0:
            raise EnterpriseManagementException("No documents found")

        reports = JsonRepository.load(TEST_NUMDOCS_STORE_FILE)
        reports.append({
            "Querydate": target_date_str,
            "ReportDate": datetime.now(timezone.utc).timestamp(),
            "Numfiles": valid_count
        })
        JsonRepository.save(TEST_NUMDOCS_STORE_FILE, reports)
        return valid_count
