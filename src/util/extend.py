def extend(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator