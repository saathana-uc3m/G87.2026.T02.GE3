"""Module for managing enterprise projects and documents"""
from datetime import datetime, timezone
from uc3m_consulting.enterprise_project import EnterpriseProject
from uc3m_consulting.enterprise_manager_config import (PROJECTS_STORE_FILE,
                                                       TEST_DOCUMENTS_STORE_FILE,
                                                       TEST_NUMDOCS_STORE_FILE)
from uc3m_consulting.json_operations import JsonRepository
from uc3m_consulting.validators import Validator
from uc3m_consulting.attribute import (AcronymAttribute, DescriptionAttribute,
                                       DateAttribute, DepartmentAttribute,
                                       BudgetAttribute)

class EnterpriseManager:
    """Singleton Class for managing enterprise projects and documents"""
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(EnterpriseManager, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        pass

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def register_project(self,
                         company_cif,
                         project_acronym,
                         project_description,
                         department,
                         date,
                         budget):
        """Registers a new project by coordinating validation and persistence"""

        # 1. Format Validations (Each raises EnterpriseManagementException internally)
        AcronymAttribute(project_acronym)
        DescriptionAttribute(project_description)
        DepartmentAttribute(department)
        BudgetAttribute(budget)

        # 2. Complex Business Validations
        Validator.validate_cif(company_cif)
        Validator.validate_starting_date(date)

        # 3. Persistence
        new_project = EnterpriseProject(company_cif,
                                        project_acronym,
                                        project_description,
                                        department,
                                        date,
                                        budget)

        projects_list = JsonRepository.load(PROJECTS_STORE_FILE)

        # Note: We use Validator or a helper if we want to remove the 'raise' below
        Validator.check_for_duplicate_project(new_project, projects_list)

        projects_list.append(new_project.to_json())
        JsonRepository.save(PROJECTS_STORE_FILE, projects_list)
        return new_project.project_id

    def find_documents_by_date(self, target_date_str):
        """Coordinates the document report generation"""
        DateAttribute(target_date_str)
        document_list = JsonRepository.load(TEST_DOCUMENTS_STORE_FILE)

        valid_count = 0
        for doc in document_list:
            doc_date = datetime.fromtimestamp(doc["register_date"]).strftime("%d/%m/%Y")
            if doc_date == target_date_str and Validator.validate_document_integrity(doc):
                valid_count += 1

        Validator.check_if_documents_found(valid_count)

        self._save_report(target_date_str, valid_count)
        return valid_count

    def _save_report(self, query_date, count):
        """Internal helper to handle report persistence"""
        reports = JsonRepository.load(TEST_NUMDOCS_STORE_FILE)
        reports.append({
            "Querydate": query_date,
            "ReportDate": datetime.now(timezone.utc).timestamp(),
            "Numfiles": count
        })
        JsonRepository.save(TEST_NUMDOCS_STORE_FILE, reports)
