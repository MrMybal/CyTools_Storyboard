"""Updates tab: the application, from GitHub releases, staged and reversible."""
import threading

from imgui_bundle import imgui as native

import maintenance
from ui_common import imgui, tr


class UpdatesTab:
    def __init__(self):
        self.repo = maintenance.settings().get('tool_repository', '')
        self.thread, self.result, self.error = None, None, ''

    def start(self, function):
        if self.thread and self.thread.is_alive():
            return

        def work():
            try:
                self.result, self.error = function(), ''
            except Exception as exc:  # shown in the tab
                self.result, self.error = None, str(exc)
        self.thread = threading.Thread(target=work, daemon=True)
        self.thread.start()

    def draw(self):
        values = maintenance.settings()
        release = maintenance.local_release()
        native.text(f"{tr('Installed version')}: {release.get('version')}   ABI {release.get('runtime_abi')}")
        native.set_next_item_width(360)
        _, self.repo = imgui.input_text('GitHub repository (owner/name)', self.repo)
        native.same_line()
        if imgui.button('Save##repo'):
            try:
                values['tool_repository'] = maintenance.repository(self.repo) if self.repo else ''
                maintenance.save_settings(values)
            except ValueError as exc:
                self.error = str(exc)
        if not values.get('tool_repository'):
            native.text_disabled(tr('No repository is configured for this Tool yet: enter the one where its releases '
                                    'are published (see app/UPDATES.md).'))
        native.begin_disabled(not values.get('tool_repository'))
        if imgui.button('Check'):
            self.start(maintenance.check_tool)
        native.same_line()
        if imgui.button('Download and verify'):
            self.start(maintenance.fetch_tool)
        native.end_disabled()
        native.same_line()
        if imgui.button('Restore the previous version'):
            self.start(maintenance.rollback_tool)
        if self.thread and self.thread.is_alive():
            native.text_disabled(tr('Working...'))
        if self.error:
            native.text_colored(native.ImVec4(1, .4, .35, 1), self.error)
        if isinstance(self.result, dict):
            if 'update_available' in self.result:
                native.text(f"{tr('Latest release')}: {self.result['version']} - "
                            f"{tr('update available') if self.result['update_available'] else tr('up to date')}")
            if self.result.get('message'):
                native.text_wrapped(tr(self.result['message']))
        native.text_disabled(tr('A verified release is activated at the next start; data/ is never replaced.'))
