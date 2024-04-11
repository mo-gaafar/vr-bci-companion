from abc import ABC, abstractmethod
from typing import Any, Dict
import json

from server.database import MongoDB

BCI_USE_MONGO = False


class ISessionRepository(ABC):
    '''Interface for saving session data to a repository.'''
    @abstractmethod
    def save_session(self, session_data: Dict[str, Any]) -> None:
        pass


class IEEGDataRepository(ABC):
    '''Interface for saving EEG data to a repository.'''
    @abstractmethod
    def save_eeg_data(self, session_id: str, eeg_data: Dict[str, Any]) -> None:
        pass


class MongoDBSessionRepository(ISessionRepository):
    def __init__(self):
        self.db = MongoDB
        self.collection = self.db['sessions']

    def save_session(self, session_data: Dict[str, Any]) -> None:
        self.collection.insert_one(session_data)


class MongoDBEEGDataRepository(IEEGDataRepository):
    def __init__(self):
        self.db = MongoDB
        self.collection = self.db['eeg_data']

    def save_eeg_data(self, session_id: str, eeg_data: Dict[str, Any]) -> None:
        eeg_data['session_id'] = session_id
        self.collection.insert_one(eeg_data)


class LocalFileSessionRepository(ISessionRepository):
    def __init__(self, base_path: str = "./data/sessions/"):
        self.base_path = base_path

    def save_session(self, session_data: Dict[str, Any]) -> None:
        with open(f"{self.base_path}{session_data['id']}.json", 'w') as file:
            json.dump(session_data, file)


class LocalFileEEGDataRepository(IEEGDataRepository):
    def __init__(self, base_path: str = "./data/eeg_data/"):
        self.base_path = base_path

    def save_eeg_data(self, session_id: str, eeg_data: Dict[str, Any]) -> None:
        with open(f"{self.base_path}{session_id}.json", 'a') as file:
            json.dump(eeg_data, file)
            file.write('\n')



# Choose the repository based on configuration
if BCI_USE_MONGO:
    session_repo = MongoDBSessionRepository()
    eeg_data_repo = MongoDBEEGDataRepository()
else:
    session_repo = LocalFileSessionRepository()
    eeg_data_repo = LocalFileEEGDataRepository()


