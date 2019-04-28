import json
import os


class SDL_WikiCache(object):

	class Error(Exception):
	   pass

	class CacheFileError(Error):
	   pass

	class CacheFileNotSetError(Error):
	   pass

	class CacheEmptyError(Error):
	   pass

	class InvalidCacheDataError(Error):
		pass

	def __init__(self, filepath = None):
		self.cache_filepath = filepath

		self.datastore = None

		# The datastore file is not required, but try to load it.
		# If it doesn't already exist, create it with empty data.
		if filepath:
			try:
				exists = os.path.isfile(self.cache_filepath)
				if exists:
					self.load()
				else:
					self.save()
			except:
				raise SDL_WikiCache.CacheFileError

	def is_empty(self):
		return self.datastore is None

	def load(self):
		try:
			if not self.cache_filepath:
				raise SDL_WikiCache.CacheFileNotSetError
			with open(self.cache_filepath, 'r') as f:
				self.datastore = json.load(f)
		except:
			raise SDL_WikiCache.CacheFileError

	def save(self):
		if self.is_empty():
			self.datastore = {}

		try:
			if not self.cache_filepath:
				raise SDL_WikiCache.CacheFileNotSetError
			with open(self.cache_filepath, 'w') as f:
				json.dump(self.datastore, f)
		except:
			raise SDL_WikiCache.CacheFileError

	def query(self, key):
		if self.is_empty():
			raise SDL_WikiCache.CacheEmptyError
		elif key in self.datastore:
			return self.datastore[key]
		else:
			return None

	def update(self, key, data):
		# Parameter sanity checks:
		if	not key or \
			not data or \
			not isinstance(data, dict) or \
			not isinstance(key, str):
			raise SDL_WikiCache.InvalidCacheDataError

		# If the cache hasn't been loaded, start with a fresh data store:
		if self.is_empty():
			self.dataStore = {}

		# Update the cache with the new data:
		self.datastore[key] = data

