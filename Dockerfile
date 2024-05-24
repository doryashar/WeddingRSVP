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

CMD ["fastapi_serve.py"] #uvicorn fastapi_serve:api --reload