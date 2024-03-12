# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
# Since we will be resolving every region, it's worth not cluttering up the
# logs with all that data.
import logging


# Leaving the logger enabled would pollute the logs too much for boto,
# so here we disable them by default.
_endpoint_logger = logging.getLogger('boto.vendored.regions.regions')
_endpoint_logger.disabled = True
