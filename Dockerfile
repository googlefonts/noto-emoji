FROM python:slim

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    make \
    gcc \
    zopfli \
    libc-dev \
    libpng-dev \
    libcairo2-dev \
    imagemagick \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache notofonttools

ADD . /blobmoji
WORKDIR /blobmoji

RUN mkdir /output

CMD make -j $(nproc) && cp NotoColorEmoji.ttf /output/
