
from models.subscriptions import SubscriptionType, SubscriptionStatus
from datetime import datetime, timedelta
from typing import Optional


def get_time_shifted(start_date: datetime, subscription_type: Optional[SubscriptionType] = None):
    """Gets the supposed ending time for a subscription."""

    if subscription_type == SubscriptionType.monthly:
        return start_date + timedelta(days=30)
    if subscription_type == SubscriptionType.quarterly:
        return start_date + timedelta(days=90)
    if subscription_type == SubscriptionType.biyearly:
        return start_date + timedelta(days=180)
    if subscription_type == SubscriptionType.yearly:
        return start_date + timedelta(days=365)
        
    return None


def infer_subscription_status(start_date: datetime, end_date: datetime, subscription_type: Optional[SubscriptionType] = None) -> SubscriptionStatus:
    """Infers the status of a subscription based on its start and end dates."""

    if end_date is not None:
        if end_date < datetime.utcnow():
            return SubscriptionStatus.expired
    if start_date is not None and end_date is not None:
        if start_date <= datetime.utcnow() <= end_date:
            return SubscriptionStatus.active
    if start_date is not None and end_date is None:
        if start_date <= datetime.utcnow():
            return SubscriptionStatus.active
    if end_date != get_time_shifted(start_date, subscription_type):
        return SubscriptionStatus.cancelled



