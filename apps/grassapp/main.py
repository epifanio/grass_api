import fastapi
from starlette.middleware.cors import CORSMiddleware
from grassapi import general
import uvicorn
# from views import dashboard


app = fastapi.FastAPI(title="GRASS GIS API",
                      description="Prototype API for GRASS GIS",
                      version="0.0.1",
                      )

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_PROCESSING_SECOND = 600


def configure_routing():
    app.include_router(general.router)
    # app.include_router(dashboard.router)


def configure():
    configure_routing()


if __name__ == '__main__':
    configure()
    uvicorn.run(app, port=9000, host='10.0.0.100')
else:
    configure()
