FROM python:3.10

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
        libatlas-base-dev gfortran nginx supervisor nfs-common

RUN pip3 install uwsgi

COPY ./requirements.txt /opt/grubstack-api/requirements.txt

RUN pip3 install -r /opt/grubstack-api/requirements.txt

RUN useradd --no-create-home nginx

RUN rm /etc/nginx/sites-enabled/default
RUN rm -r /root/.cache

COPY nginx.conf /etc/nginx/
COPY nginx-backend.conf /etc/nginx/conf.d/
COPY uwsgi.ini /etc/uwsgi/
COPY supervisord.conf /etc/

COPY grubstack/grubstack.ini.sample /opt/grubstack-api/grubstack/grubstack.ini
COPY main.py /opt/grubstack-api/
COPY grubstack /opt/grubstack-api/grubstack

WORKDIR /opt/grubstack-api

CMD ["/usr/bin/supervisord"]