from expr.nodes import Group, Rule, Source
from expr.ops import CUSTOM_OPERATORS, Condition, Operator, QBOperatorSpec
from util import get_all_subclasses

filters = [rule.to_filter() for rule in get_all_subclasses(Rule)]

_operator_models = [CUSTOM_OPERATORS.get(op, {"type": op.value}) for op in Operator]
operators = [op.model_dump(mode="json") if isinstance(op, QBOperatorSpec) else op for op in _operator_models]

default_expression = Group(condition=Condition.AND, rules=[Source()], **{"not": False}).model_dump(mode="json")
