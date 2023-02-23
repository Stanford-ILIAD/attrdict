
# AttrDict
This package contains a generic dictionary `AttrDict`, which implements nested dictionaries that are easy to access, filter, combine, and write to.

Installation: `pip install attr-dicts`:

PyPI: https://pypi.org/project/attr-dicts/

**Creation**: Let's say we want to store the following nested structure of arrays:
```angular2html
- food
    - carrot: [1,2,3]
    - apple: [4,5,6]
    - broccoli: [7,8,9,10]
- utensils
    - fork
        - three_prong: [11,12]
        - four_prong: [13,14,15]
    - spoon: [16,17,18]
```

AttrDicts use '/' to separate keys, and this is built in to read/write operations. Here's two examples of how to instantiate the above structure.
```angular2html
d = AttrDict()
d['food/carrot'] = [1,2,3]
d.food.apple = [4,5,6]
d['food/broccoli'] = [7,8,9,10]
d['utensils/fork/three_prong'] = [11,12]
d['utensils/fork/four_prong'] = [13,14,15]
d['utensils/spoon'] = [16,17,18]
```
Note that both indexing and dot access work, since AttrDicts inherit from the DotMap class. Here's a slightly less effort way:
```angular2html
d = AttrDict(
    food=AttrDict(carrot=[1,2,3], apple=[4,5,6], broccoli=[7,8,9,10]),
    utensils=AttrDict(
        fork=AttrDict(three_prong=[11,12], four_prong=[13,14,15]), 
        spoon=[16,17,18]
    )
)
```
**Access**: There are several ways to access an AttrDict.
1. `d['utensils/fork/three_prong']`: standard dictionary access, but using '/' to implicitly sub-index (KeyError if missing)
2. `d.utensils.fork.three_prong`: dotmap access (AttributeError if missing)
3. `d.utensils['fork/three_prong']`: mixed indexing + dotmap (either AttributeError or KeyError if missing)
4. `d >> 'utensils/fork/three_prong`: (DEPRECATED) required key access, will error if not present.
5. `d << 'utensils/fork/three_prong`: optional key access, will return None if not present
6. `d > ['utensils/fork/three_prong,'utensils/spoon']`: required key filtering, returns sub-dict. errors if a key in the arg list is not present.
7. `d < ['utensils/fork/three_prong,'utensils/spoon']`: optional key access, returns sub-dict, ignores keys that aren't present.

**Node/Leaf operations**: Leaf nodes are any access pattern that returns something that isn't an AttrDict. In the above example, 'food' is a node key, while 'food/carrot' is a leaf key.
We can operate on all leaf nodes at once, here are some example methods:
1. `d.leaf_keys()`: Generator that yields leaf keys under a depth first traverse.
2. `d.list_leaf_keys()`: Outputs a list instead of generator.
3. `d.leaf_values()`: Generator that yields leaf values under a depth first traverse.
4. `applied_d = d.leaf_apply(lambda v: <new_v>)`: Apply a function(value) on all leaf values, and create a new AttrDict.
5. `filtered_d = d.leaf_filter(lambda k,v: <condition>)`: Only keep leaf keys where `condition` is true in new AttrDict.

Similarly, there are functions that operate on both nodes and leaves. 

**Combining**: Combining AttrDicts can be done in several ways:
1. `new_d = d1 & d2`: Standard join, returns a new AttrDict, which will favor keys from d2 if there are duplicates.
2. `d1.combine(d2)`: Mutates d1 to join the arrays.
3. `new_d = AttrDict.leaf_combine_and_apply([d1, d2, ...], lambda vs: <return one value>)`: Given a list of AttrDicts with the same keys, will create one AttrDict where the value for a given key `k` is some function of `vs = [d1[k], d2[k], ...]`.

