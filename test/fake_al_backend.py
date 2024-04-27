import sys
from pathlib import Path

ROOT = Path(__file__).parents[1] / 'src'
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
from deloop.client.tools import create_server

test_al_backend_host = '127.0.0.1'
test_al_backend_url = '/test_al_backend'
test_al_backend_port = 6007


@create_server(test_al_backend_host, test_al_backend_port, test_al_backend_url)
def infer(image):
    return [
        {
            "name": "example_name",
            "class": 42,
            "confidence": 0.87,
            "box": {
                "x1": 10.5,
                "y1": 20.3,
                "x2": 30.8,
                "y2": 40.2
            }
        }
    ]


def create():
    infer()
