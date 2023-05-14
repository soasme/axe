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
            f'You should respond with `{self.true_value}` '
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
            f'You should respond with a list of {self.separator_name} separated '
            f'values, such as `one{self.separator} two{self.separator} three`.'
        )

    def parse(self, text: str) -> List[str]:
        return text.strip().split(f'{self.separator} ')

@dataclass
class CombineParser:

    parsers: List[Parser]

    def prompt(self) -> str:
        nth = defaultdict(lambda: 'th')
        nth[1] = 'st'
        nth[2] = 'nd'
        return '\n'.join([
            f'For the {i+1}{nth[i+1]} output: {p.prompt()}\n'
            f'Then produce two newline characters.'
            for i, p in enumerate(self.parsers)
        ])
