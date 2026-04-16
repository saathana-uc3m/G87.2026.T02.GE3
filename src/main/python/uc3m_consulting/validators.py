"""Module containing the Validator class for cross-attribute business rules"""
from datetime import datetime, timezone
from freezegun import freeze_time
from uc3m_consulting.project_document import ProjectDocument
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException

class Validator:
    """Coordinates complex business validation logic involving system state."""

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
