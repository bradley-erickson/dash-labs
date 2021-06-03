from dash_labs.plugins.long_callback.managers import BaseLongCallbackManager


class CeleryCallbackManager(BaseLongCallbackManager):
    def __init__(self, celery_app):
        self.celery_app = celery_app
        self.callback_futures = dict()

    def init(self, app):
        pass

    def cancel_future(self, key):
        if key in self.callback_futures:
            future = self.callback_futures.pop(key)
            self.celery_app.control.terminate(future.task_id)
            return True
        return False

    def terminate_unhealthy_future(self, key):
        if key in self.callback_futures:
            future = self.callback_futures[key]
            if future.status != "PENDING":
                return self.cancel_future(key)
        return False

    def has_future(self, key):
        return key in self.callback_futures

    def get_future(self, key, default=None):
        return self.callback_futures.get(key, default)

    def make_background_fn(self, fn, progress=False):
        return make_celery_fn(fn, self.celery_app, progress)

    def call_and_register_background_fn(self, key, background_fn, *args, **kwargs):
        future = background_fn.delay(*args, **kwargs)
        self.callback_futures[key] = future

    def get_progress(self, key):
        future = self.get_future(key)
        if future is not None:
            progress_info = future.info if future.state == "PROGRESS" else None
            if progress_info is not None:
                return (
                    progress_info["current"],
                    progress_info["total"]
                )
        return None

    def result_ready(self, key):
        future = self.get_future(key)
        if future:
            return future.ready()
        else:
            return False

    def get_result(self, key):
        future = self.callback_futures.pop(key, None)
        if future:
            return future.get(timeout=1)
        else:
            return None


def make_celery_fn(user_fn, celery_app, progress):
    @celery_app.task(bind=True)
    def _celery_fn(self, user_callback_args):
        def _set_progress(i, total):
            self.update_state(state="PROGRESS", meta={'current': i, 'total': total})

        maybe_progress = [_set_progress] if progress else []
        print(maybe_progress)

        if isinstance(user_callback_args, dict):
            user_callback_output = user_fn(*maybe_progress, **user_callback_args)
        elif isinstance(user_callback_args, list):
            user_callback_output = user_fn(*maybe_progress, *user_callback_args)
        else:
            user_callback_output = user_fn(*maybe_progress, user_callback_args)
        return user_callback_output
    return _celery_fn
