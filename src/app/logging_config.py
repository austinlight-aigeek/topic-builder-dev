import inspect
import logging

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s %(message)s", level=logging.INFO)


# Decorator for `logging` log record factory
# Replaces root logger name with caller's module name
#  so we can use logging.info() etc. directly and still see module name
def _with_module_name(func):
    def wrapper(*args, **kwargs):
        record = func(*args, **kwargs)

        # Override root logger name
        # NOTE: Prefer inspect.currentframe() to inspect.stack() when possible
        #       inspect.currentframe() is 1000x faster since it uses no file I/O
        if record.name == "root":
            frame = (
                inspect.currentframe().f_back
            )  # Start at stack frame for the `logging` function that called this function
            record.name = frame.f_globals["__name__"]
            while record.name == "logging":  # Keep walking back until we exit `logging` and get to the caller
                frame = frame.f_back
                record.name = frame.f_globals["__name__"]

        return record

    return wrapper


logging.setLogRecordFactory(_with_module_name(logging.getLogRecordFactory()))
