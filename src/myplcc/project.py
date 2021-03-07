from dataclasses import dataclass, field
from typing import List, Optional, Dict
from collections import defaultdict

@dataclass(eq = False)
class GeneratedClass:
    name: str
    package: List[str]
    class_name: str
    special: Optional[object] = field(default=None)
    extra_code: Dict[Optional[str], List[str]] = field(default_factory=lambda: defaultdict(lambda: list()))

    def import_(self, package):
        if package != self.package:
            yield 'import {};'.format(self.name)

@dataclass(eq = False)
class Project:
    classes: Dict[str, GeneratedClass] = field(default_factory=dict)
    extra_code: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(lambda: list()))
    compat_terminals: bool = field(default=False)
    compat_extra_code_indent: bool = field(default=False)

    def add(self, name, special = None):
        if name in self.classes:
            raise RuntimeError('TODO: duplicate class: ' + class_name)
        parts = name.split('.')
        package = parts[:-1]
        class_name = parts[-1]
        cls = GeneratedClass(name, package, class_name, special)
        if special is not None:
            special.generated_class = cls
        self.classes[class_name] = cls
        return cls

    def ensure(self, name, typ, make):
        if name in self.classes:
            cls = self.classes[name]
            assert isinstance(cls.special, typ) # TODO
            return cls
        else:
            return self.add(name, special = make())