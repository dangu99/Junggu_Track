import os
import cgi
import urllib

from decimal import Decimal

from google.appengine.api import users
from google.appengine.ext import ndb

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import app_identity

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GUESTBOOK_NAME = 'default_prodid'

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def count(iterable):
    return sum(1 for _ in iterable)


def division(x, y):
    try:
        result = x / float(y)
    except ZeroDivisionError:
        print "division by zero!"
        return 0
    return result


def percent(x, y):
    try:
        x = float(x)
        y = float(y)
        result = '{0:.2f}'.format((x / y* 100))
    except ZeroDivisionError:
        print "division by zero!"
        return 0
    return result


def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)


class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    transiddb = ndb.StringProperty(indexed=False)
    gaiddb = ndb.StringProperty(indexed=False)
    idfadb = ndb.StringProperty(indexed=False)
    method = ndb.StringProperty(indexed=False)
    platform = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    rewardid = ndb.StringProperty(indexed=False)
    dev_id = ndb.StringProperty(indexed=False)
    amt = ndb.StringProperty(indexed=False)
    currency = ndb.StringProperty(indexed=False)
    verifier = ndb.StringProperty(indexed=False)


class MainPage(webapp2.RequestHandler):

    def get(self):

        # Fetch query
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)
        greetingAll = greetings_query.fetch(1000000)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        # Counter
        clickCountAC = count(p for p in greetingAll if p.method == 'Click' and p.platform == 'AdColony')
        installCountAC = count(p for p in greetingAll if p.method == 'Install' and p.platform == 'AdColony')
        cvrAC = percent(installCountAC, clickCountAC)

        clickCountOR = count(p for p in greetingAll if p.method == 'Click' and p.platform == 'Opera Response')
        installCountOR = count(p for p in greetingAll if p.method == 'Install' and p.platform == 'Opera Response')
        cvrOR = percent(installCountOR, clickCountOR)

        # Display on Web
        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
            'clickCountAC': clickCountAC,
            'installCountAC': installCountAC,
            'cvrAC': cvrAC,
            'clickCountOR': clickCountOR,
            'installCountOR': installCountOR,
            'cvrOR': cvrOR,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class ClickTrack(webapp2.RequestHandler):

    def get(self):
        # Get parameter value
        guestbook_name = self.request.get('guestbook_name')
        junggutid = self.request.get('transid')
        gaid = self.request.get('gaid')
        idfa = self.request.get('idfa')

        # Input DB
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.method = 'Click'
        greeting.content = self.request.get('guestbook_name')
        greeting.transiddb = self.request.get('transid')
        greeting.gaiddb = self.request.get('gaid')
        greeting.idfadb = self.request.get('idfa')

        if greeting.transiddb:
            greeting.platform = 'Opera Response'
        else:
            greeting.platform = 'AdColony'

        greeting.put()

        # Redirection with the referrer
        referrer = 'junggu_transid=%(1)s&gaid=%(2)s&idfa=%(3)s&prod_id=%(4)s' % {"1" : junggutid, "2" : gaid, "3" : idfa, "4" : guestbook_name}
        self.response.write(referrer)
        referrer_params = {'referrer': referrer}
        self.redirect(str('market://details?id=' + guestbook_name + '&' + urllib.urlencode(referrer_params)), True)

       
class InstallTrack(webapp2.RequestHandler):

    def get(self):
        # Get parameter value
        guestbook_name = self.request.get('guestbook_name')
        junggutid = self.request.get('transid')
        gaid = self.request.get('gaid')
        idfa = self.request.get('idfa')

        # Input DB
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.method = 'Install'
        greeting.content = self.request.get('guestbook_name')
        greeting.transiddb = self.request.get('transid')
        greeting.gaiddb = self.request.get('gaid')
        greeting.idfadb = self.request.get('idfa')

        if greeting.transiddb:
            greeting.platform = 'Opera Response'
        else:
            greeting.platform = 'AdColony'

        greeting.put()

        # Postback
        if junggutid:
            postback = 'https://adcolony.go2cloud.org/aff_lsr?transaction_id=%(1)s' % {"1" : junggutid}
        else:
            postback = 'https://cpa.adcolony.com/on_user_action?api_key=75fPJmPa5MaW8h3DFjpFeGG9n8atxFv4&product_id=%(1)s&raw_advertising_id=%(2)s&google_ad_id=%(3)s' % {"1" : guestbook_name, "2" : idfa, "3" : gaid}

        self.redirect(str(postback), True)


class RewardTrack(webapp2.RequestHandler):

    def get(self):
        # Get parameter value
        guestbook_name = self.request.get('guestbook_name')
        rewardid = self.request.get('id')
        dev_id = self.request.get('uid')
        amt = self.request.get('amount')
        currency = self.request.get('currency')
        verifier = self.request.get('verifier')

        # Input DB
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.method = 'Reward'
        greeting.content = self.request.get('guestbook_name')
        greeting.rewardid = self.request.get('id')
        greeting.dev_id = self.request.get('uid')
        greeting.amt = self.request.get('amount')
        greeting.currency = self.request.get('currency')
        greeting.verifier = self.request.get('verifier')

        greeting.put()


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/click', ClickTrack),
    ('/install', InstallTrack),
    ('/reward', RewardTrack),
], debug=True)