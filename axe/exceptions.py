# -*- coding: utf-8 -*-

class GenerativeAIException(Exception):
    """The base class for all GenerativeAI exceptions.
    """

    description: str | None = None

    def __init__(
        self,
        description: str | None = None,
    ) -> None:
        super().__init__()
        self.description = description
