import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from bauh import __version__, __app_name__, app_args, ROOT_DIR
from bauh.api.abstract.controller import ApplicationContext
from bauh.api.http import HttpClient
from bauh.view.core import gems, config
from bauh.view.core.controller import GenericSoftwareManager
from bauh.view.core.downloader import AdaptableFileDownloader
from bauh.view.qt.systray import TrayIcon
from bauh.view.qt.window import ManageWindow
from bauh.view.util import util, logs, resource
from bauh.view.util.cache import DefaultMemoryCacheFactory, CacheCleaner
from bauh.view.util.disk import DefaultDiskCacheLoaderFactory


def main():
    if not os.getenv('PYTHONUNBUFFERED'):
        os.environ['PYTHONUNBUFFERED'] = '1'

    args = app_args.read()
    logger = logs.new_logger(__app_name__, bool(args.logs))
    app_args.validate(args, logger)

    i18n_key, i18n = util.get_locale_keys(args.locale)

    cache_cleaner = CacheCleaner()
    cache_factory = DefaultMemoryCacheFactory(expiration_time=args.cache_exp, cleaner=cache_cleaner)
    icon_cache = cache_factory.new(args.icon_exp)

    http_client = HttpClient(logger)

    context = ApplicationContext(i18n=i18n,
                                 http_client=http_client,
                                 disk_cache=args.disk_cache,
                                 download_icons=args.download_icons,
                                 app_root_dir=ROOT_DIR,
                                 cache_factory=cache_factory,
                                 disk_loader_factory=DefaultDiskCacheLoaderFactory(disk_cache_enabled=args.disk_cache, logger=logger),
                                 logger=logger,
                                 distro=util.get_distro(),
                                 file_downloader=AdaptableFileDownloader(logger, bool(args.download_mthread),
                                                                         i18n, http_client))
    user_config = config.read()

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setWindowIcon(QIcon(resource.get_path('img/logo.svg')))

    if user_config.style:
        app.setStyle(user_config.style)
    else:
        if app.style().objectName().lower() not in {'fusion', 'breeze'}:
            app.setStyle('Fusion')

    managers = gems.load_managers(context=context, locale=i18n_key, config=user_config)

    manager = GenericSoftwareManager(managers, context=context, app_args=args)
    manager.prepare()

    mwindow_args = {'i18n': i18n, 'manager': manager, 'disk_cache': args.disk_cache,
                    'download_icons': bool(args.download_icons), 'screen_size': app.primaryScreen().size(),
                    'suggestions': args.sugs, 'display_limit': args.max_displayed, 'config': user_config,
                    'context': context, 'http_client': http_client, 'logger': logger,
                    'notifications': bool(args.system_notifications), 'icon_cache': icon_cache}

    if args.tray:
        tray_icon = TrayIcon(i18n=i18n,
                             manager=manager,
                             check_interval=args.check_interval,
                             mwindow_args=mwindow_args,
                             update_notification=bool(args.system_notifications))
        tray_icon.show()

        if args.show_panel:
            tray_icon.show_manage_window()
    else:
        manage_window = ManageWindow(**mwindow_args)
        manage_window.refresh_apps()
        manage_window.show()

    cache_cleaner.start()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
