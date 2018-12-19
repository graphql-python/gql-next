import os

SPACES = ' ' * 4


class CodeGenerator:
    def __init__(self):
        self.lines = []
        self.level = 0

    def indent(self):
        self.level += 1

    def undent(self):
        if self.level > 0:
            self.level -= 1

    @property
    def indent_string(self):
        return self.level * SPACES

    def write(self, value: str, *args, **kwargs):
        value = self.indent_string + value
        if args or kwargs:
            value = value.format(*args, **kwargs)

        self.lines.append(value)

    def write_lines(self, lines):
        for line in lines:
            self.lines.append(self.indent_string + line)

    def __add__(self, value: str):
        self.write(value)

    def __str__(self):
        return os.linesep.join(self.lines)
