# -*- coding: utf-8 -*-
import logging
from random import randrange

from django.db import models
from django.core.cache import cache

import datetime

# import simplejson as json
# from django.conf import settings

class UserManager(models.Manager):
    def get_by_name(self, name):
        try:
            return self.filter(name=name).get()
        except User.DoesNotExist:
            return None


class User(models.Model):
    name = models.CharField(max_length=255)
    instagram_id = models.IntegerField()
    token = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    full_name = models.CharField(max_length=100)
    pic = models.CharField(max_length=100)

    points = models.IntegerField(default=0)
    last_subject_id = models.IntegerField()
    last_subject_points = models.IntegerField()
    vote_like = models.IntegerField()
    vote_dislike = models.IntegerField()

    subject_last_photo = models.DateTimeField(default=datetime.datetime.now())
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = UserManager()

    class Meta:
        db_table = 'user'
        verbose_name = 'User'

    def __unicode__(self):
        return "User %s" % self.name

    def to_dict(self):
        return {
            'id': self.id,
            'instagram_id': self.instagram_id,
            'name': self.name,
            'pic': self.pic,
            'points': self.points,
            'last_subject_points': self.last_subject_points or 0,
        }


class SubjectManager(models.Manager):
    def get_by_id(self, id):
        return self.filter(id=id).get()

    def get_all(self):
        return self.all().order_by('is_current', 'active_from', 'name')

    def get_current(self):
        try:
            return self.filter(is_current=True).get()
        except Subject.DoesNotExist:
            return None

    def get_for_date(self, date):
        # TODO: fix
        # return self.get_current()

        try:
            return self.filter(active_from__lte=date, active_to__gte=date).get()
        except Subject.DoesNotExist:
            return None


class Subject(models.Model):
    name = models.CharField(max_length=100)
    active_from = models.DateTimeField()
    active_to = models.DateTimeField()
    tags = models.CharField(max_length=255)

    is_current = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = SubjectManager()

    class Meta:
        db_table = 'subject'
        verbose_name = 'Subject'

    def __unicode__(self):
        return "Subject %s" % self.name

    def to_dict(self):
        diff = self.active_to - datetime.datetime.now()
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return {
            'name': self.name,
            'id': self.id,
            'due': {
                'day': diff.days,
                'hour': '%02d' % hours,
                'minute': '%02d' % minutes,
                'second': '%02d' % seconds,
            },
            'current': int(self.is_current)
        }


class PhotoManager(models.Manager):
    def get_by_id(self, pid):
        return self.filter(id=pid).get()

    def get_by_instagram_id(self, instagram_id):
        try:
            return self.filter(instagram_id=instagram_id).get()
        except Photo.DoesNotExist:
            return None

    def get_more_photos(self, user):
        key = 'user_vote_%s_' % user.name
        # cache.delete_many([key, key+'subject_id', key+'photos'])
        subject = None
        subject_id = cache.get(key + 'subject_id')
        if subject_id is not None:
            subject = Subject.objects.get_by_id(int(subject_id))
            if not subject.is_current:
                cache.delete_many([key + 'subject_id', key + 'photos'])
                logging.info('Cleared cache for %s' % user.name)
        elif subject_id is None or \
                        subject is None or \
                        subject.is_current == False:
            subject = Subject.objects.get_current()
            subject_id = subject.id
            cache.set(key + 'subject_id', subject_id, 3600 * 24)

        photos = cache.get(key + 'photos')
        if photos is None:
            photos = []

        if len(photos) < 50:
            ps = self.filter(subject=subject, is_active=True, is_user_active=True, is_blocked=False)
            if user.subject_last_photo is not None:
                ps = ps.filter(date_instagram__gt=user.subject_last_photo)

            if ps.count() > 0:
                user.subject_last_photo = ps[ps.count() - 1].date_instagram
                user.save()

            photos.extend([p.id for p in ps.order_by('date_instagram')[:200]])

        drawed = []
        items = len(photos)
        while len(drawed) < 10 and len(photos) > 0:
            try:
                r = randrange(0, items - 1)
                p = Photo.objects.get_by_id(photos[r])

                # remove this photo if is not active anymore
                if not p.is_active or not p.is_user_active or p.is_blocked:
                    raise ValueError
                # don't show my photos
                if p.user == user.name:
                    raise ValueError
                # if drawed photos are from different subjects, it means subject has changed. clear whole set.
                if p.subject_id != subject_id:
                    photos = []
                    drawed = []
                    cache.delete_many([key + 'subject_id', key + 'photos'])
                    raise ValueError
                drawed.append(p.to_dict())
            except IndexError:
                logging.warning('not found photo @ %d' % r)
                continue
            except ValueError:
                logging.info('photo disabled or belongs not to current subject or is just mine')
            try:
                del photos[r]
            except:
                pass
            items -= 1

        # if len(photos) > 0:
        cache.set(key + 'photos', photos, 3600 * 24)
        # else:
        # cache.delete_many([key, key+'subject_id', key+'photos'])
        return drawed


