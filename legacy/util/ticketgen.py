# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
from bson.objectid import ObjectId
from models.business import Business, Venue
from models.orders import Order
from models.tickets import Ticket
from fpdf import FPDF
from io import BytesIO
import os
import base64
import qrcode
from typing import List


def generate_qr_code_html(data: str) -> str:
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, "PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f'<img src="data:image/png;base64,{qr_code_base64}" alt="QR Code" border="0" width="200" style="display: block; margin-left: auto; margin-right: auto; width: 50%;"/>'


def generate_qr_code_png(data: str, filename: str) -> None:
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, "PNG")
    with open(filename, "wb") as f:
        f.write(buffer.getvalue())


class TicketPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.current_x = 0
        self.current_y = 0
        self.order_id = "Null"

    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "", align="C", ln=1)
        self.cell(0, 10, f"Order #{self.order_id}", align="C", ln=1)
        # move position up 10 units
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "Page %s" % self.page_no(), 0, 0, "C")

    def add_tickets(self, ticket_data, rendered_html=False):
        x = self.current_x
        y = self.current_y

        width = self.w - 2 * x
        height = self.h - 2 * y

        spacing = 20  # Spacing between tickets
        num_tickets_per_page = 3
        ticket_height = (height - spacing *
                         (num_tickets_per_page + 1)) / num_tickets_per_page

        for i, ticket in enumerate(ticket_data):
            if i != 0 and i % num_tickets_per_page == 0:
                self.add_page()
                self.current_x = 0  # Reset X position

            col = i % num_tickets_per_page

            ticket_x = x
            ticket_y = y + col * (ticket_height + spacing) + spacing
            if rendered_html is False:
                # Draw rectangle with border and fill
                self.rect(ticket_x, ticket_y, width, ticket_height, style="D")

                # Align QR code to the right with a margin of 10
                qr_x = ticket_x + width - 50 - 10
                qr_y = ticket_y + (ticket_height - 40) / \
                    2  # Center QR code vertically
                # Generate and draw QR code
                qr_img_filename = f"/tmp/qr_code{i}.png"
                generate_qr_code_png(ticket["ticket_id"], qr_img_filename)

                # Set the position and dimensions of the QR code
                self.image(qr_img_filename, qr_x, qr_y, w=40)

                # Add ticket data
                ticket_info_x = ticket_x + 10  # Left margin for ticket data
                ticket_info_y = ticket_y + 10  # Top margin for ticket data

                # Larger font for name
                self.set_font("Arial", size=16, style="B")
                self.set_xy(ticket_info_x, ticket_info_y)
                self.cell(0, 15, ticket["name"], ln=1,
                          align="L", fill=False, border=0)

                self.set_xy(ticket_info_x, ticket_info_y + 20)
                self.cell(
                    0, 10, f"Ticket Type: {ticket['ticket_tier_name']}", ln=1, align="L", fill=False, border=0)
                # Reset font size for other details
                self.set_font("Arial", size=12)
                self.set_xy(ticket_info_x, ticket_info_y + 30)
                self.cell(
                    0, 10, f"Ticket ID: {ticket['ticket_id']}", ln=1, align="L", fill=False, border=0)
                self.set_xy(ticket_info_x, ticket_info_y + 40)
            elif rendered_html is True:
                # loop on ticket_data images and add them to the pdf with the correct position and spacing
                # Find generated ticket image
                ticket_img_filename = f"tmp/{ticket['output_file']}"
                # Set the position and dimensions of the ticket image
                self.image(ticket_img_filename, ticket_x, ticket_y, w=width)
                # Set cursor to the bottom of the ticket image
                self.set_xy(ticket_x, ticket_y + ticket_height)
                # Add spacing
                self.ln(spacing)
                # if next ticket would take up  more than 1/3 of the page, add a new page
                if (i + 1) % num_tickets_per_page == 0 and i != len(ticket_data) - 1:
                    self.add_page()
                    self.current_x = 0
                    self.current_y = 0


async def generate_ticket_order_pdf(ticket_data: list[dict], filename: str, rendered_html=False):
    pdf = TicketPDF()
    from util.ticket_render import render_tickets_png
    if rendered_html is True:
        # render tickets to png
        await render_tickets_png(ticket_data)

    pdf.order_id = ticket_data[0]["order_id"]
    pdf.add_page()

    pdf.add_tickets(ticket_data, rendered_html)

    pdf.output(filename)  # save to file

    # get output as bytes
    pdf_buffer = str(pdf.output(dest="S")).encode("latin-1")
    stream = BytesIO(pdf_buffer)

    return stream


