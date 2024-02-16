from util.ticketgen import generate_qr_code_html
from models.business import Venue
from models.orders import Order
from datetime import datetime, timedelta
# import pandas as pd
from models.tickets import Ticket
from config.config import pytz_timezone


# def excel_to_df(file):
#     '''Reads an excel file and returns a dictionary of dataframes'''
#     df_dict = pd.read_excel(file, sheet_name=None)
#     return df_dict


# def df_to_dict(df):
#     '''Converts a dataframe to a dictionary'''
#     return df.to_dict(orient='records')


# def excel_to_dict(file):
#     '''Reads an excel file and returns a dictionary of dictionaries'''
#     df_dict = excel_to_df(file)
#     return {sheet: df_to_dict(df) for sheet, df in df_dict.items()}


# def df_to_json(df):
#     '''Converts a dataframe to a json'''
#     return df.to_json(orient='records')


# def csv_to_model(file, model):
#     '''Reads a csv file and checks model's required fields'''
#     df = pd.read_csv(file)
#     # check if all required fields are present
#     required_fields = model.__fields__.keys()
#     if not set(required_fields).issubset(set(df.columns)):
#         raise Exception(f"Required fields missing: {required_fields}")
#     # create model object
#     model = model(**df.to_dict(orient='records'))
#     return model


def ISO_to_human_hours_minutes(input):
    '''Converts a time in ISO format to human readable hours and minutes'''
    # if less than an hour return minutes
    # how to handle timedelta?
    hours = 0
    minutes = 0
    print(type(input))
    if str(type(input)) == "<class 'datetime.timedelta'>":
        # Get the total number of seconds in the timedelta
        total_seconds = input.total_seconds()

        # Calculate hours and minutes
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        # print(f"Hours: {hours}")
        # print(f"Minutes: {minutes}")
    else:
        hours = input.hour
        minutes = input.minute

    if hours == 0:
        return f"{hours} mins"
    # if more than an hour return hours and minutes
    else:
        return f"{hours} hours and {minutes} mins"


def guest_status_message(ticket: Ticket) -> str:
    """
    Returns a status message based on the guest's activity
    - Currently attending, checked in at {time}
    - Checked out at {time}, stayed for {duration} hours
    - Did not arrive yet
    """

    # derive from checkin and checkout timestamps in checkin history
    # from util.parsing import ISO_to_human_hours_minutes
    if ticket.check_in is None:
        # if ticket.date_start.date != ticket.date_created.date:
        # return f"Sold today to start on {ticket.date_start.strftime('%b %d')}"
        return "Did not arrive yet"
    elif ticket.check_out is None:
        return f"Currently attending, checked in at ??"
    else:
        if ticket.is_active:
            return f"Attending, checked in again at ??"
        else:
            duration_stay = ISO_to_human_hours_minutes(
                ticket.check_out - ticket.check_in)
            return f"Checked out at ?? , stayed for {duration_stay}"


def create_ticket_dict(order_id, order: Order):
    order_id = order.id
    order_items = order.order_items
    ticket_data = []
    for item in order_items:
        ticket_data.append({
            "name": item.customer.name,
            "ticket_tier_name": item.ticket_tier_name,
            "ticket_id": item.ticket_id,
            "order_id": order_id,
        })
    return ticket_data


def prepare_ticket_render_item(order: Order, ticket_id, venue: Venue):
    order_item = None
    for order_item in order.order_items:
        # inefficient search, but works
        if order_item.ticket_id == ticket_id:
            break
    if order_item is None:
        return None

    ticket_hour_start = order_item.date_start.astimezone(
        pytz_timezone).strftime("%I:%M %p")

    if order_item.date_expire is None:
        ticket_hour_end = "N/A"
    else:
        ticket_hour_end = order_item.date_expire.astimezone(
            pytz_timezone).strftime("%I:%M %p")

    ticket_hour_gates = order_item.date_start.astimezone(
        pytz_timezone) - timedelta(hours=.5)
    ticket_hour_gates = ticket_hour_gates.strftime("%H:%M")
    keys_dict = {
        "venue_name": venue.name,
        "order_id": order.id,
        "ticket_id": order_item.ticket_id,
        "ticket_hour_start": ticket_hour_start,
        "ticket_hour_gates": ticket_hour_gates,
        "ticket_hour_end": ticket_hour_end,
        "ticket_tier_name": order_item.ticket_tier_name,
        "ticket_date_start": order_item.date_start.astimezone(
            pytz_timezone).strftime("%d/%m"),
        "venue_location": venue.location,
        "qr_png": "",
        "output_file": "ticket.png"
    }
    keys_dict["qr_png"] = generate_qr_code_html(keys_dict["ticket_id"])
    keys_dict["output_file"] = "ticket" + str(ticket_id[:-5]) + ".png"
    return keys_dict


def prepare_ticket_render_dictlist(order: Order, venue: Venue):
    ticket_data = []
    # TODO: add ticket end time handling
    for index, order_item in enumerate(order.order_items):
        keys_dict = prepare_ticket_render_item(
            order, order_item.ticket_id, venue)
        ticket_data.append(keys_dict)
    return ticket_data
