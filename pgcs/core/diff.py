from . import objects

# __init__ decorator which replaces created non-__nonzero__ instances with None
def nonify(init):
	def __init__(self, *args, **kwargs):
		return init(self, *args, **kwargs) or None
	return __init__

class Value(object):
	@nonify
	def __init__(self, l, r):
		self.left, self.right = l, r

	def __nonzero__(self):
		return self.left != self.right

class ObjectValue(Value):
	@nonify
	def __init__(self, l, r):
		self.left, self.right = l.get_value(), r.get_value()

class Schema(object):
	def __init__(self, l, r):
		self.databases = [l.database, r.database]
		self.languages = named_list(Language, l.languages, r.languages)
		self.namespaces = named_list(Namespace, l.namespaces, r.namespaces)

class Language(object):
	@nonify
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner)

	def __nonzero__(self):
		return bool(self.owner)

class Namespace(object):
	@nonify
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner)
		self.types = named_list(type_object, l.types, r.types)
		# TODO: ...
		self.functions = named_list(Function, l.functions, r.functions)
		# TODO: ...

	def __nonzero__(self):
		return bool(self.owner or self.types)

class Type(object):
	@nonify
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner)
		self.notnull = Value(l.notnull, r.notnull)
		self.default = Value(l.default, r.default)

	def __nonzero__(self):
		return bool(self.owner or self.notnull or self.default)

class Domain(Type):
	@nonify
	def __init__(self, l, r):
		Type.__init__(self, l, r)
		self.basetype = ObjectValue(l.basetype, r.basetype)
		self.constraints = None # TODO: named_list(..., l.constraints, r.constraints)

	def __nonzero__(self):
		return Type.__nonzero__(self) or bool(self.basetype or self.constraints)

def type_object(l, r):
	diff_types = {
		objects.Type: Type,
		objects.Domain: Domain,
	}
	return diff_types[type(l)](l, r)

class Function(object):
	@nonify
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner)
		self.language = ObjectValue(l.language, r.language)
		self.rettype = ObjectValue(l.rettype, r.rettype)
		self.argtypes = value_list(l.argtypes, r.argtypes)
		self.source1 = Value(l.source1, r.source1)
		self.source2 = Value(l.source2, r.source2)

	def __nonzero__(self):
		return bool(self.owner or self.language or self.rettype or self.argtypes or
		            self.source1 or self.source2)

def value_list(list1, list2):
	def get_values(seq):
		return [obj.get_value() for obj in seq]

	return Value(get_values(list1), get_values(list2))

def named_list(diff_type, list1, list2):
	diff_list = []
	keys = set()

	def make_map(seq):
		map = {}
		for obj in seq:
			key = type(obj), obj.name
			keys.add(key)
			map[key] = obj
		return map

	map1 = make_map(list1)
	map2 = make_map(list2)

	for key in sorted(keys):
		obj1 = map1.get(key)
		obj2 = map2.get(key)

		name = key[1]

		if obj1 and obj2:
			diff = diff_type(obj1, obj2)
			if diff:
				diff_list.append((name, 0, diff))
		elif obj1:
			diff_list.append((name, -1, obj1))
		elif obj2:
			diff_list.append((name, +1, obj2))

	return diff_list or None
