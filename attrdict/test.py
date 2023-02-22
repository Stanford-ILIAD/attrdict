from attrdict import AttrDict
from attrdict.utils import get_required

if __name__ == '__main__':
    # just an example of how to instantiate
    dc = AttrDict(dict(
        a=dict(
            b=1,
            c=2
        )
    ))
    print('dc:', dc.pprint(ret_string=True))

    dc_1 = AttrDict(
        a=AttrDict(
            e=4
        )
    )
    print('dc_1:', dc_1.pprint(ret_string=True))

    dc_dup = dc.copy()

    combined = dc_dup & dc_1
    print('dc_combined:', combined.pprint(ret_string=True))
    print('dc (original):', dc.pprint(ret_string=True))

    assert 'a/b' in dc.leaf_keys()
    assert 'a' in dc.keys()
    assert 'a/e' in combined.leaf_keys()
    assert 'a/e' not in dc.leaf_keys()

    # raises a key error
    try:
        f = dc['a/f']
        raise AssertionError('Key a/f should not exist!')
    except KeyError:
        pass

    # raises an attribute error
    try:
        f = dc.a.f
        raise AssertionError('Key a.f should not exist!')
    except AttributeError:
        pass

    print('--- this should issue a deprecation warning ---')
    print(f"value of a: {dc >> 'a/b'}")

    print('--- this should also issue a deprecation warning ---')
    print(f"value of a: {get_required(dc, 'a/b')}")
