from dataclasses import dataclass
from collections import defaultdict
from typing import List, Any

class Parser:

    def prompt(self) -> str:
        raise NotImplementedError

    def parse(self, text: str) -> Any:
        raise NotImplementedError

@dataclass
class BooleanParser(Parser):

    true_value: str = 'yes'
    false_value: str = 'no'

    def prompt(self) -> str:
        return (
            f'Print `{self.true_value}` '
            f'or `{self.false_value}`.'
        )

    def parse(self, text: str) -> bool:
        if text.lower() == self.true_value:
            return True
        elif text.lower() == self.false_value:
            return False
        else:
            raise ValueError(f'Invalid boolean value: {text.strip()}')

@dataclass
class SeparatedListParser:

    separator_name: str = 'comma'
    separator: str = ','

    def prompt(self) -> str:
        return (
            f'Print a list of values joined by {self.separator_name}, '
            f'such as `one{self.separator} two{self.separator} three`.'
        )

    def parse(self, text: str) -> List[str]:
        return text.strip().split(f'{self.separator} ')

@dataclass
class CombineParser:

    parsers: List[Parser]

    def prompt(self) -> str:
        return '\n'.join([
            f'{i+1}. {p.prompt()} '
            f'Then print two newline characters.\n'
            for i, p in enumerate(self.parsers)
        ])
