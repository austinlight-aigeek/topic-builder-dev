FROM python:3.12
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip freeze

WORKDIR /code/app
COPY . /code/app
CMD ["python", "app.py"]