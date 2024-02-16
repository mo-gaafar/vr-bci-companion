from typing import Optional


def id_to_str(dict: dict) -> dict:
    """Converts ObjectId to string."""
    if "_id" in dict:
        dict["id"] = str(dict["_id"])
    dict["_id"] = dict["id"]
    return dict


def db_to_dict(db_obj: Optional[dict]) -> dict:
    """Converts db object to dict."""
    if db_obj is not None:
        id_to_str(db_obj)
        return db_obj
    else:
        raise Exception("Object not found")

def obj_to_dict(obj) -> dict:
    """Converts db object to dict."""
    if obj is not None:
        dict = obj.dict()
        id_to_str(dict)
        dict["_id"] = str(dict["id"])
        return dict
    else:
        raise Exception("Object not found")