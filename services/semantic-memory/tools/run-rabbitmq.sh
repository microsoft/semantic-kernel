#docker run -d \
#--hostname foobar \
#docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management
docker run -it --rm --name rabbitmq \
  -e RABBITMQ_DEFAULT_USER=user \
  -e RABBITMQ_DEFAULT_PASS=password \
  -p 5672:5672 \
  rabbitmq:3
  
  
