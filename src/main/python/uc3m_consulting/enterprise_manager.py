"""Module for managing enterprise projects and documents"""
from datetime import datetime, timezone
from uc3m_consulting.enterprise_project import EnterpriseProject
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException
from uc3m_consulting.enterprise_manager_config import (PROJECTS_STORE_FILE,
                                                       TEST_DOCUMENTS_STORE_FILE,
                                                       TEST_NUMDOCS_STORE_FILE)
from uc3m_consulting.json_operations import JsonRepository
from uc3m_consulting.validators import Validator

class EnterpriseManager:
    """Singleton Class for managing enterprise projects and documents"""
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(EnterpriseManager, cls).__new__(cls)
        return cls.__instance

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def register_project(self,
                         company_cif,
                         project_acronym,
                         project_description,
                         department,
                         date,
                         budget):
        """Registers a new project by coordinating validation and persistence"""

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
        """Generates a JSON report counting valid documents for a specific date"""
        Validator.check_date_format(target_date_str)
        document_list = JsonRepository.load(TEST_DOCUMENTS_STORE_FILE)

        valid_count = self._count_valid_documents(document_list, target_date_str)

        if valid_count == 0:
            raise EnterpriseManagementException("No documents found")

        self._save_report(target_date_str, valid_count)

        return valid_count

    def _count_valid_documents(self, document_list, target_date_str):
        """Internal helper to filter valid documents"""
        count = 0
        for doc in document_list:
            doc_date = datetime.fromtimestamp(doc["register_date"]).strftime("%d/%m/%Y")
            if doc_date == target_date_str and Validator.validate_document_integrity(doc):
                count += 1
        return count

    def _save_report(self, query_date, count):
        """Internal helper to handle the report persistence"""
        reports = JsonRepository.load(TEST_NUMDOCS_STORE_FILE)
        reports.append({
            "Querydate": query_date,
            "ReportDate": datetime.now(timezone.utc).timestamp(),
            "Numfiles": count
        })
        JsonRepository.save(TEST_NUMDOCS_STORE_FILE, reports)
