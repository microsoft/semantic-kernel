# Dockerfile extending the generic Go image with application files for a
# single application.
FROM gcr.io/google-appengine/golang

COPY . /go/src/app
RUN go-wrapper install -tags appenginevm
