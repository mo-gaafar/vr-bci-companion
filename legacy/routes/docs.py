import markdown
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse


docs = APIRouter(prefix="/docs", tags=["docs"])


def render_markdown(file_path):
    with open(file_path, "r") as md_file:
        md_content = md_file.read()
        html_content = markdown.markdown(md_content)
        return html_content


@docs.get("/guide/{file_name}", response_class=HTMLResponse)
async def serve_markdown(file_name: str):
    file_path = f"docs/{file_name}.md"  # Change the path accordingly
    html_content = render_markdown(file_path)
    # add bootstrap css
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>Picnic App Backend API</title>
    <link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'>
    </head>
    <body>
    <div class="container">
    {html_content}
    </div>
    </body>
    </html>
    """
    # make it a dark theme
    html_content = html_content.replace(
        "<body>", '<body class="bg-dark text-light">')
    # add a back to home button at the end in the footer but center it below the content
    html_content = html_content.replace(
        "</body>", '<div class="text-center"><a href="/"><button class="btn btn-primary">Back to Home</button></a></div></body>')
    return HTMLResponse(content=html_content)


