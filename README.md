A few tools to make it easier for me to read and write various data to
sqlite3 DBs.  Generally, I'm using data that has the same structure
each day, but the structure might evolve over the course of the
project.  Generally, the data is extremely expensive to calculate, and
I want to save all my intermediate results.

modules:

cache:  a thread-safe LRU cache.  Used to cache in memory SQLite DBs when configured. Kurt Rose is author
cached_requests:  if you have requests, a wrapper to cache contents of URL by URL key.  Forever.
compress: utility written to re-set all the values of a cache (enabling compression if so configured once I added that
          capability).
generic_data:  a SQLite thing to let me add fields in on the fly.
persist_dict:  from Stack Overflow - but enhanced to have compression, threadsafety and json preferred to pickling.  Also used and some operational fixes.
decorators:  a decorator to memoize functions using persist_dict; also versions that expect to be memoizing a class with date members.  Also randomly retry and timeit decorators.  


Please feel free to contact me about this.

chris@lane-jayasinha.com

