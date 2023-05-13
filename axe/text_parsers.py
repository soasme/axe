from dataclasses import dataclass

@dataclass
class BooleanParser:

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
