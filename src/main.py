from auth.routes import auth
from patient.routes import router as patient
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
        "name": "patient",
        "description": "Operations with patients. This includes **CRUD** operations for patients and their exercise records.",
    },
    {
        "name": "admin",
        "description": "Operations done by admin user. This is a **superuser** who can do anything.",
    },
]


app = FastAPI(docs_url=None, redoc_url=None, version=VERSION,
              description="<h2> This is the backend for the virtual reality post-stroke rehabilitation game.</h2> <br> <br> The API is built using FastAPI and MongoDB, Hosted on Heroku. <br> API documentation is built automatically using Swagger and ReDoc. <br> <br> Built in Cairo University, Egypt", title="VR/BCI Backend API", favicon="static/favicon.ico", openapi_tags=tags_metadata)

origins = ['*']
app.openapi_version = "3.0.2"  # Or a different OpenAPI 3.0.x version

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")
# app.include_router(, prefix=root_prefix)
app.include_router(patient, prefix=root_prefix, tags=["patient"])
app.include_router(auth, prefix=root_prefix, tags=["auth"])


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
    from gui.backend_home import html_content
    html = html_content
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
                port=int(conf["SERVER_PORT"]), log_level='info')
