# Head only: VenvBackup exists from PR 2229. A failed move into the trash must not delete the live environment.
import tempfile, pathlib, os
from unittest import mock
from pipx import paths
from pipx.commands.transaction import preserve_venv
home = pathlib.Path(tempfile.mkdtemp()); paths.ctx.make_local() if hasattr(paths.ctx,'make_local') else None
with mock.patch.object(type(paths.ctx), 'trash', new_callable=mock.PropertyMock, return_value=home / 'trash'):
    venv = home / 'venvs' / 'demo'; venv.mkdir(parents=True); (venv / 'marker').write_text('live')
    real_rename = pathlib.Path.rename
    def failing_rename(self, target):
        if self == venv: raise PermissionError(13, 'file in use')
        return real_rename(self, target)
    try:
        with mock.patch.object(pathlib.Path, 'rename', failing_rename):
            with preserve_venv(venv, enabled=True, copy_upfront=False) as backup:
                backup.remove_venv()
    except BaseException as e:
        print('raised', type(e).__name__, e)
    print('live environment still exists:', venv.exists())
