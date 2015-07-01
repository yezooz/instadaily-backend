# -*- coding: utf-8 -*-

import datetime

# from django.core.urlresolvers import reverse
from annoying.decorators import render_to

from admin.models import *
from admin import R


@render_to('admin/index.html')
def index(request):
    return {'users': 0}


@render_to('admin/subject.html')
def subject(request, subject_id=0):
    if request.method == 'POST':
        if request.get('name'):
            s = Subject()
            s.name = request.get('name')
            if len(request.get('tags')) == 0 or request.get('tags') == '""':
                s.tags = ''
            else:
                s.tags = request.get('tags')
            # active from
            f_y, f_m, f_d = request.get('active_from').split('-')
            s.active_from = datetime.datetime(int(f_y), int(f_m), int(f_d), 0, 0, 0)
            # active to
            t_y, t_m, t_d = request.get('active_to').split('-')
            s.active_to = datetime.datetime(int(t_y), int(t_m), int(t_d), 23, 59, 59)
            s.is_current = False
            s.save()

        request.redirect('/admin/subject/')

    subjects = Subject.objects.all().order_by('active_from')
    return {
        'subjects': subjects,
        'subject_id': int(subject_id),
        'today': str((subjects[len(subjects) - 1].active_to + datetime.timedelta(days=1)).date()),
        'today_3': str((subjects[len(subjects) - 1].active_to + datetime.timedelta(days=3)).date())
    }


@render_to('admin/index.html')
def test_data(request):
    redis = R()

    for us in UserSubject.objects.all():
        user = User.objects.get_by_name(us.user)

        redis.r.zincrby('leaderboard', user.name, us.points)
        redis.r.zincrby('leaderboard:year:%d' % us.subject.active_to.year, user.name, us.points)
        redis.r.zincrby('leaderboard:year:%d:month:%d' % (us.subject.active_to.year, us.subject.active_to.month),
                        user.name, us.points)
        redis.r.zincrby('leaderboard:subject:%d' % us.subject.id, user.name, us.points)

    for u in redis.r.zrange('leaderboard', 0, -1, withscores=True):
        try:
            user = User.objects.get_by_name(u[0])
            user.points = u[1]
            user.save()
        except Exception, e:
            print 'error with %s' % u[0]
            print e

    for us in UserSubject.objects.filter(subject__id=1):
        user = User.objects.get_by_name(us.user)

        user.last_subject_id = 1
        user.points += us.points
        # user.last_subject_points = us.points
        user.save()

    start_date = datetime.datetime.now() + datetime.timedelta(days=1)
    end_date = datetime.datetime.now() + datetime.timedelta(days=4)

    for s in Subject.objects.all().order_by('active_from'):
        s.active_from = "%s 00:00:00" % start_date.date()
        s.active_to = "%s 23:59:59" % end_date.date()
        s.save()

        start_date = end_date + datetime.timedelta(days=1)
        end_date = start_date + datetime.timedelta(days=2)

    return {}
