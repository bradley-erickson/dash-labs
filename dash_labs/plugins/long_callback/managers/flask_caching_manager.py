from multiprocessing import Process
from dash_labs.plugins.long_callback.managers import BaseLongCallbackManager


class FlaskCachingCallbackManager(BaseLongCallbackManager):
    def __init__(
        self, flask_cache, clear_cache=None, cache_by=None, cache_timeout=None
    ):
        super().__init__(cache_by)
        self.flask_cache = flask_cache
        self.callback_futures = dict()

        # Handle default clear_cache
        if clear_cache is None:
            # Clear cache at startup if not caching
            clear_cache = cache_by is None
        self.clear_cache = clear_cache
        self.cache_timeout = cache_timeout

    def init(self, app):
        self.flask_cache.init_app(app.server)
        if self.clear_cache:
            self.flask_cache.clear()

    def delete_future(self, key):
        if key in self.callback_futures:
            future = self.callback_futures.pop(key, None)
            if future:
                future.kill()
                future.join()
                return True
        return False

    def clear_cache_entry(self, key):
        self.flask_cache.delete(key)

    def terminate_unhealthy_future(self, key):
        return False

    def has_future(self, key):
        return self.callback_futures.get(key, None) is not None

    def get_future(self, key, default=None):
        return self.callback_futures.get(key, default)

    def make_background_fn(self, fn, progress=False):
        return make_update_cache(fn, self.flask_cache, progress, self.cache_timeout)

    @staticmethod
    def _make_progress_key(key):
        return key + "-progress"

    def call_and_register_background_fn(self, key, background_fn, args):
        self.delete_future(key)
        future = Process(
            target=background_fn, args=(key, self._make_progress_key(key), args)
        )
        future.start()
        self.callback_futures[key] = future

    def get_progress(self, key):
        future = self.get_future(key)
        if future is not None:
            progress_key = self._make_progress_key(key)
            return self.flask_cache.get(progress_key)
        return None

    def result_ready(self, key):
        return self.flask_cache.get(key) not in (None, "__undefined__")

    def get_result(self, key):
        # Get result value
        result = self.flask_cache.get(key)
        if result == "__undefined__":
            result = None

        # Clear result if not caching
        if self.cache_by is None and result is not None:
            self.clear_cache_entry(key)

        # Always delete_future (even if we didn't clear cache) so that we can
        # handle the case where cache entry is cleared externally.
        self.delete_future(key)
        return result


def make_update_cache(fn, cache, progress, timeout):
    def _callback(result_key, progress_key, user_callback_args):
        def _set_progress(i, total):
            cache.set(progress_key, (i, total), timeout=timeout)

        maybe_progress = [_set_progress] if progress else []
        if isinstance(user_callback_args, dict):
            user_callback_output = fn(*maybe_progress, **user_callback_args)
        elif isinstance(user_callback_args, list):
            user_callback_output = fn(*maybe_progress, *user_callback_args)
        else:
            user_callback_output = fn(*maybe_progress, user_callback_args)
        cache.set(result_key, user_callback_output, timeout=timeout)

    return _callback
