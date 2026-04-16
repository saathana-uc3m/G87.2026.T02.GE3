"""Module for managing enterprise projects and documents"""
from uc3m_consulting.enterprise_project import EnterpriseProject
from uc3m_consulting.json_operations import (ProjectsJsonStore,
                                             DocumentsJsonStore,
                                             ReportsJsonStore)
from uc3m_consulting.validators import Validator
from uc3m_consulting.attribute import (AcronymAttribute, DescriptionAttribute,
                                       DateAttribute, DateFormatAttribute,
                                       DepartmentAttribute, BudgetAttribute,
                                       CifAttribute)
class EnterpriseManager:
    """Singleton Class for managing enterprise projects and documents"""
    __instance = None
    _projects_store: ProjectsJsonStore
    _docs_store: DocumentsJsonStore
    _reports_store: ReportsJsonStore

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(EnterpriseManager, cls).__new__(cls)
            cls.__instance._projects_store = ProjectsJsonStore()
            cls.__instance._docs_store = DocumentsJsonStore()
            cls.__instance._reports_store = ReportsJsonStore()
        return cls.__instance

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def register_project(self, company_cif, project_acronym, project_description,
                         department, date, budget):
        """Registers a project if all values are valid"""
        CifAttribute(company_cif)
        AcronymAttribute(project_acronym)
        DescriptionAttribute(project_description)
        DepartmentAttribute(department)
        DateAttribute(date)
        BudgetAttribute(budget)

        new_project = EnterpriseProject(company_cif, project_acronym,
                                        project_description, department, date, budget)

        self._projects_store.add_project(new_project.to_json(), Validator)

        return new_project.project_id

    def find_documents_by_date(self, target_date_str):
        """Uses a target date to find documents"""
        DateFormatAttribute(target_date_str)

        valid_count = self._docs_store.find_items_by_date(
            target_date_str,
            Validator.validate_document_integrity
        )

        Validator.check_if_documents_found(valid_count)
        self._reports_store.save_report(target_date_str, valid_count)

        return valid_count
