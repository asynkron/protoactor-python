import pytest
from protoactor.props import Props, get_default_spawner

def test_props_default_init():
    props = Props()
    
    assert props.producer == None
    # TODO: change these value with concrete default instances
    assert props.mailbox_producer == None
    assert props.supervisor_strategy == None
    assert props.dispatcher == None
    assert props.middleware == []
    assert props.middleware_chain == None
   
    assert props.spawner == get_default_spawner

class PropsObj(object):
    pass

@pytest.mark.parametrize("field,method,value", [
    ('producer', 'with_producer', PropsObj()),
    ('dispatcher', 'with_dispatcher', PropsObj()),
    ('mailbox_producer', 'with_mailbox', PropsObj()),
    ('supervisor_strategy', 'with_supervisor', PropsObj()),
])
def test_props_with(field, method, value):
    props = Props()

    with_method =  getattr(props, method)
    new_props = with_method(value)

    results = [
        ('producer', None),
        ('dispatcher', None),
        ('mailbox_producer', None),
        ('supervisor_strategy', None)
    ]

    for r in results:
        field_name = r[0]
        prop_value = getattr(new_props, field_name)
        if field_name == field:
            assert prop_value == value
        else:
            assert prop_value == r[1]
