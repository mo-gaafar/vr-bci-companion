import os
from fastapi import Request
from fastapi import FastAPI, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from config import VERSION
from config import conf, root_prefix


from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


from fastapi.staticfiles import StaticFiles
tags_metadata = [
    {
        "name": "usage guide",
        "description": "Guide to use the API, and specific workflows for adding units, etc.",
    },
    {
        "name": "auth",
        "description": "Operations with users and authentication. The **login** logic is also here.",
    },
    {
        "name": "units",
        "description": "Operations related to units. Open to all users and none users."
    },
    {
        "name": "customer",
        "description": "Operations done by customer user."
    },
    {
        "name": "owner",
        "description": "Operations done by owner user. Includes operations like adding units, adding images, etc."
    },
    {
        "name": "admin",
        "description": "Operations done by admin user. This is a **superuser** who can do anything.",
    },
]

app = FastAPI(docs_url=None, redoc_url=None, version=VERSION,
              description="<h2> This is the backend for a property rental application.</h2> <br> <br> The API is built using FastAPI and MongoDB, Hosted on Heroku. <br> API documentation is built automatically using Swagger and ReDoc. <br> <br> Built for Illusionaire", title="Picnic Backend API", favicon="static/favicon.ico", openapi_tags=tags_metadata)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# app.include_router(, prefix=root_prefix)


@app.get(f"{root_prefix}/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,  # type: ignore
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/detailed-guide", tags=["usage guide"])
async def serve_guide():
    # calls serve_markdown with the default file name and then redirects to it
    return RedirectResponse(url=f"{root_prefix}/docs/guide/home", status_code=302)


# type: ignore
@app.get(app.swagger_ui_oauth2_redirect_url,  # type: ignore
         include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(openapi_url=app.openapi_url,  # type: ignore
                          title=app.title + " - ReDoc",
                          redoc_js_url="/static/redoc.standalone.js")


@app.get("/", response_class=HTMLResponse)
async def root():
    '''Contains webpage with html content'''
    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>Picnic App Backend API</title>
    <link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'> \
    <script src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js'></script> \
    <script src='https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js'></script> \
    <script src='https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js'></script>
    </head>
    <body>
    <h1>Picnic App Backend API</h1>
    <p> This is the backend API for a Picnic App Backend. </p>
    <p> The API is built using <a href='https://fastapi.tiangolo.com/'>FastAPI</a> and \
    <a href='https://www.mongodb.com/'>MongoDB</a>. </p>
    <p> Hosted on <a href='https://www.heroku.com/'>Heroku</a>. </p>
    <p> API documentation is built automatically using <a href='https://swagger.io/'>Swagger</a> 
    and <a href='https://redoc.ly/'>ReDoc</a>. </p>
    <p> Built for Illusionaire </p>

    <div>
    <h2>API Documentation</h2>
    <ul>
    <li><a href="/docs">Swagger UI</a></li>
    <li><a href="/redoc">ReDoc</a></li>
    </ul>
    </div>
    </body>
    </html>"""
    return html


# def delete_tmp_files():
#     if not os.path.exists('tmp'):
#         os.mkdir('tmp')
#     for file in os.listdir('tmp'):
#         os.remove(os.path.join('tmp', file))
#     print("Deleted all files in tmp folder")


# delete_tmp_files()


if __name__ == '__main__':

    uvicorn.run(app, host=conf["SERVER_DOMAIN"],  # type: ignore
                port=int(conf["PORT"]), log_level='info')
