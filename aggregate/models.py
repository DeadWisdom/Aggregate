import re, datetime, cPickle, threading
import feedparser
import consumers

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from yamlfield import YAMLField
from picklefield import PickledObjectField
from utils import ago


class Source(models.Model):
    name = models.SlugField()
    slug = models.SlugField()
    consumer = models.SlugField(choices=consumers.SourceChoices())
    link = models.URLField(blank=True)
    user = models.ForeignKey(User, blank=True, null=True)
    options = YAMLField(help_text="(YAML options for the consumer)", blank=True, null=True)
    
    updated = models.DateTimeField(blank=True, null=True)
    updates = models.PositiveIntegerField(default=0)
    updating = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.name
    
    def status(self):
        if self.updating:
            return "updating"
        if self.updated is None:
            return "never updated"
        if self.is_stale:
            return "stale"
        return "updated %s" % ago(self.updated)
        
    def is_stale(self, version=None):
        """
        Check if the source is "stale", based on the last update and
        settings.AGGREGATE_STALE.
        """
        if self.updated is None:
            return True
        else:
            return self.updated < datetime.datetime.now() - datetime.timedelta(seconds=settings.AGGREGATE_STALE)
    
    def update(self, force=False):
        """
        Updates the current source, if it is stale or if *force* is True.
        
        Returns a thread, or None if it is not stale or if we are already
        updating.
        """
        if not force and (not self.is_stale() or self.updating):
            return None
        
        self.updating = True
        self.save()
        
        t = threading.Thread(target=self._update)
        t.setDaemon(True)
        t.start()
        
        return t
        
    def _update(self):
        consumers.consume(self)
        self.updated = datetime.datetime.now()
        self.updates += 1
        self.updating = False
        self.save()
    
    def template(self):
        return "aggregate/source/%s.html" % self.consumer

    def entry(self, **args):
        entry, _ = self.entry_set.get_or_create(key = args['key'])
        for k, v in args.items():
            setattr(entry, k, v)
        entry.save()
        return entry
        

class Entry(models.Model):
    source = models.ForeignKey(Source)
    key = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    hidden = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    found = models.DateTimeField(auto_now_add=True)
    data = PickledObjectField()
    
    class Meta:
        unique_together = (('key', 'source'),)
    
    def __unicode__(self):
        return self.key