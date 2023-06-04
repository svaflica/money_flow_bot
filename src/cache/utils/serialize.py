import pickle


def serialize_value(value):
    """
    Function to serialize object
    Input:
        value (Any): object to serialize
    Output:
        (bytes): byte string of serialized object
    """
    return pickle.dumps(value)


def deserialize_value(value, encoding="utf-8"):
    """
    Function to deserealize object
    Input:
        value (bytes): byte string to deserealize
    Output:
        (object): deserealized object
    """
    if value is None:
        return None
    return pickle.loads(value, encoding=encoding)