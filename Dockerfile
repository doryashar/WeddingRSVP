# start by pulling the python image
FROM python:3.10-alpine

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
# RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /app

EXPOSE 80

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
# ["app.py"] 
#gunicorn main:app --workers 4 --worker-class 