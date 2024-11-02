# Multi-service ECS example

This repo' demonstrates how to deploy multiple services (each a different container) to an AWS ECS cluster
such that the containers can communicate.  The first container, a proxy, relays incoming http
requests to a second container which returns a canned response.

The proxy container is created on the fly using the Dockerfile in this repo', configured by the
`proxy.conf` file to forward incoming requests, on port 8080, to the second service on port 80.
The second service is the Docker container `httpd` which is is run in its default configuration,
returning a canned response when receiving a GET requrst to the `/` URI.

