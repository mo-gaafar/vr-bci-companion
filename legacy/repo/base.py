from models import PaginationIn, PaginationOut, PaginatedList
from abc import ABC, abstractmethod
from pymongo import MongoClient
from typing import Generic, TypeVar

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")


class BaseRepository(ABC, Generic[InputType, OutputType]):
    @abstractmethod
    def get_by_id(self, _id: str) -> OutputType:
        raise NotImplementedError

    @abstractmethod
    def create(self, obj: InputType) -> OutputType:
        raise NotImplementedError

    @abstractmethod
    def update(self, obj: InputType) -> OutputType:
        raise NotImplementedError

    @abstractmethod
    def delete(self, obj: InputType) -> OutputType:
        raise NotImplementedError

    @abstractmethod
    def get_all(self, pagination: PaginationIn) -> PaginatedList[OutputType]:
        raise NotImplementedError


class MongoRepository(BaseRepository[dict, dict]):
    @abstractmethod
    def get_collection(self):
        raise NotImplementedError

    def get_by_id(self, _id: str) -> dict:
        return self.get_collection().find_one({"_id": _id})

    def create(self, obj: dict) -> dict:
        return self.get_collection().insert_one(obj)

    def update(self, obj: dict) -> dict:
        return self.get_collection().update_one({"_id": obj["_id"]}, {"$set": obj})

    def delete(self, obj: dict) -> dict:
        return self.get_collection().delete_one({"_id": obj["_id"]})

    def get_all(self, page: PaginationIn) -> PaginatedList[dict]:
        return PaginatedList(
            data=self.get_collection().find().limit(page.limit).skip(page.skip),
            total=self.get_collection().count_documents({}),
        )
