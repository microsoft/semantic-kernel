# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.oauth2 import service_account


class ConstructableFromServiceAccount:
    @classmethod
    def from_service_account_file(cls, filename, **kwargs):
        f"""Creates an instance of this client using the provided credentials file.
        Args:
            filename (str): The path to the service account private key json
                file.
            kwargs: Additional arguments to pass to the constructor.
        Returns:
            A {cls.__name__}.
        """
        credentials = service_account.Credentials.from_service_account_file(filename)
        return cls(credentials=credentials, **kwargs)

    from_service_account_json = from_service_account_file
