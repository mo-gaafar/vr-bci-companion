
# from server.config import CONFIG

# import pytest
# from server.machine_learning.models import MLConfig
# from server.machine_learning.repo import MLRepo
# from server.bci.service import BCISession
# from server.bci.models import SessionState, ConnectionStatus, EEGMode
# from dataclasses import dataclass, field


# # Testing machine learning module funcitonality

from server.machine_learning.repo import MLRepo, S3MLRepo, LocalMLRepo
from server.machine_learning.models import StorageType, TrainingStatus
from server.machine_learning.service import MachineLearningService
from server.config import CONFIG

import pytest
from server.machine_learning.service import ml_service


def test_ml_service():
    '''
    Test the machine learning service on a class level
    '''
    # Create a new service instance
    service = MachineLearningService()
    assert service.model_queue == []
    assert service.models == {}
    assert isinstance(service.repo, MLRepo)
    assert service.repo.storage_type == CONFIG.ML_CONFIG.MODEL_STORAGE

    # Test the train_model method
    session_id = "1234"
    calibration_data = "calibration_data"
    service.train_model(session_id, calibration_data)

    # # Test the get_model_status method
    # status = service.get_model_status(session_id)
    # assert status == TrainingStatus.PENDING

    # # Test the load_model method
    # model = service.load_model(session_id)
    # assert model is None
