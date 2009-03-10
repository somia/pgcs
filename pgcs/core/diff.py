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

class Schema(object):
	@nonify
	def __init__(self, l, r):
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

	def __nonzero__(self):
		return bool(self.owner and self.types)

class Type(object):
	@nonify
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner)
		self.notnull = Value(l.notnull, r.notnull)
		self.default = Value(l.default, r.default)

	def __nonzero__(self):
		return bool(self.owner and self.notnull and self.default)

class Domain(Type):
	@nonify
	def __init__(self, l, r):
		Type.__init__(self, l, r)
		self.basetype = Value(l.basetype.get_value(), r.basetype.get_value())
		# TODO: self.constraints = named_list(..., l.constraints, r.constraints)

	def __nonzero__(self):
		return Type.__nonzero__(self) and bool(self.basetype and self.constraints)

def type_object(l, r):
	diff_types = {
		objects.Type: Type,
		objects.Domain: Domain,
	}
	return diff_types[type(l)](l, r)

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
