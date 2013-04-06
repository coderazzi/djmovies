from movie.models import Configuration

class ImagesHandler:

	LAST_IMAGE_PATH='last image path'

	@staticmethod
	def getLastImagePath():
		return Configuration._get(Configuration.LAST_IMAGE_PATH)

	@staticmethod
	def setLastImagePath(value):
		Configuration._set(Configuration.LAST_IMAGE_PATH, value)

	@staticmethod
	def _access(key):
		return Configuration.get('key=?', [key])

	@staticmethod
	def _get(key):
		try:
			return Configuration._access(key).value
		except:
			return None

	@staticmethod
	def _set(key, value):
		try:
			c=Configuration._access(key)
			c.value=value
			c.save()
			macaron.bake()
		except macaron.ObjectDoesNotExist:
			Configuration.create(key=key, value=value)


	@staticmethod
	def _setup(dbfile):
		import sqlite3
		with sqlite3.connect(dbfile) as conn:
			cursor = conn.cursor()
			if not cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='configuration'").fetchone()[0]:
				cursor.execute('''CREATE TABLE configuration (
				                            id          INTEGER PRIMARY KEY,
				                            key         TEXT, 
				                            value       TEXT)''')
				cursor.execute('''CREATE UNIQUE INDEX configuration_key ON configuration (key)''')


if __name__ == '__main__':
	dbfile="_.sqlite"

	Configuration._setup(dbfile)

	macaron.macaronage(dbfile=dbfile)

	print Configuration.getLastImagePath()
