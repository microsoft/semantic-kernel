# Based from: https://github.com/dapr/python-sdk/tree/main/examples/pubsub-simple
# ====================================================================================
# SETUP:
# 1. [Optional] Create python virtual environment and activate
# 2. Install dependencies: python -m pip install -r ./requirements.txt
# USAGE:
# To run use:
# dapr run --app-id python-subscriber --app-protocol grpc --app-port 50051 python subscriber.py
# To stop app use:
# dapr stop --app-id python-subscriber
# For testing (from a separate terminal):
# dapr publish --publish-app-id python-subscriber --pubsub pubsub --topic someotherkickofftopicname --data '{"orderId": "100"}'
# dapr publish --publish-app-id python-subscriber --pubsub pubsub --topic sharedeventtopic --data '{"id": "100", "message": "test"}'
# ====================================================================================

from datetime import datetime, timezone
from time import sleep
from cloudevents.sdk.event import v1
from dapr.ext.grpc import App
from dapr.clients.grpc._response import TopicEventResponse
from dapr.proto import appcallback_v1

import json

PUBSUB_NAME = "pubsub"
SUB_TOPIC_1 = "someotherkickofftopicname"
SUB_TOPIC_2 = "OnStepACompleted"
SUB_TOPIC_3 = "OnStepBCompleted"
SUB_TOPIC_4 = "sharedeventtopic"

app = App()
should_retry = False  # To control whether dapr should retry sending a message

def get_timestamp():
    tz = timezone.utc
    ft = "%Y-%m-%dT%H:%M:%SZ"
    return datetime.now(tz=tz).strftime(ft)

def process_message(event: v1.Event, topic_name: str):
    data = json.loads(event.Data())
    print(
        f'{get_timestamp()} - Subscriber TOPIC {topic_name} received: {data}", '
        f'content_type="{event.content_type}"',
        flush=True,
    )

@app.subscribe(pubsub_name=PUBSUB_NAME, topic=SUB_TOPIC_1)
def on_topic_1(event: v1.Event) -> TopicEventResponse:
    global should_retry
    process_message(event, SUB_TOPIC_1)
    # event.Metadata() contains a dictionary of cloud event extensions and publish metadata
    if should_retry:
        should_retry = False  # we only retry once in this example
        sleep(0.5)  # add some delay to help with ordering of expected logs
        return TopicEventResponse('retry')
    return TopicEventResponse('success')

@app.subscribe(pubsub_name=PUBSUB_NAME, topic=SUB_TOPIC_2)
def on_topic_2(event: v1.Event) -> TopicEventResponse:
    global should_retry
    process_message(event, SUB_TOPIC_2)
    # event.Metadata() contains a dictionary of cloud event extensions and publish metadata
    if should_retry:
        should_retry = False  # we only retry once in this example
        sleep(0.5)  # add some delay to help with ordering of expected logs
        return TopicEventResponse('retry')
    return TopicEventResponse('success')

@app.subscribe(pubsub_name=PUBSUB_NAME, topic=SUB_TOPIC_3)
def on_topic_3(event: v1.Event) -> TopicEventResponse:
    global should_retry
    process_message(event, SUB_TOPIC_3)
    # event.Metadata() contains a dictionary of cloud event extensions and publish metadata
    if should_retry:
        should_retry = False  # we only retry once in this example
        sleep(0.5)  # add some delay to help with ordering of expected logs
        return TopicEventResponse('retry')
    return TopicEventResponse('success')


@app.subscribe(pubsub_name=PUBSUB_NAME, topic=SUB_TOPIC_4)
def on_topic_4(event: v1.Event) -> TopicEventResponse:
    global should_retry
    process_message(event, SUB_TOPIC_4)
    # event.Metadata() contains a dictionary of cloud event extensions and publish metadata
    if should_retry:
        should_retry = False  # we only retry once in this example
        sleep(0.5)  # add some delay to help with ordering of expected logs
        return TopicEventResponse('retry')
    return TopicEventResponse('success')

# == for testing with Redis only ==
# workaround as redis pubsub does not support wildcards
# we manually register the distinct topics
for id in range(4, 7):
    app._servicer._registered_topics.append(
        appcallback_v1.TopicSubscription(pubsub_name=PUBSUB_NAME, topic=f'topic/{id}')
    )
# =================================


# this allows subscribing to all events sent to this app - useful for wildcard topics
@app.subscribe(pubsub_name=PUBSUB_NAME, topic='topic/#', disable_topic_validation=True)
def mytopic_wildcard(event: v1.Event) -> TopicEventResponse:
    data = json.loads(event.Data())
    print(
        f'Wildcard-Subscriber received: id={data["id"]}, message="{data["message"]}", '
        f'content_type="{event.content_type}"',
        flush=True,
    )
    return TopicEventResponse('success')


# Example of an unhealthy status
# def unhealthy():
#     raise ValueError("Not healthy")
# app.register_health_check(unhealthy)

app.register_health_check(lambda: print('Healthy'))

app.run(50051)
