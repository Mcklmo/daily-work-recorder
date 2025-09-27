import logging


class KeyValueLogger(logging.Logger):
    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
        **kwargs,
    ):
        new_msg = msg
        new_args = args

        try:
            if args and len(args) == 1 and isinstance(args[0], dict):
                mapping = args[0]
                if isinstance(msg, str) and "%" not in msg:
                    kv_parts = [f"{k}={mapping[k]}" for k in sorted(mapping.keys())]
                    if kv_parts:
                        if msg:
                            new_msg = f"{msg} | " + " ".join(kv_parts)
                        else:
                            new_msg = " ".join(kv_parts)
                        new_args = ()
        except Exception:
            new_msg = msg
            new_args = args

        super()._log(
            level,
            new_msg,
            new_args,
            exc_info=exc_info,
            extra=extra,
            stack_info=stack_info,
            stacklevel=stacklevel,
            **kwargs,
        )


logging.setLoggerClass(KeyValueLogger)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
