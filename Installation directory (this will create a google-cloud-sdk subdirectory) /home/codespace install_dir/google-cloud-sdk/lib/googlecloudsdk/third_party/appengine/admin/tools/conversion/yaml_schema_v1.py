# Copyright 2016 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Definition for conversion between legacy YAML and the API JSON formats."""

from __future__ import absolute_import
from googlecloudsdk.third_party.appengine.admin.tools.conversion import converters as c
from googlecloudsdk.third_party.appengine.admin.tools.conversion import schema as s

SCHEMA = s.Message(
    api_config=s.Message(
        url=s.Value(converter=c.ToJsonString),
        login=s.Value(converter=c.EnumConverter('LOGIN')),
        secure=s.Value('security_level', converter=c.EnumConverter('SECURE')),
        auth_fail_action=s.Value(converter=c.EnumConverter('AUTH_FAIL_ACTION')),
        script=s.Value(converter=c.ToJsonString)),
    api_version=s.Value('runtime_api_version', converter=c.ToJsonString),
    app_engine_apis=s.Value(),
    auto_id_policy=s.Value('beta_settings',
                           lambda val: {'auto_id_policy': val}),
    automatic_scaling=s.Message(
        converter=c.ConvertAutomaticScaling,
        cool_down_period_sec=s.Value(
            'cool_down_period', converter=c.SecondsToDuration),
        cpu_utilization=s.Message(
            target_utilization=s.Value(),
            aggregation_window_length_sec=s.Value(
                'aggregation_window_length', converter=c.SecondsToDuration)),
        max_instances=s.Value('max_instances'),
        min_instances=s.Value('min_instances'),
        target_cpu_utilization=s.Value('target_cpu_utilization'),
        target_throughput_utilization=s.Value('target_throughput_utilization'),
        max_num_instances=s.Value('max_total_instances'),
        min_pending_latency=s.Value(converter=c.LatencyToDuration),
        min_idle_instances=s.Value(
            converter=c.StringToInt(handle_automatic=True)),
        max_idle_instances=s.Value(
            converter=c.StringToInt(handle_automatic=True)),
        max_pending_latency=s.Value(converter=c.LatencyToDuration),
        max_concurrent_requests=s.Value(converter=c.StringToInt()),
        min_num_instances=s.Value('min_total_instances'),
        target_network_sent_bytes_per_sec=s.Value(
            'target_sent_bytes_per_second'),
        target_network_sent_packets_per_sec=s.Value(
            'target_sent_packets_per_second'),
        target_network_received_bytes_per_sec=s.Value(
            'target_received_bytes_per_second'),
        target_network_received_packets_per_sec=s.Value(
            'target_received_packets_per_second'),
        target_disk_write_bytes_per_sec=s.Value(
            'target_write_bytes_per_second'),
        target_disk_write_ops_per_sec=s.Value('target_write_ops_per_second'),
        target_disk_read_bytes_per_sec=s.Value('target_read_bytes_per_second'),
        target_disk_read_ops_per_sec=s.Value('target_read_ops_per_second'),
        target_request_count_per_sec=s.Value('target_request_count_per_second'),
        target_concurrent_requests=s.Value()),
    basic_scaling=s.Message(
        idle_timeout=s.Value(converter=c.IdleTimeoutToDuration),
        max_instances=s.Value(converter=c.StringToInt())),
    beta_settings=s.Map(),
    default_expiration=s.Value(converter=c.ExpirationToDuration),
    endpoints_api_service=s.Message(
        name=s.Value(),
        rollout_strategy=s.Value(
            converter=c.ConvertEndpointsRolloutStrategyToEnum),
        config_id=s.Value(),
        trace_sampling=s.Value('disable_trace_sampling', converter=c.Not),
    ),
    entrypoint=s.Value(converter=c.ConvertEntrypoint),
    env=s.Value(),
    env_variables=s.Map(),
    build_env_variables=s.Map(),
    error_handlers=s.RepeatedField(
        element=s.Message(
            error_code=s.Value(converter=c.EnumConverter('ERROR_CODE')),
            file=s.Value('static_file', converter=c.ToJsonString),
            mime_type=s.Value(converter=c.ToJsonString))),
    runtime_config=s.Message('flexible_runtime_settings',
        operating_system=s.Value(converter=c.ToJsonString),
        runtime_version=s.Value(converter=c.ToJsonString),
    ),
    # Restructure the handler after it's complete, since this is more
    # complicated than a simple rename.
    handlers=s.RepeatedField(
        element=s.Message(
            converter=c.ConvertUrlHandler,
            auth_fail_action=s.Value(
                converter=c.EnumConverter('AUTH_FAIL_ACTION')),
            static_dir=s.Value(converter=c.ToJsonString),
            secure=s.Value(
                'security_level', converter=c.EnumConverter('SECURE')),
            redirect_http_response_code=s.Value(
                converter=c.EnumConverter('REDIRECT_HTTP_RESPONSE_CODE')),
            http_headers=s.Map(),
            url=s.Value('url_regex'),
            expiration=s.Value(converter=c.ExpirationToDuration),
            static_files=s.Value('path', converter=c.ToJsonString),
            script=s.Value('script_path', converter=c.ToJsonString),
            upload=s.Value('upload_path_regex', converter=c.ToJsonString),
            api_endpoint=s.Value(),
            application_readable=s.Value(),
            position=s.Value(),
            login=s.Value(converter=c.EnumConverter('LOGIN')),
            mime_type=s.Value(converter=c.ToJsonString),
            require_matching_file=s.Value())),
    health_check=s.Message(
        check_interval_sec=s.Value(
            'check_interval', converter=c.SecondsToDuration),
        timeout_sec=s.Value('timeout', converter=c.SecondsToDuration),
        healthy_threshold=s.Value(),
        enable_health_check=s.Value('disable_health_check', converter=c.Not),
        unhealthy_threshold=s.Value(),
        host=s.Value(converter=c.ToJsonString),
        restart_threshold=s.Value()),
    liveness_check=s.Message(
        check_interval_sec=s.Value(
            'check_interval', converter=c.SecondsToDuration),
        timeout_sec=s.Value('timeout', converter=c.SecondsToDuration),
        initial_delay_sec=s.Value(
            'initial_delay', converter=c.SecondsToDuration),
        success_threshold=s.Value(),
        failure_threshold=s.Value(),
        path=s.Value(),
        host=s.Value(converter=c.ToJsonString)),
    readiness_check=s.Message(
        check_interval_sec=s.Value(
            'check_interval', converter=c.SecondsToDuration),
        timeout_sec=s.Value('timeout', converter=c.SecondsToDuration),
        app_start_timeout_sec=s.Value(
            'app_start_timeout', converter=c.SecondsToDuration),
        success_threshold=s.Value(),
        failure_threshold=s.Value(),
        path=s.Value(),
        host=s.Value(converter=c.ToJsonString)),
    inbound_services=s.RepeatedField(
        element=s.Value(converter=c.EnumConverter('INBOUND_SERVICE'))),
    instance_class=s.Value(converter=c.ToJsonString),
    libraries=s.RepeatedField(
        element=s.Message(
            version=s.Value(converter=c.ToJsonString),
            name=s.Value(converter=c.ToJsonString))),
    main=s.Value('runtime_main_executable_path', converter=c.ToJsonString),
    manual_scaling=s.Message(instances=s.Value(converter=c.StringToInt())),
    network=s.Message(
        instance_tag=s.Value(converter=c.ToJsonString),
        name=s.Value(converter=c.ToJsonString),
        subnetwork_name=s.Value(converter=c.ToJsonString),
        forwarded_ports=s.RepeatedField(
            element=s.Value(converter=c.ToJsonString)),
        session_affinity=s.Value(),
        instance_ip_mode=s.Value(converter=c.ToJsonString)),
    nobuild_files=s.Value('nobuild_files_regex', converter=c.ToJsonString),
    resources=s.Message(
        memory_gb=s.Value(),
        disk_size_gb=s.Value('disk_gb'),
        cpu=s.Value(),
        volumes=s.RepeatedField(
            element=s.Message(
                name=s.Value(converter=c.ToJsonString),
                volume_type=s.Value(converter=c.ToJsonString),
                size_gb=s.Value()))),
    runtime=s.Value(converter=c.ToJsonString),
    runtime_channel=s.Value(converter=c.ToJsonString),
    service_account=s.Value(converter=c.ToJsonString),
    standard_websocket=s.Value('enable_standard_websocket'),
    threadsafe=s.Value(),
    version=s.Value('id', converter=c.ToJsonString),
    vm=s.Value(),
    vm_settings=s.Map('beta_settings'),
    vpc_access_connector=s.Message(
        name=s.Value(converter=c.ToJsonString),
        egress_setting=s.Value(converter=c.ToVpcEgressSettingEnum)))
