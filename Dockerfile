FROM alpine

RUN apk add --no-cache bash python3 py3-pip sqlite
RUN pip3 install b2 --upgrade --ignore-installed --break-system-packages

ADD backup.sh /

ENTRYPOINT [ "/backup.sh" ]