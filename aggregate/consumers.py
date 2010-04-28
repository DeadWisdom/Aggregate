import datetime, urllib2
from django.utils import simplejson

### Support ###
_consumers = {}
def consumer(name_or_func):
    """
    Consumer decorator, optionally takes a name.  This will register the
    function as a consumer, making it available for the source.
    """
    def outer(func):
        _consumers[name] = func
        return func
    
    if isinstance(name_or_func, basestring):
        name = name_or_func
        return outer
    else:
        name = name_or_func.func_name
        return outer(name_or_func)

def consume(source):
    return _consumers[source.consumer](source)

class SourceChoices(object):
    def __iter__(self):
        return ((k, k) for k in _consumers.keys())


import re
strip = "a an as at before but by for from is in into like of off on onto per since than the this that to up via with"
re_strip = re.compile(r'\b(%s)\b' % "|".join(strip.split()))
def slugify(str):
    str = re_strip.sub('', str)
    str = re.sub('[^\w\s-]', '', str).strip().lower()
    str = re.sub('\s+', '-', str)
    return str


### RSS Consumers ###
@consumer
def rss(source):
    print "[%s] %s - %s" % (source, source.consumer, source.options['url'])
    import feedparser
    feed = feedparser.parse(urllib2.urlopen(source.options['url']).read())
    
    #source.entry_set.all().delete()
    for entry in feed['entries']:
        print "    entry -", entry['id']
        source.entry(
            key = entry['id'],
            link = entry['link'],
            title = entry['title'],
            created = datetime.datetime(*entry['updated_parsed'][0:6]),
            body = entry['summary'],
            data = entry,
        )

### Reddit ###
@consumer
def reddit(source):
    import feedparser
    
    r = source.options.get('r', None)
    if r is None:
        url = "http://www.reddit.com/.rss"
    else:
        url = "http://www.reddit.com/r/%s/.rss" % r
    
    feed = feedparser.parse(urllib2.urlopen(url).read())

    source.entry_set.all().delete()     # Clear existing entries so we have the right order.
    for i, entry in enumerate(feed['entries']):

        m = re.search(r'submitted by <a.*?>(.*?)</a>', entry['summary'])
        if m:
            username = m.group(1).strip()
        else:
            username = "?"
        
        m = re.search(r'\[(\d+) comments\]', entry['summary'])
        if m:
            comments = m.group(1)
        else:
            comments = "?"
        
        m = re.search(r'\<a href="([^"]*?)"\>\[link\]\<\/a\>', entry['summary'])
        if m:
            link = m.group(1)
        else:
            link = "?"
        
        source.entry(
            key = entry['id'],
            link = link,
            title = entry['title'],
            created = datetime.datetime(*entry['updated_parsed'][0:6]),
            body = entry['summary'],
            data = dict(
                username = username,
                comments = comments,
                order = i,
            ),
        )

### Twitter ###
TWITTER_DATETIME = '%a %b %d %H:%M:%S +0000 %Y'

def process_timeline(source, timeline):
    if timeline:
        source.entry_set.all().delete()
        
    for status in timeline:
        source.entry(
            key = status.id,
            link = "http://twitter.com/%s/status/%s" % (status.user.screen_name, status.id),
            title = status.text,
            body = status.text,
            hidden = status.in_reply_to_screen_name,
            data = dict(
                screen_name = status.user.screen_name,
                name = status.user.name,
                icon = status.user.profile_image_url,
                created = datetime.datetime.strptime(status.created_at, TWITTER_DATETIME) - datetime.timedelta(hours=5),
            )
        )
        
def get_green_twitter_api(**kw):
    import twitter
    twitter.Api._urllib = urllib2
    return twitter.Api(**kw)

@consumer
def twitter_user(source):
    api = get_green_twitter_api()
    
    latest = tuple(source.entry_set.all()[:1])
    if latest:
        timeline = api.GetUserTimeline(source.options, since_id=int(latest[0].key))
    else:
        timeline = api.GetUserTimeline(source.options, count=200)
    
    process_timeline(source, timeline)

@consumer
def twitter_friends(source):
    api = get_green_twitter_api(username=source.options['username'], password=source.options['password'])
    
    latest = tuple(source.entry_set.all()[:1])
    if latest:
        timeline = api.GetFriendsTimeline(since_id=int(latest[0].key))
    else:
        timeline = api.GetFriendsTimeline(count=200)
    
    process_timeline(source, timeline)


### Google ###
def calendar_service(email=None, password=None):
    import gdata.calendar.service
    calendar_service = gdata.calendar.service.CalendarService()
    calendar_service.email = email
    calendar_service.password = password
    calendar_service.source = 'Tao-Personal-Homepage-1.0'
    calendar_service.ProgrammaticLogin()
    return calendar_service

def get_calendar_entries(source, feed):    
    events = []
    for event in feed.entry:
        start_time = event.when[0].start_time
        if 'T' in start_time:
            dt, tz = start_time.rsplit('-', 1)
            dt, _ = dt.rsplit('.', 1)
            start_time = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
        else:
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
        
        events.append(dict(
            id = event.id.text,
            link = event.link[0].href,
            title = event.title.text,
            slug = slugify(event.title.text),
            text = event.title.text,
            created = start_time,
            start_time = start_time,
            author = event.author[0].email.text,
            calendar = slugify(feed.title.text),
        ))
    return events

@consumer
def google_calendar(source):
    import gdata.calendar.service
    
    email = source.options.get('email')
    password = source.options.get('password')
    service = calendar_service(email, password)
    
    entries = []
    for resource in source.options.get('calendars', [email]):
        query = gdata.calendar.service.CalendarEventQuery(resource, 'private', 'full')
        query.start_min = datetime.datetime.now().strftime('%Y-%m-%d')
        query.start_max = (datetime.datetime.now() + datetime.timedelta(21)).strftime('%Y-%m-%d')
        entries += get_calendar_entries( source, service.CalendarQuery(query) )
    
    entries.sort(key=lambda x: x['start_time'])
    
    source.clear()
    for e in entries:
        source.set(e)

@consumer
def gmail(source):
    import feedparser
    
    pword_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    pword_manager.add_password(None, 'https://mail.google.com/mail/feed/atom/', source.options['username'], source.options['password'])

    authentication_handler = urllib2.HTTPBasicAuthHandler(pword_manager)
    urlopener = urllib2.build_opener(authentication_handler)
    urllib2.install_opener(urlopener) 
    
    feed = feedparser.parse(urllib2.urlopen('https://mail.google.com/mail/feed/atom/').read())
    
    source.clear();
    for entry in reversed(feed['entries']):
        source.set(
            id = entry['id'],
            link = entry['link'],
            title = entry['title'],
            summary = entry['summary'],
            author = entry['author'],
            slug = slugify(entry['title']),
            created = datetime.datetime(*entry['updated_parsed'][0:6]),
            text = entry['summary'],
        )