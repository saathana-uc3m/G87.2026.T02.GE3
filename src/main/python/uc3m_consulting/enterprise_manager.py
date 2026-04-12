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
