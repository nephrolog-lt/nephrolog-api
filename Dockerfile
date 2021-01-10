FROM python:3.9
EXPOSE 8080

ENV PYTHONUNBUFFERED 1

RUN mkdir /srv/nephrolog-api
WORKDIR /srv/nephrolog-api

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/bin/sh", "start.sh"]