"""JsonStoreMaster class"""
import json
import os
from datetime import datetime, timezone
from uc3m_consulting.enterprise_management_exception import EnterpriseManagementException
from uc3m_consulting.enterprise_manager_config import (PROJECTS_STORE_FILE,
                                                       TEST_DOCUMENTS_STORE_FILE,
                                                       TEST_NUMDOCS_STORE_FILE)

class JsonStoreMaster:
    """Base class handling raw JSON storage operations."""
    def __init__(self, file_store):
        self._file_name = file_store
        self._data_list = []

    def load_json_file(self):
        """Standard loading logic."""
        try:
            with open(self._file_name, "r", encoding="utf-8", newline="") as file:
                self._data_list = json.load(file)
        except FileNotFoundError:
            self._data_list = []
        except json.JSONDecodeError as ex:
            raise EnterpriseManagementException("JSON Decode Error - Wrong JSON Format") from ex
        return self._data_list

    def save_json_file(self):
        """Standard saving logic."""
        try:
            with open(self._file_name, "w", encoding="utf-8", newline="") as file:
                json.dump(self._data_list, file, indent=2)
        except (FileNotFoundError, PermissionError) as ex:
            raise EnterpriseManagementException("Wrong file or file path") from ex

    def add_item(self, item):
        """Generic append."""
        self.load_json_file()
        self._data_list.append(item)
        self.save_json_file()


class ProjectsJsonStore(JsonStoreMaster):
    """Child class specialized for project persistence."""
    def __init__(self):
        super().__init__(PROJECTS_STORE_FILE)

    def add_project(self, new_project_json, validator):
        """Includes the specific duplicate check logic."""
        projects = self.load_json_file()
        validator.check_for_duplicate_project(new_project_json, projects)
        self.add_item(new_project_json)


class DocumentsJsonStore(JsonStoreMaster):
    """Child class specialized for document retrieval."""
    def __init__(self):
        super().__init__(TEST_DOCUMENTS_STORE_FILE)

    def find_items_by_date(self, target_date_str, integrity_check_func):
        """Encapsulates the document searching loop."""
        if not os.path.exists(self._file_name):
            raise EnterpriseManagementException("No documents found")

        docs = self.load_json_file()
        count = 0
        for doc in docs:
            doc_date = datetime.fromtimestamp(doc["register_date"]).strftime("%d/%m/%Y")
            if doc_date == target_date_str and integrity_check_func(doc):
                count += 1
        return count


class ReportsJsonStore(JsonStoreMaster):
    """Child class specialized for report history."""
    def __init__(self):
        super().__init__(TEST_NUMDOCS_STORE_FILE)

    def save_report(self, query_date, count):
        """Encapsulates the report format."""
        report_entry = {
            "Querydate": query_date,
            "ReportDate": datetime.now(timezone.utc).timestamp(),
            "Numfiles": count
        }
        self.add_item(report_entry)