class Photo(models.Model):
    instagram_id = models.CharField(max_length=255)
    user = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject)

    likes = models.IntegerField()
    dislikes = models.IntegerField()
    points = models.IntegerField()
    total_score = models.IntegerField()
    flags = models.IntegerField()

    caption = models.CharField(max_length=255)
    tags = models.CharField(max_length=255)
    filter = models.CharField(max_length=100)
    link = models.URLField()
    url = models.URLField()
    url_low = models.URLField()
    url_thumb = models.URLField()
    loc_lat = models.CharField(max_length=50)
    loc_lng = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)
    is_user_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    is_final_score = models.BooleanField(default=False)
    date_instagram = models.DateTimeField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = PhotoManager()

    class Meta:
        db_table = 'photo'
        verbose_name = 'Photo'

    def __unicode__(self):
        return "Photo %d" % self.instagram_id

    def to_dict(self, insta_photo_object=None):
        if insta_photo_object:
            d = {}
            obj = insta_photo_object
            d['instagram_id'] = obj['id']
            d['user'] = obj['user']['username']
            d['likes'] = obj['likes']['count']
            d['dislikes'] = 0
            d['points'] = 0
            d['total_score'] = obj['likes']['count']
            d['caption'] = ''
            if obj['caption'] is not None:
                d['caption'] = obj['caption']['text']
            d['tags'] = obj['tags']
            d['url'] = obj['images']['standard_resolution']['url']
            d['url_low'] = obj['images']['low_resolution']['url']
            d['url_thumb'] = obj['images']['thumbnail']['url']
            if 'instadaily' in obj['tags']:
                d['active'] = True
            else:
                d['active'] = False
            d['user_active'] = True
            d['blocked'] = False
            return d

        return {
            'instagram_id': self.instagram_id,
            'user': self.user,
            'likes': self.likes,
            'points': self.points,
            'dislikes': self.dislikes,
            'total_score': self.total_score,
            'caption': self.caption,
            'tags': self.tags,
            'url': self.url,
            'url_low': self.url_low,
            'url_thumb': self.url_thumb,
            'active': self.is_active,
            'user_active': self.is_user_active,
            'blocked': self.is_blocked
        }

    def add_or_update(self, data):
        p = Photo.objects.get_by_instagram_id(data['id'])
        if p is None:
            p = Photo()
            p.instagram_id = data['id']
            p.user = data['user']['username']
            p.dislikes = 0
            p.points = 0
            p.likes = 0
            p.flags = 0
            p.total_score = 0
            p.date_instagram = datetime.datetime.fromtimestamp(float(data['created_time']))
            p.subject = Subject.objects.get_for_date(p.date_instagram)
            if data['caption'] is not None:
                p.caption = data['caption']['text']
            p.filter = data['filter']
            p.link = data['link']
            p.url = data['images']['standard_resolution']['url']
            p.url_low = data['images']['low_resolution']['url']
            p.url_thumb = data['images']['thumbnail']['url']
            try:
                p.loc_lat = str(data['location']['latitude'])
                p.loc_lng = str(data['location']['longitude'])
            except (KeyError, TypeError):
                pass
            p.is_active = True
            p.is_user_active = True
            p.is_blocked = False
            p.is_final_score = False

        p.likes = data['likes']['count']
        p.tags = data['tags']
        p.total_score = p.likes

        try:
            p.save()
        except Exception, e:
            try:
                if len(p.caption) > 0:
                    p.caption = p.caption[:497] + '...'
                    p.save()
                else:
                    logging.error('Error with Photo - %s' % e)
            except Exception, e:
                return


class TagManager(models.Manager):
    pass


class Tag(models.Model):
    name = models.CharField(max_length=100)
    min_tag_id = models.IntegerField()

    objects = TagManager()

    class Meta:
        db_table = 'tag'
        verbose_name = 'Tag'

    def __unicode__(self):
        return "Tag %s" % self.name


class UserSubjectManager(models.Manager):
    def get_by_user(self, username):
        return self.filter(user=username).order_by('-date_added')


class UserSubject(models.Model):
    user = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject)
    best_photo = models.ForeignKey(Photo)
    points = models.IntegerField()

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = UserSubjectManager()

    class Meta:
        db_table = 'user_subject'
        verbose_name = 'UserSubject'

    def __unicode__(self):
        return "%s + %s = %d pts" % (self.user, self.subject, self.points)

    def to_dict(self):
        key = 'user_subject_%s_%s' % (self.user, self.subject.id)
        item = cache.get(key)
        if item is not None:
            return item

        item = {
            'subject': self.subject.to_dict(),
            'best_photo': self.best_photo.to_dict(),
            'points': self.points
        }
        cache.set(key, item, 3600)
        return item


class LeaderboardManager(models.Manager):
    pass


class Leaderboard(models.Model):
    user = models.CharField(max_length=100)
    points = models.IntegerField()
    position = models.IntegerField()
    position_change = models.IntegerField()
    month = models.IntegerField()
    year = models.IntegerField()
    last_subject_id = models.IntegerField()

    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = LeaderboardManager()

    class Meta:
        db_table = 'leaderboard'
        verbose_name = 'Leaderboard'

    def __unicode__(self):
        return "%s, %d pts" % (self.user, self.points)

    def to_dict(self):
        return {
            'user': User().get_by_name(self.user).to_dict(),
            'points': self.points,
            'position': self.position,
            'position_change': self.position_change,
            'month': self.month,
            'year': self.year
        }


class SaveStateManager(models.Manager):
    def get_by_k(self, key):
        try:
            return self.filter(k=key).get()
        except SaveState.DoesNotExist:
            return None


class SaveState(models.Model):
    k = models.CharField(max_length=255)
    v = models.CharField(max_length=255)

    objects = SaveStateManager()

    class Meta:
        db_table = 'save_state'
        verbose_name = 'SavedState'

    def __unicode__(self):
        return "%s=%s" % (self.k, self.v)


class NotifyEmail(models.Model):
    email = models.EmailField()
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notify_email'
        verbose_name = 'NotifyEmail'
