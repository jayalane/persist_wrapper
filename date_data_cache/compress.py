
import persist_dict

a = persist_dict.PersistentDict('memo_requests_get.sqlite')

for k in a:
    print "doing", k
    a.compress(k)
