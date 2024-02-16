from bson.objectid import ObjectId
from models.tickets import Ticket
from util.multitenant import get_tenant_db
from fastapi import HTTPException


def get_ticket_by_id(db, ticket_id: str):
    ticket = db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket["_id"] = str(ticket["_id"])
    return Ticket(**ticket)


def get_tickets_in_venue(db, venue_id: str):
    tickets = list(db.tickets.find({"venue_id": venue_id}))
    if len(tickets) == 0:
        raise HTTPException(status_code=404, detail="No tickets found")
    for ticket in tickets:
        ticket["_id"] = str(ticket["_id"])

    return [Ticket(**ticket) for ticket in tickets]


def get_tickets_in_order(db, order_id: str):
    tickets = list(db.tickets.find({"order_id": order_id}))
    if len(tickets) == 0:
        raise HTTPException(status_code=404, detail="No tickets found")
    for ticket in tickets:
        ticket["_id"] = str(ticket["_id"])
    return [Ticket(**ticket) for ticket in tickets]


def update_foodstuff_amenity(db, ticket_id, foodstuff):

    # # convert each element to dict
    # amenities = []
    # for amenity in foodstuff_amenities:
    #     amenities.append(amenity.dict())

    # db.tickets.update_one({"_id": ObjectId(ticket.id)}, {
    #                       "$set": {"amenities.foodstuff": amenities}})
    # update foodstuff element in amenities array with matching id
    db.tickets.update_one({"_id": ObjectId(ticket_id), "amenities.foodstuff.id": foodstuff.id}, {
        "$set": {"amenities.foodstuff.$": foodstuff.dict()}})

    return True
