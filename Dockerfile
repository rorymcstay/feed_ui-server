FROM nickgryg/alpine-pandas:latest

RUN mkdir -p /home

WORKDIR /home


ADD ./requirements.txt /home/requirements.txt


RUN apk update
RUN apk add --virtual build-deps gcc python3-dev musl-dev
RUN apk add postgresql-dev
RUN pip install --upgrade pip
# Installing packages
RUN pip install -r requirements.txt
RUN apk del build-deps

# Copying over necessary files
COPY src /home/src
COPY settings.py ./settings.py
COPY ui-server.py ./app.py



######################
# environment variables file for image template
ENV LEADER_ENV_FILE=src/config/deployment.env
RUN mkdir -p /home/src/config
RUN touch /home/src/config/deployment.env


# Entrypoint
CMD ["python", "./app.py" ]
