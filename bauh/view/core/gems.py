import inspect
import os
import pkgutil
from typing import List

from bauh import ROOT_DIR
from bauh.api.abstract.controller import SoftwareManager, ApplicationContext
from bauh.view.core.config import Configuration
from bauh.view.util import util


def find_manager(member):
    if not isinstance(member, str):
        if inspect.isclass(member) and inspect.getmro(member)[1].__name__ == 'SoftwareManager':
            return member
        elif inspect.ismodule(member):
            for name, mod in inspect.getmembers(member):
                manager_found = find_manager(mod)
                if manager_found:
                    return manager_found


def load_managers(locale: str, context: ApplicationContext, config: Configuration) -> List[SoftwareManager]:
    managers = []

    for f in os.scandir(ROOT_DIR + '/gems'):
        if f.is_dir() and f.name != '__pycache__':
            loader = pkgutil.find_loader('bauh.gems.{}.controller'.format(f.name))

            if loader:
                module = loader.load_module()

                manager_class = find_manager(module)

                if manager_class:
                    if locale:
                        locale_path = '{}/resources/locale'.format(f.path)

                        if os.path.exists(locale_path):
                            context.i18n.update(util.get_locale_keys(locale, locale_path)[1])

                    man = manager_class(context=context)

                    if config.enabled_gems is None:
                        man.set_enabled(man.is_default_enabled())
                    else:
                        man.set_enabled(f.name in config.enabled_gems)

                    managers.append(man)

    return managers

