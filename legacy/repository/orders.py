from models.orders import Order, OrderOut
from util.multitenant import get_tenant_db
from fastapi import HTTPException
from bson.objectid import ObjectId


def get_order(db, order_id: str) -> Order:
    order = db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order["_id"] = str(order["_id"])
    order["id"] = order["_id"]
    order = Order(**order)
    return order


def get_orders(db, skip: int = 0, limit: int = 100):
    orders = db.orders.find().skip(skip).limit(limit)
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")
    for order in orders:
        order["_id"] = str(order["_id"])

    return [Order(**order) for order in orders]


# def create_order(db, order: OrderIn):
#     order = OrderIn(**order.dict())
#     order_id = db.orders.insert_one(order.dict()).inserted
#     id = str(order_id)
#     return OrderOut(**order.dict(), id=order_id)


def update_order(db, order_id: str, order: Order):
    order = Order(**order.dict())
    db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": order.dict()})
    return get_order(db, order_id)


# TODO: refactor later to reuse db
def delete_order(order_id: str, tenant_id: str):

    db = get_tenant_db(tenant_id, precheck=True)
    order = get_order(db, order_id)

    # delete order
    db.orders.delete_one({"_id": ObjectId(order_id)})
    # delete tickets
    db.tickets.delete_many({"order_id": ObjectId(order_id)})
    # remove from user's orders
    db.customers.update_one({"_id": ObjectId(order.buyer.id)}, {
        "$pull": {"orders": ObjectId(order_id)}})
    # remove tickets from guests
    guest_ids = []
    ticket_ids = []
    for item in order.order_items:
        guest_ids.append(item.customer.id)
        ticket_ids.append(item.ticket_id)

    db.guests.update_many({"_id": {"$in": guest_ids}}, {
                          "$pull": {"tickets": {"$in": ticket_ids}}})