# def invitation_email(ticket_id, event_img_url, guest_name, msg_body, maps_link):
#     '''
#     Generate attendee qr code and embed in html
#     QR code contains attendee id
#     '''
#     # generate qr code
#     payload = str(ticket_id)
#     qr_code = generate_qr_code_html(payload)
#     # embed in html
#     html = f'''
#     <html>
#         <head></head>
#         <body>
#             <img src="{event_img_url}" alt="logo" border="0" width="500" style="display: block; margin-left: auto; margin-right: auto; width: 50%;"/>

#             <p>Dear, {guest_name}</p>
#             <p>{msg_body}</p>

#             <p>This is your event pass.</p>
#             <p>Scan this QR code to check in.</p>
#             <table>
#                 <tr> {qr_code} </tr>
#             </table>
#             <p> Not working? check the attached image file.</p>
#         </body>
#     </html>
#     '''

#     plaintext = f'''
#     QR Code Tickets Confirmation Order #{order_id}

#     Get ready, {attendee["name"]}!

#     {msg_body}

#     This is your event pass.
#     Scan this QR code to check in.
#     {payload}
#     '''

#     return html, plaintext


def format_order_invitation(venue: Venue, business: Business, order: Order):
    '''
    Send invitation email to order buyer
    '''
    # get order details
    subject = 'Ticket order confirmation for ' + \
        venue.name + ' Order #' + str(order.id)
    msg_body = f'''
    <html>
        <head>
            <style>
                /* Add any additional CSS styling here */
                body {{
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 20px;
                }}
                .email-body {{
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    margin: 0 auto;
                    max-width: 600px;
                    padding: 20px;
                    border: 1px solid #333;
                    background-color: #ffffff;
                }}
                .logo-image {{
                    display: block;
                    max-width: 200px;
                    height: auto;
                    margin: 0 auto;
                    margin-bottom: 20px;
                }}
                h1 {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                h2 {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                p {{
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="email-body">
                <img src="{business.logo_link}" alt="Business Logo" class="logo-image">
                <h1>Order Confirmation</h1>
                <p>Dear {order.buyer.name},</p>
                <p>Thank you for your order. Here are your order details:</p>
                <h2>Order Information</h2>
                <p><strong>Order #: </strong>{order.id}</p>
                <p><strong>Event: </strong>{venue.name}</p>
                <p><strong>Order Date: </strong>{order.date_created}</p>
                <h2>Attached Ticket Order</h2>
                <p>Attached is your ticket order.</p>
                <p>See you at the event!</p>
                <h2>Contact Details</h2>
                <p><strong>{business.name}</strong></p>
                <p><strong>Email: </strong>{business.email}</p>
                <p><strong>Phone: </strong>{business.phone}</p>
            </div>
        </body>
    </html>
    '''

    return subject, msg_body


def format_ticket_invitation(venue: Venue, business: Business, ticket: Ticket):
    '''
    Send invitation email to guest
    '''
    subject = 'Your ticket for ' + venue.name
    msg_body = f'''
    <html>
        <head>
            <style>
                /* Add any additional CSS styling here */
                body {{
                    background-color: #f3f3f3;
                    margin: 0;
                    padding: 20px;
                }}
                .email-container {{
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    margin: 0 auto;
                    max-width: 600px;
                    padding: 20px;
                    border: 1px solid #333;
                    background-color: #ffffff;
                }}
                .header-image {{
                    width: 100%;
                    max-width: 600px;
                    height: auto;
                    margin-bottom: 20px;
                }}
                h1 {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                h2 {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                p {{
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <img src="{venue.thumbnail_link}" alt="Header Image" class="header-image">
                <h1>Confirmation Email</h1>
                <h3> Welcome to {venue.name} ! </h3>
                <p> Waiting for you today to join us. </p>
                <p> Here is your QR code ticket 🎫, please show it to the gatekeeper when you arrive.</p> 
                <br>
                <br>

                <p> Regards, </p>
                <p>{business.name} Team </p>
                <p>{business.email}</p>
                <p>{business.phone}</p>

                <br>
                <br>

                <p> ! {venue.name} اهلا بك في  </p>
                <p> ننتظرك اليوم للانضمام الينا. </p>
                <p> هذا هو تذكرتك الالكترونية 🎫، يرجى اظهارها لحارس البوابة عند وصولك. </p>
                <br>
                <br>

                <p> تحياتنا, </p>
                <p> {business.name} فريق  </p>
            </div>
        </body>
    </html>
    '''

    return subject, msg_body
