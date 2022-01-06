FROM python:3.9-slim-buster as base

LABEL maintainer="hl@blocksize-capital.com"

RUN apt-get update && apt-get install -y -qq bash apt-transport-https ca-certificates curl iputils-ping net-tools libpq-dev build-essential

RUN pip install --upgrade pip

RUN mkdir -p /workdir
WORKDIR /workdir

# python environment
COPY poetry.lock /workdir/
COPY pyproject.toml /workdir/

# support scripts
COPY install.sh /workdir/
COPY scripts/run.sh /workdir/

# install all python dependencies
RUN bash install.sh

# application
COPY src/ /workdir/src/
COPY .env /workdir/

FROM base
#EXPOSE 5555

CMD ["bash", "/workdir/run.sh"]
