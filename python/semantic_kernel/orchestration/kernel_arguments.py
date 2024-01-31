from collections import UserDict
from typing import Any, Dict, List, Optional, Union

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class KernelArguments(UserDict):
    def __init__(
        self, settings: Optional[Union[AIRequestSettings, List[AIRequestSettings]]] = None, **arguments: Dict[str, Any]
    ):
        """Initializes a new instance of the KernelArguments class.

        This class is derived from a dict, hence behaves the same way,
        just adds the execution_settings as a dict, with service_id and the settings.

        Arguments:
            settings {Optional[Union[AIRequestSettings, List[AIRequestSettings]]]} -- The settings for the execution.
                If a list is given, make sure all items in the list have a unique service_id
                as that is used as the key for the dict.
            **arguments {Dict[str, Any]} -- The arguments for the function invocation.
        """
        super().__init__(**arguments)
        settings_dict = None
        if settings:
            if isinstance(settings, list):
                settings_dict = {s.service_id: s for s in settings}
            else:
                settings_dict = {settings.service_id: settings}
        self.execution_settings: Optional[Dict[str, AIRequestSettings]] = settings_dict
