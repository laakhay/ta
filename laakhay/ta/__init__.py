import importlib

from .api import *  # noqa: F401,F403
from .api import __all__ as _api_all
from .core.dataset import dataset as _dataset_builder

_dataset_module = importlib.import_module(".data.dataset", __name__)


class _DatasetAccessor:
    def __init__(self, module):
        self._module = module

    def __call__(self, *args, **kwargs):
        return _dataset_builder(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self._module, attr)


dataset = _DatasetAccessor(_dataset_module)
__all__ = list(_api_all) + ["dataset"]
