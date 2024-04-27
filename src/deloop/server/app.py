import os
import sys
from pathlib import Path

FILE = Path(__file__).parent
if str(FILE) not in sys.path:
    sys.path.append(str(FILE))

# os.environ.setdefault('MINIO_HOST_PORT', '10.39.88.175:9000')
# os.environ.setdefault('DELOOP_HOST_PORT', '0.0.0.0:6006')
# os.environ.setdefault('ES_PROTOCOL_HOST_PORT', 'http://10.39.88.175:9200')
# os.environ.setdefault('LABELTSTUDIO_HOST_PORT', 'http://10.39.88.175:8080')

from resources.image import router as image_router
from resources.al_backend import router as al_backend_router
from resources.aps import router as aps_router
from resources.ls import router as ls_router
from resources.dataset import router as dataset_router
from resources.record import router as record_router
from resources.project import router as project_router
from resources.auth import router as auth_router
from resources import DELOOP_HOST_PORT

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title='Deloop Server')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(image_router)
app.include_router(al_backend_router)
app.include_router(aps_router)
app.include_router(ls_router)
app.include_router(dataset_router)
app.include_router(record_router)
app.include_router(project_router)
app.include_router(auth_router)

if __name__ == '__main__':
    host, port = DELOOP_HOST_PORT.split(':')
    uvicorn.run(app, host=host, port=int(port))
