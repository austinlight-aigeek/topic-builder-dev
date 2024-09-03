FROM 687690056036.dkr.ecr.us-west-2.amazonaws.com/wgu/base/python3.11:latest
COPY ./src/app/requirements.txt /code/requirements.txt
USER root
WORKDIR /code/app

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN pip freeze
RUN mkdir -p /home/wguuser
RUN chown -R wguuser:wguuser /home/wguuser
USER wguuser
WORKDIR /code/app
COPY ./src/app/ /code/app

CMD ["python", "app.py"]
