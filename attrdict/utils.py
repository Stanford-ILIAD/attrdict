from attrdict import AttrDict
from warnings import warn


def get_with_default(obj, attr, default, map_fn=None):
    """ Get an argument from AttrDict with an optional default value

    Parameters
    ----------
    obj: AttrDict
    attr: str
        the key to access
    default: Any
        default value if key is not present
    map_fn: Callable
        how to map the extracted value if the key is present

    Returns
    -------

    """

    if isinstance(obj, AttrDict):
        has = attr in obj.node_leaf_keys()
    else:
        has = hasattr(obj, attr)

    final = None
    if has:
        at = getattr(obj, attr)
        if at is not None and not (isinstance(at, AttrDict) and at.is_empty()):
            final = at if map_fn is None else map_fn(at)
    if final is None:
        final = default

    return final


# DEPRECATED
def get_required(obj, attr):
    """

    Parameters
    ----------
    obj: AttrDict
    attr: str

    Returns
    -------

    """
    warn('get_required is deprecated, use regular access!', DeprecationWarning, stacklevel=2)
    if isinstance(obj, AttrDict):
        assert attr in obj.node_leaf_keys(), "AttrDict missing key: %s" % attr
    else:
        assert hasattr(obj, attr), "Missing attr: %s" % attr

    out = getattr(obj, attr)
    assert out is not None and not (isinstance(out, AttrDict) and out.is_empty())

    return out


def get_cls_param_instance(params, cls_name, params_name, class_type,
                           constructor=lambda cls, cls_params: cls(cls_params)):
    """ Instantiate an instance of a cls with some params, using a constructor (see default above).

    Also implements class type checking.

    Parameters
    ----------
    params: AttrDict
        The params that hold both <cls> and <cls_params>
    cls_name: str
        where in params to find the cls
    params_name: Optional[str]
        where in params to find the params (None if using the root params)
    class_type: cls
        class type to check after instantiation.
    constructor: Callable
        constructor function that takes in cls, cls_params and outputs an instance.

    Returns
    -------

    """
    cls = params[cls_name]
    if params_name is None:
        cls_params = params
    else:
        cls_params = params[params_name]

    assert isinstance(cls_params, AttrDict), cls_params

    obj = constructor(cls, cls_params)
    assert isinstance(obj, class_type), [type(obj), class_type]
    return obj


def get_or_instantiate_cls(params: AttrDict, attr_name: str, class_type, cls_name="cls", params_name=None,
                           constructor=lambda cls, cls_params: cls(cls_params)):
    """ Creates an instance of a class using params if not already created.

    Wraps <get_cls_param_instance>, to optionally check if the class has already been instantiated.
    If params[attr_name] is already instantiated, this will return that.

    Parameters
    ----------
    params: AttrDict
        global params
    attr_name: Optional[str]
        Where is the attribute to look up, or None if params is the attribute.
    class_type: cls
        What class to enforce
    cls_name: str
        What attribute within params[attr_name][cls_name] should be a class
    params_name: Optional[str]
        What attribute within params[attr_name] to consider the params (or None if root params)
    constructor: Callable
        How to instantiate cls

    Returns
    -------
    Instance of class_type

    """
    if attr_name is not None and len(attr_name) > 0:
        attr = params[attr_name]
    else:
        attr = params
    if isinstance(attr, AttrDict):
        return get_cls_param_instance(attr, cls_name, params_name, class_type, constructor=constructor)
    else:
        assert isinstance(attr, class_type)
        return attr
