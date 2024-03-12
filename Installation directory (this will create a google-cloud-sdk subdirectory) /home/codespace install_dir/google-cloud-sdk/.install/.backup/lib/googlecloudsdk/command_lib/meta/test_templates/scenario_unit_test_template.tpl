title: compute images get-iam-policy scenario test
release_tracks: [ALPHA, BETA, GA]
summary:
# This summary is generated automatically on update and should not be edited.
- execute:
  - command: compute images get-iam-policy my-image
  - stdout: |
      etag: etag
- execute:
  - command: compute images get-iam-policy my-image
  - stdout: |
      bindings:
      - condition:
          description: descr
          expression: expr
          title: title
        members:
        - user:oldtest@gmail.com
        role: roles/non-primitive
      etag: etag
      version: 1
- execute:
  - command: compute images get-iam-policy my-image --flatten=bindings[].members --filter=bindings.role:non-primitive
      --format='value(bindings.members)'
  - stdout: |
      user:oldtest@gmail.com
actions:
- define_reference:
    reference: api-version
    track_values:
      GA: v1
      BETA: beta
      ALPHA: alpha

- define_reference:
    reference: query-params
    value: alt=json&optionsRequestedPolicyVersion=3

- execute_command:
    command: compute images get-iam-policy my-image
    events:
    - api_call:
        expect_request:
          uri: https://compute.googleapis.com/compute/$$api-version$$/projects/fake-project/global/images/my-image/getIamPolicy?$$query-params$$
          method: GET
          body: null
        return_response:
          headers:
            status: '200'
          body: |-
            {
              "etag": "etag",
              "bindings": []
            }
    - expect_stdout: |
        etag: etag
    - expect_exit:
        code: 0

- execute_command:
    command: compute images get-iam-policy my-image
    events:
    - api_call:
        expect_request:
          uri: https://compute.googleapis.com/compute/$$api-version$$/projects/fake-project/global/images/my-image/getIamPolicy?$$query-params$$
          method: GET
          body: null
        return_response:
          headers:
            status: '200'
          body: |-
            {
              "version": 1,
              "etag": "etag",
              "bindings": [
                {
                  "role": "roles/non-primitive",
                  "members": ["user:oldtest@gmail.com"],
                  "condition": {
                    "expression": "expr",
                    "title": "title",
                    "description": "descr"
                  }
                }
              ]
            }
    - expect_stdout: |
        bindings:
        - condition:
            description: descr
            expression: expr
            title: title
          members:
          - user:oldtest@gmail.com
          role: roles/non-primitive
        etag: etag
        version: 1
    - expect_exit:
        code: 0

- execute_command:
    command: compute images get-iam-policy my-image --flatten=bindings[].members --filter=bindings.role:non-primitive
      --format='value(bindings.members)'
    events:
    - api_call:
        expect_request:
          uri: https://compute.googleapis.com/compute/$$api-version$$/projects/fake-project/global/images/my-image/getIamPolicy?$$query-params$$
          method: GET
          body: null
        return_response:
          headers:
            status: '200'
          body: |-
            {
              "version": 1,
              "etag": "etag",
              "bindings": [
                {
                  "role": "roles/non-primitive",
                  "members": ["user:oldtest@gmail.com"],
                  "condition": {
                    "expression": "expr",
                    "title": "title",
                    "description": "descr"
                  }
                }
              ]
            }
    - expect_stdout: |
        user:oldtest@gmail.com
    - expect_exit:
        code: 0
