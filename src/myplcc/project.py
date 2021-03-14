from dataclasses import dataclass, field
from typing import List, Optional, Dict
from collections import defaultdict
import itertools
import os
import re

@dataclass(eq = False)
class GeneratedClass:
    project: 'Project'
    name: str
    package: List[str] = field(init=False)
    class_name: str = field(init=False)
    special: Optional[object] = field(default=None)
    extra_code: Dict[Optional[str], List[str]] = field(default_factory=lambda: defaultdict(lambda: list()))

    def __post_init__(self):
        parts = self.name.split('.')
        self.package = parts[:-1]
        self.class_name = parts[-1]

    def import_(self, package):
        if package != self.package:
            yield 'import {};'.format(self.name)

@dataclass(eq = False)
class Project:
    classes: Dict[str, GeneratedClass] = field(default_factory=dict)
    extra_code: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(lambda: list()))

    def add(self, name, special = None):
        if name in self.classes:
            raise RuntimeError('TODO: duplicate class: ' + name)
        cls = GeneratedClass(self, name, special)
        if special is not None:
            special.generated_class = cls
        self.classes[name] = cls
        return cls

    def ensure(self, name, typ, make):
        if name in self.classes:
            cls = self.classes[name]
            assert isinstance(cls.special, typ) # TODO
            return cls
        else:
            return self.add(name, special = make())

    def generate_extra_code(self, cls):
        def gen(name, indent):
            yield '{}//::PLCC::{}'.format(indent, name if name else '')
            for line in itertools.chain(self.extra_code[name], cls.extra_code[name]):
                match = re.match('^(\s*)//::PLCC::(\w+)?$', line)
                if match:
                    yield from gen(match.group(2), indent + match.group(1))
                else:
                    yield line.format(indent)
        return gen

    def generate_code(self, out_path):
        for cls in self.classes.values():
            gen_extra = self.generate_extra_code(cls)
            if cls.special:
                gen = cls.special.generate_code(gen_extra)
            else:
                gen = gen_extra(None, '')
            path = os.path.normpath(out_path)
            try:
                os.mkdir(path)
            except FileExistsError:
                pass
            for part in cls.package:
                path += '/' + part
                try:
                    os.mkdir(path)
                except FileExistsError:
                    pass
            path += '/{}.java'.format(cls.class_name)
            with open(path, 'w') as f:
                for line in gen:
                    print(line, file = f)

def package_prefix(package):
    return ''.join(part + '.' for part in package)
