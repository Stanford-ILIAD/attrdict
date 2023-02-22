from typing import List, Iterable, Optional, Any, Tuple, Set, Callable
from warnings import warn

from dotmap import DotMap
from json import dumps


class AttrDict(DotMap):
    """
    Dictionary extension for nested access.

    """

    def __getitem__(self, item):
        if isinstance(item, str) and '/' in item:
            # nested search, using '/' as the delimiter
            item_split = item.split('/')
            curr_item = item_split[0]
            next_item = '/'.join(item_split[1:])
            return self[curr_item][next_item]
        else:
            # directly lookup if not nested
            return self._map[item]

    def __setitem__(self, key, value):
        if isinstance(key, str) and '/' in key:
            # nested assignment
            key_split = key.split('/')
            curr_key = key_split[0]
            next_key = '/'.join(key_split[1:])
            if curr_key not in self._map and curr_key != '_ipython_canary_method_should_not_exist_':
                # automatically extend to new AttrDict on set
                self[curr_key] = self.__class__()
            self[curr_key][next_key] = value
        else:
            # dotmap based assignment.
            super(AttrDict, self).__setitem__(key, value)

    def pprint(self, str_max_len=30, ret_string=False):
        if str_max_len is None:
            str_self = self.leaf_apply(lambda x: str(x))
        else:
            str_self = self.leaf_apply(lambda x: str(x)[:str_max_len] + '...')
        if ret_string:
            return dumps(str_self.toDict(), indent=4, sort_keys=True)
        else:
            return super(AttrDict, str_self).pprint(pformat='json')

    def leaf_keys(self):
        def _get_leaf_keys(d, prefix=''):
            for key, value in d.items():
                new_prefix = prefix + '/' + key if len(prefix) > 0 else key
                if isinstance(value, AttrDict):
                    yield from _get_leaf_keys(value, prefix=new_prefix)
                else:
                    yield new_prefix

        yield from _get_leaf_keys(self)

    def node_leaf_keys(self):
        def _get_node_leaf_keys(d, prefix=''):
            for key, value in d.items():
                new_prefix = prefix + '/' + key if len(prefix) > 0 else key
                if isinstance(value, AttrDict):
                    yield new_prefix  # yield AttrDict mid level nodes as well
                    yield from _get_node_leaf_keys(value, prefix=new_prefix)
                else:
                    yield new_prefix

        yield from _get_node_leaf_keys(self)

    def list_leaf_keys(self) -> List[str]:
        # for printing the keys
        return list(self.leaf_keys())

    def list_node_leaf_keys(self):
        # for printing the keys
        return list(self.node_leaf_keys())

    def leaf_values(self):
        for key in self.leaf_keys():
            yield self[key]

    def node_leaf_values(self):
        for key in self.leaf_keys():
            yield self[key]

    def leaf_items(self):
        for key in self.leaf_keys():
            yield key, self[key]

    def node_leaf_items(self):
        for key in self.node_leaf_keys():
            yield key, self[key]

    def leaf_filter(self, func):
        d = AttrDict()
        for key, value in self.leaf_items():
            if func(key, value):
                d[key] = value
        return d

    def leaf_partition(self, cond):
        d_true = AttrDict()
        d_false = AttrDict()
        for key, value in self.leaf_items():
            if cond(key, value):
                d_true[key] = value
            else:
                d_false[key] = value
        return d_true, d_false

    def leaf_arrays(self):
        from ._base_utils import is_array
        return self.leaf_filter(lambda k, v: is_array(v))

    def leaf_shapes(self):
        # mainly good for debugging tensor dicts.
        return self.leaf_arrays().leaf_apply(lambda arr: arr.shape)

    def node_leaf_filter(self, func, copy_nodes=False):
        d = AttrDict()
        for key, value in self.node_leaf_items():
            if func(key, value):
                d[key] = value
                if copy_nodes and isinstance(d[key], AttrDict):
                    d[key] = d[key].leaf_copy()
        return d

    def leaf_filter_keys(self, names):
        return self.leaf_filter(lambda key, value: key in names)

    def node_leaf_filter_keys(self, names):
        return self.node_leaf_filter(lambda key, value: key in names)

    def node_leaf_filter_keys_required(self, names, copy_nodes=False):
        """ Filter with both leaf and node names.

        Parameters
        ----------
        names:
            keys to get, can include nodes
        copy_nodes:
            if True, will recursively copy from a filtered key.

        Returns
        -------

        """
        out = AttrDict()
        for key in names:
            out[key] = self >> key
            if copy_nodes and isinstance(out[key], AttrDict):
                out[key] = out[key].leaf_copy()
        return out

    def leaf_assert(self, func):
        """
        Recursively asserts func on each value
        :param func (lambda): takes in one argument, outputs True/False
        """
        for value in self.leaf_values():
            assert func(value), [value, [key for key, item in self.leaf_items() if item is value]]

    def leaf_reduce(self, reduce_fn, seed=None):
        """
        sequentially reduces the given values for this dict, using reduce_fn
        Fixed order reduction should not be assumed.

        :param reduce_fn: [red, val_i] -> new_red
        :param seed: red0, if not present will use the first value to be popped
        :return:
        """
        vs = list(self.leaf_values())
        if seed is None:
            assert len(vs) > 0, len(vs)
            reduced_val = vs.pop()
        else:
            reduced_val = seed

        while len(vs) > 0:
            reduced_val = reduce_fn(reduced_val, vs.pop())
        return reduced_val

    def all_equal(self, equality_fn: Callable[[Any, Any], bool] = lambda a, b: a == b):
        v = list(self.leaf_values())
        if len(v) <= 1:
            return True
        return all(equality_fn(v[i], v[i+1]) for i in range(len(v) - 1))

    def leaf_modify(self, func):
        """
        Applies func to each value (recursively), modifying in-place
        :param func (lambda): takes in one argument and returns one object
        """
        for key, value in self.leaf_items():
            try:
                self[key] = func(value)
            except Exception as e:
                raise type(e)(key + ' : ' + str(e)).with_traceback(e.__traceback__)

    def leaf_kv_modify(self, func):
        """
        Applies func to each value (recursively), modifying in-place
        :param func (lambda): takes in two arguments and returns one object
        """
        for key, value in self.leaf_items():
            self[key] = func(key, value)

    def leaf_key_change(self, func):
        """
        Applies func to each key value (recursively), modifying in-place
        :param func (lambda): takes in two arguments and returns one object
        """
        d = AttrDict()
        for key, value in self.leaf_items():
            d[func(key, value)] = value
        return d

    def leaf_apply(self, func):
        """
        Applies func to each value (recursively) and returns a new AttrDict
        :param func (lambda): takes in one argument and returns one object
        :return AttrDict
        """
        d = AttrDict()
        for key, value in self.leaf_items():
            try:
                d[key] = func(value)
            except Exception as e:
                raise type(e)(key + ' : ' + str(e)).with_traceback(e.__traceback__)
        return d

    def leaf_kv_apply(self, func):
        d = AttrDict()
        for key, value in self.leaf_items():
            try:
                d[key] = func(key, value)
            except Exception as e:
                raise type(e)(key + ' : ' + str(e)).with_traceback(e.__traceback__)
        return d

    def leaf_call(self, func, pass_in_key_to_func=False):
        """
        Applies func to each value and ignores the func return
        :param func (lambda): takes in one argument, return unused
        """
        for key, value in self.leaf_items():
            func(key, value) if pass_in_key_to_func else func(value)

    def combine(self, d_other, ret=False):
        for k, v in d_other.leaf_items():
            self[k] = v

        if ret:
            return self

    def safe_combine(self, d_other, ret=False, warn_conflicting=False):
        others = set(d_other.leaf_keys())
        if not others.isdisjoint(self.leaf_keys()):
            if warn_conflicting:
                print(f"Combine found conflicts: {list(others.intersection(self.leaf_keys()))}")
            # keep keys in other dict that aren't conflicting
            d_other = d_other.leaf_filter_keys(list(others.difference(self.leaf_keys())))
        return self.combine(d_other, ret=ret)

    def freeze(self):
        frozen = AttrDict(self, _dynamic=False)
        self.__dict__.update(frozen.__dict__)
        return self

    def is_empty(self):
        return len(self.list_leaf_keys()) == 0

    def get_one(self):
        # raises StopIteration if is_empty()
        k, item = next(self.leaf_items())
        return item

    def has_leaf_key(self, key):
        return key in self.leaf_keys()

    def has_leaf_keys(self, keys):
        lk = set(self.leaf_keys())
        keys = set(keys)
        common = lk.intersection(keys)
        return len(common) == len(keys)

    def has_node_leaf_key(self, key):
        return key in self.node_leaf_keys()

    def has_node_leaf_keys(self, keys):
        k = set(self.node_leaf_keys())
        keys = set(keys)
        common = k.intersection(keys)
        return len(common) == len(keys)

    def leaf_key_intersection(self, ls: Set):
        return list(set(ls).intersection(self.leaf_keys()))

    def leaf_key_symmetric_difference(self, ls: Set):
        return list(set(ls).symmetric_difference(self.leaf_keys()))

    def leaf_key_difference(self, ls):
        return list(set(self.leaf_keys()).difference(ls))

    def leaf_key_missing(self, ls):
        return list(set(ls).difference(set(self.leaf_keys())))

    def node_leaf_key_overlap(self, ls: Set):
        return list(set(ls).intersection(self.node_leaf_keys()))

    def node_leaf_key_leftovers(self, ls):
        return list(set(self.node_leaf_keys()).difference(ls))

    def get_keys_required(self, keys) -> Tuple:
        assert self.has_node_leaf_keys(keys), list(set(keys).difference(self.node_leaf_keys()))
        return tuple(self[key] for key in keys)

    def get_keys_optional(self, keys, defaults):
        all_keys = list(self.node_leaf_keys())
        return tuple(self[keys[i]] if keys[i] in all_keys else defaults[i] for i in range(len(keys)))

    @staticmethod
    def leaf_combine_and_apply(ds, func, map_func=lambda x: x, match_keys=True, pass_in_key_to_func=False):
        # if match_keys false, default to the first dataset element's keys
        leaf_keys = tuple(sorted(ds[0].leaf_keys()))
        if match_keys:
            for d in ds[1:]:
                assert leaf_keys == tuple(sorted(d.leaf_keys())), "\n %s \n %s \n %s" % (leaf_keys, tuple(sorted(d.leaf_keys())), set(leaf_keys).symmetric_difference(d.leaf_keys()))

        d_combined = AttrDict()
        for k in leaf_keys:
            values = [map_func(d >> k) for d in ds]
            if pass_in_key_to_func:
                d_combined[k] = func(k, values)
            else:
                d_combined[k] = func(values)

        return d_combined

    @staticmethod
    def from_dict(d, nested=True):
        d_attr = AttrDict()
        for k, v in d.items():
            if nested and isinstance(v, dict):
                v = AttrDict.from_dict(v, nested=True)
            d_attr[k] = v
        return d_attr

    def as_dict(self, out=None):
        if out is None:
            out = dict()
        for name in self.leaf_keys():
            out[name] = self[name]
        return out

    @staticmethod
    def from_kvs(keys: List[str], vals: List[Any]):
        assert len(keys) == len(vals)
        out = AttrDict()
        for k, v in zip(keys, vals):
            out[k] = v
        return out

    def leaf_copy(self):
        out = AttrDict()
        for k, v in self.leaf_items():
            out[k] = v
        return out

    """ SHORT HAND """

    # DEPRECATED
    # d >> key is short-hand for getting a required key
    def __rshift__(self, name):
        warn('right shifting is deprecated, use regular access!', DeprecationWarning, stacklevel=2)
        assert self.has_node_leaf_key(name), ">>: missing key %s" % name
        return self[name]

    # d << key is short-hand for getting an optional key with default None
    def __lshift__(self, name):
        if self.has_node_leaf_key(name):
            return self[name]
        return None

    # d > Iter: node_leaf_keys_required
    def __gt__(self, names: Iterable[str]):
        assert isinstance(names, Iterable) or names is None
        if names is None:
            return self.leaf_copy()
        return self.node_leaf_filter_keys_required(names)

    # d < Iter:  node_leaf_keys_optional
    def __lt__(self, names: Optional[Iterable[str]]):
        assert isinstance(names, Iterable)
        return self.node_leaf_filter_keys(names)

    # d1 & d2 is shorthand for combining dictionaries without modifying the original structs
    def __and__(self, other):
        out = self.leaf_copy()
        if other is None:
            return out
        return out.combine(other, ret=True)


class IterableAttrDict(AttrDict, Iterable):
    """
    Iterates over inner values, not implemented.
    """
    def __iter__(self):
        raise NotImplemented
