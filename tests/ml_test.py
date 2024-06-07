
# from server.config import CONFIG

# import pytest
# from server.machine_learning.models import MLConfig
# from server.machine_learning.repo import MLRepo
# from server.bci.service import BCISession
# from server.bci.models import SessionState, ConnectionStatus, EEGMode
# from dataclasses import dataclass, field


# # Testing machine learning module funcitonality

import time
from server.machine_learning.repo import MLRepo, S3MLRepo, LocalMLRepo
from server.machine_learning.models import StorageType, TrainingStatus
from server.machine_learning.service import MachineLearningService
from server.config import CONFIG

import pytest
from server.machine_learning.service import ml_service

@pytest.mark.skip(reason="Waiting for test data to be available")
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
    calibration_data = "source_np.pkl"
    service.add_to_queue(session_id, calib_path=calibration_data)

    # Test the get_model_status method
    status = service.get_model_status(session_id)
    assert status == TrainingStatus.COMPLETED

    # Test the load_model method
    model = service.load_model(session_id)

    # Test the model prediction
    test_3s_raw = "test_3s_raw.pkl"
    data = service.repo._load_from_storage(test_3s_raw)
    prediction = service.classify(session_id, data)

    assert prediction == "feet" or prediction == "rest"
    