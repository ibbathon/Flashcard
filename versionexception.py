"""versionexception.py
Author = Richard D. Fears
Created = 2017-07-26
LastModified = 2017-07-26
Description = Defines the VersionException class, which is fired when unpickling a class object
	which cannot be converted to the current class version (e.g. because the unpickled object
	is a newer version, or because the version jump cannot be bridged).
"""

class VersionException (Exception):
	"""VersionException class
	A simple Exception which fires when unpickling incompatibly-versioned objects.
	"""

	TOO_NEW = "Data is later version than program (data: {}, program: {})"
	TOO_OLD = "Data cannot be converted to program's version (data: {}, program: {})"
	BAD_TYPE = "Data's version is not compatible with list-of-integers versioning (data: {})"
	ALL_ERROR_TYPES = (TOO_NEW,TOO_OLD,BAD_TYPE)

	def __init__ (self, error_type, instance_version, class_version = []):
		"""VersionException class
		Sets the message for this exception, based on the type of version error.
		"""
		# Don't bother with any error-checking, since we're firing an exception anyways
		if error_type == self.BAD_TYPE:
			self.message = error_type.format(instance_version)
		else:
			self.message = error_type.format(
				'.'.join(map(str,instance_version)),'.'.join(map(str,class_version)))

	def __str__ (self):
		return self.message
