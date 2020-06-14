FROM python:3.8.3-slim

RUN mkdir -p /home

WORKDIR /home


ADD ./requirements.txt /home/requirements.txt


#RUN apk update
#RUN apk add --virtual build-deps gcc python3-dev musl-dev
#RUN apk add postgresql-dev

#RUN apk del build-deps

RUN pip install --upgrade pip
# Installing packages
RUN pip install -r requirements.txt

# Copying over necessary files
COPY src /home/src
COPY settings.py ./settings.py
COPY ui-server.py ./app.py

ENV SELECTOR_GADGET="/data/content"

# add selenium static js files
ADD ./selector/selectorgadget_combined.min.js /data/content/selectorgadget_combined.js
ADD ./selector/selectorgadget_combined.css /data/content/selectorgadget_combined.css
ADD ./selector/initialise_gadget.js /data/content/initialise_gadget.js

######################
# environment variables file for image template
ENV LEADER_ENV_FILE=src/config/deployment.env
RUN mkdir -p /home/src/config
RUN touch /home/src/config/deployment.env


# Entrypoint
CMD ["python", "./app.py" ]
