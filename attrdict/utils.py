from attrdict import AttrDict
from warnings import warn


# use these, since they interact with the parameterized object
def get_with_default(obj, attr, default, map_fn=None):
    """

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


def get_cls_param_instance(params, cls_name, params_name, class_type, constructor=lambda cls, cls_params: cls(cls_params)):
    cls = get_required(params, cls_name)
    cls_params = params[params_name]

    assert isinstance(cls_params, AttrDict), cls_params

    obj = constructor(cls, cls_params)
    assert isinstance(obj, class_type), [type(obj), class_type]
    return obj


def get_or_instantiate_cls(params: AttrDict, attr_name: str, class_type, cls_name="cls", params_name="params", constructor=lambda cls, cls_params: cls(cls_params)):
    if attr_name is not None and len(attr_name) > 0:
        attr = get_required(params, attr_name)
    else:
        attr = params
    if isinstance(attr, AttrDict):
        return get_cls_param_instance(attr, cls_name, params_name, class_type, constructor=constructor)
    else:
        assert isinstance(attr, class_type)
        return attr

