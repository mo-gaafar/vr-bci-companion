# from fastapi_profiler import PyInstrumentProfilerMiddleware
from fastapi.responses import FileResponse
from pydantic import AnyHttpUrl
# import fastapi_asyncapi
from os import path
import uvicorn
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import CONFIG, ROOT_PREFIX, VERSION
from .api import api_router
from .handlers import validation_exception_handler, http_exception_handler, repository_exception_handler, common_exception_handler
from server.common.exceptions import RepositoryException

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
        "name": "patient",
        "description": "Operations with patients. This includes **CRUD** operations for patients and their exercise records.",
    },
    {
        "name": "admin",
        "description": "Operations done by admin user. This is a **superuser** who can do anything.",
    },
]


app = FastAPI(docs_url=None, redoc_url=None, version=VERSION,
              description="<h2> This is the backend for the virtual reality post-stroke rehabilitation game.</h2> <br> <br> The API is built using FastAPI and MongoDB, Hosted on Heroku. <br> API documentation is built automatically using Swagger and ReDoc. <br> <br> Built in Cairo University, Egypt", title=CONFIG.APP_NAME, favicon="favicon.ico", openapi_tags=tags_metadata)

origins = ['*']
app.openapi_version = "3.0.2"  # Or a different OpenAPI 3.0.x version

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# PERFORMANCE PROFILER MIDDLEWARE

# app.add_middleware(
#     PyInstrumentProfilerMiddleware,
#     server_app=app,
#     profiler_output_type="speedscope",
#     prof_file_name="example_speedscope_profile.json"
# )
# app.add_middleware(
#     PyInstrumentProfilerMiddleware,
#     server_app=app,  # Required to output the profile on server shutdown
#     profiler_output_type="html",
#     is_print_each_request=False,  # Set to True to show request profile on
#                                   # stdout on each request
#     open_in_browser=True,  # Set to true to open your web-browser automatically
#     # when the server shuts down
#     html_file_name="example_profile.html"  # Filename for output
# )


STATIC_DIR = "/server/static"
if STATIC_DIR and path.isdir('.'+STATIC_DIR):
    app.mount("/server/static",
              StaticFiles(directory="."+STATIC_DIR), name="static")
else:
    print("No static directory found")
    print("Current directory: ", path.abspath(path.curdir))
    print("Static directory: ", path.abspath(STATIC_DIR))
    # print all available directories
    # print("Available directories: ", [d for d in path.listdir(path.curdir) if path.isdir(d)])


# ROUTER INCLUDES
app.include_router(api_router, prefix=ROOT_PREFIX)

# EXCEPTION HANDLERS
app.add_exception_handler(RepositoryException, repository_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, common_exception_handler)


@app.get(f"{ROOT_PREFIX}/healthcheck")
def healthcheck():
    return {"status": "ok"}


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,  # type: ignore
        title=app.title + " - Swagger UI",
        swagger_favicon_url="/favicon.ico",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url=STATIC_DIR+"/swagger-ui-bundle.js",
        swagger_css_url=STATIC_DIR+"/swagger-ui.css",
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("server/static/favicon.ico")


@app.get("/detailed-guide", tags=["usage guide"])
def serve_guide():
    # calls serve_markdown with the default file name and then redirects to it
    return RedirectResponse(url=f"{ROOT_PREFIX}/docs/guide/home", status_code=302)


# type: ignore
@app.get(app.swagger_ui_oauth2_redirect_url,  # type: ignore
         include_in_schema=False)
def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
def redoc_html():
    return get_redoc_html(openapi_url=app.openapi_url,  # type: ignore
                          title=app.title + " - ReDoc",
                          redoc_js_url=STATIC_DIR+"/redoc.standalone.js")


@app.get("/", response_class=HTMLResponse)
def root():
    '''Contains webpage with html content'''
    from server.static.backend_home import html_content
    html = html_content
    return html


# def delete_tmp_files():
#     if not os.path.exists('tmp'):
#         os.mkdir('tmp')
#     for file in os.listdir('tmp'):
#         os.remove(os.path.join('tmp', file))
#     print("Deleted all files in tmp folder")


# delete_tmp_files()


# if __name__ == '__main__':

#     uvicorn.run(app, host=CONFIG.SERVER_DOMAIN,  # type: ignore
#                 port=int(CONFIG.PORT), log_level='info')
