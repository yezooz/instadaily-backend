import redis


class R(object):
    def __init__(self):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)

    def add_photo(self, instagram_id):
        self.r.rpush('photo:queue', instagram_id)

    def get_photos(self, i=20):
        l = []
        for x in xrange(0, i):
            v = self.r.lpop('photo:queue')
            if v == None: break

            l.append(v)
            self.r.lrem('photo:queue', i * -1, v)

        # print 'left %d photos to process' % self.r.llen('photo:queue')
        return l
