from models.tickets import Ticket
from models.business import Venue
from models.orders import Order
from util.parsing import prepare_ticket_render_item
from pyppeteer import launch
import jinja2
import os

template_dir = "./templates"
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

# install wkhtmltopdf
# https://wkhtmltopdf.org/downloads.html


def render_str(template, is_string=False, **params):
    '''Renders a jinja2 template with the given params
    Args:
        template: the template file name OR the template string
        is_string: if True, template is a string, else it is a file name
        '''

    if is_string is True:
        t = jinja_env.from_string(template)
    else:
        t = jinja_env.get_template(template)
    # get template as string
    # t = jinja2.Template(t)
    return t.render(params)


def render_ticket(keys_dict, html_name="ticket.html", css_name="style.css"):
    '''Renders a ticket html file with the given keys_dict'''
    return render_str(template=html_name, **keys_dict)


def get_ticket_html(order: Order, ticket_id, venue: Venue, html_content, css_content, is_filepath=True):
    '''Returns the html content of the ticket'''
    # TODO: this is a dummy implementation, should instead take html_content as string or file
    # order = get_order_by_ticket_id(ticket_id, tenant_id)

    formatted_data = prepare_ticket_render_item(order, ticket_id, venue)
    if formatted_data is None:
        return None

    if is_filepath is True:
        html_content = open(html_content, "r")
        html_content = html_content.read()
        css_content = open(css_content, "r")
        css_content = css_content.read()
    # embed css into html str
    html_str = render_str(template=html_content,
                          is_string=True, **formatted_data)
    html_str = html_str.replace(
        "</head>", "<style>" + css_content + "</style></head>")
    return html_str


async def ticket_png_operation(page, keys_dict, output_file="ticket.png", html_name="ticket.html", css_name="style.css"):
    html = render_ticket(keys_dict, html_name, css_name)
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    output_path = os.path.join(parent_dir, "tmp", output_file)
    css_path = os.path.join(parent_dir, "templates", css_name)

    # open the html file
    await page.setContent(html + "<style>" + css_path + "</style>")
    # await page.goto("file://" + os.path.join(parent_dir, "/templates/", html_name))
    await page.addStyleTag({"path": css_path})
    # wait until the page is loaded
    # await page.waitForNavigation()
    await page.waitFor(2000)
    # get the bounding box of the ticket

    # Select the div element with class "ticket"
    div_element = await page.querySelector('.ticket')
    # select the body element
    # div_element = await page.querySelector('body')
    # select all div elements
    screenshot = None
    if div_element:
        # Get the bounding box of the div element
        bounding_box = await div_element.boundingBox()
        if bounding_box:
            # Capture a screenshot of the div element
            screenshot = await page.screenshot(clip=bounding_box, path=output_path, type="png")

    return screenshot

# ! TODO make this work for multiple tickets and improve the efficiency


async def render_tickets_png(keys_dict_arr, html_name="ticket.html", css_name="style.css"):
    '''Renders a ticket png file with the given keys_dict, html and style should be saved in templates file for use'''

    # Create a new browser instance
    print("Creating a new browser instance")
    browser = await launch({'headless': True, 'args': ['--no-sandbox']})
    print("Creating a new page")
    page = await browser.newPage()

    # Configure page options
    await page.setViewport({"width": 1920, "height": 1080})
    await page.setExtraHTTPHeaders({"Accept-Language": "en-US,en"})

    # Allow access to local files
    # await page._client.send("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": "/tmp"})
    page.on('console', lambda msg: print('PAGE LOG:', msg.text))

    output_path = ""
    for ticket in keys_dict_arr:
        print("Rendering ticket for: ", ticket["ticket_id"])
        output_path = await ticket_png_operation(page, ticket, ticket["output_file"], html_name, css_name)

    await browser.close()
    await close_browser(browser)
    # await browser.disconnect()

    return output_path


async def close_browser(browser):
    process_browser = browser.process
    if process_browser and process_browser.pid:
        process_browser.kill()
        process_browser.wait()
    pass
