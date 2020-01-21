import logging


def create_logger(level: int, prefix: str = None, context: type = None):
    name = 'protoactor'
    if prefix is not None and context is None:
        new_name = f'{name}.{prefix}'
        logger = logging.getLogger(new_name)
    elif prefix is None and context is not None:
        if name in context.__module__:
            new_name = f'{context.__module__}.{context.__name__}'.lower()
        else:
            new_name = f'{name}.{context.__module__}.{context.__name__}'.lower()
        logger = logging.getLogger(new_name)
    else:
        logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

