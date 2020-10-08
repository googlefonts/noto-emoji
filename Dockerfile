FROM python:3.7-slim

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    git \
    zopfli \
    libcairo2-dev \
    make \
    imagemagick \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/googlefonts/nototools.git /nototools
WORKDIR /nototools
RUN pip install --no-cache -r requirements.txt && pip install --no-cache -e .

ADD . /blobmoji
WORKDIR /blobmoji

RUN mkdir /output

CMD make -j $(nproc) && cp NotoColorEmoji.ttf /output/
