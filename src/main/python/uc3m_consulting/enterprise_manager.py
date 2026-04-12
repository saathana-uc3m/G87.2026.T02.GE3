"""Module for managing enterprise projects and documents"""
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

    @staticmethod
    def validate_cif(cif_code: str):
        """validates a Spanish CIF number (Tax Identification Code)"""
        if not isinstance(cif_code, str):
            raise EnterpriseManagementException("CIF code must be a string")

        cif_regex = re.compile(r"^[ABCDEFGHJKNPQRSUVW]\d{7}[0-9A-J]$")
        if not cif_regex.fullmatch(cif_code):
            raise EnterpriseManagementException("Invalid CIF format")

        total_sum = EnterpriseManager()._calculate_cif_sums(cif_code[1:8])
        control_digit_value = (10 - (total_sum % 10)) % 10
        EnterpriseManager()._validate_cif_control(cif_code[0], control_digit_value, cif_code[8])
        return True

    # --- DATE VALIDATION HELPERS ---
    def _check_date_regex(self, date_to_validate):
        """Checks if date string matches DD/MM/YYYY."""
        date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        if not date_pattern.fullmatch(date_to_validate):
            raise EnterpriseManagementException("Invalid date format")

    def validate_starting_date(self, date_to_validate):
        """validates the date format and range"""
        self._check_date_regex(date_to_validate)
        try:
            my_date = datetime.strptime(date_to_validate, "%d/%m/%Y").date()
        except ValueError as ex:
            raise EnterpriseManagementException("Invalid date format") from ex

        if my_date < datetime.now(timezone.utc).date() or not (2025 <= my_date.year <= 2050):
            raise EnterpriseManagementException("Project's date must be today or later.")
        return date_to_validate

    # --- REGISTRATION HELPERS ---
    def _validate_registration_inputs(self, acronym, description, dept, budget):
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

    def _load_json_data(self, file_path):
        """Generic JSON loader with error handling."""
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as ex:
            raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex

    def _save_json_data(self, file_path, data):
        """Generic JSON saver."""
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as file:
                json.dump(data, file, indent=2)
        except FileNotFoundError as ex:
            raise EnterpriseManagementException("Wrong file or file path") from ex

    #pylint: disable=too-many-arguments, too-many-positional-arguments
    def register_project(self, company_cif, project_acronym, project_description, department, date, budget):
        """registers a new project"""
        self.validate_cif(company_cif)
        self._validate_registration_inputs(project_acronym, project_description, department, budget)
        self.validate_starting_date(date)

        new_project = EnterpriseProject(company_cif, project_acronym, project_description, department, date, budget)
        projects_list = self._load_json_data(PROJECTS_STORE_FILE)

        if any(existing == new_project.to_json() for existing in projects_list):
            raise EnterpriseManagementException("Duplicated project in projects list")

        projects_list.append(new_project.to_json())
        self._save_json_data(PROJECTS_STORE_FILE, projects_list)
        return new_project.project_id

    # --- DOCUMENT REPORT HELPERS ---
    def _validate_document_integrity(self, document_data):
        """Checks if a single document's signature is valid."""
        timestamp = document_data["register_date"]
        doc_dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        with freeze_time(doc_dt_utc):
            p_doc = ProjectDocument(document_data["project_id"], document_data["file_name"])
            if p_doc.document_signature != document_data["document_signature"]:
                raise EnterpriseManagementException("Inconsistent document signature")
        return True

    def find_documents_by_date(self, target_date_str):
        """Generates a JSON report counting valid documents for a specific date."""
        self._check_date_regex(target_date_str)
        document_list = self._load_json_data(TEST_DOCUMENTS_STORE_FILE)

        valid_count = 0
        for doc in document_list:
            doc_date = datetime.fromtimestamp(doc["register_date"]).strftime("%d/%m/%Y")
            if doc_date == target_date_str and self._validate_document_integrity(doc):
                valid_count += 1

        if valid_count == 0:
            raise EnterpriseManagementException("No documents found")

        reports = self._load_json_data(TEST_NUMDOCS_STORE_FILE)
        reports.append({
            "Querydate": target_date_str,
            "ReportDate": datetime.now(timezone.utc).timestamp(),
            "Numfiles": valid_count
        })
        self._save_json_data(TEST_NUMDOCS_STORE_FILE, reports)
        return valid_count