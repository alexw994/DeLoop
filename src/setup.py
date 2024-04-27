from setuptools import setup, find_packages

setup(
    name='deloop',
    version='0.1.1',
    packages=['deloop', 'deloop.client'],
    install_requires=["pydantic==2.6.0",
                      "requests",
                      "fastapi",
                      "minio",
                      "elasticsearch",
                      "pillow",
                      "opencv-python",
                      "httpx",
                      "datasets"],
    author='alexwww94',
    author_email='puzzlewant@foxmail.com',
    description='Deep Loop For Agile Development',
    long_description=open('../README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/alexwww94/deloop'
)
