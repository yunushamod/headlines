import feedparser, json, urllib, urllib3, datetime
from flask import Flask, render_template, request, make_response

DEFAULTS = {
    'publication':'bbc',
    'city':'London, UK',
    'currency_from':"GBP",
    'currency_to':'USD',
}
WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=metrics&appid=bc35a7117d80446378cf53ba12f69b11'
CURRENCY_URL = 'https://openexchangerates.org/api/latest.json?app_id=40abb51cd45e4f2eb4c005eee5800bf5'
app = Flask(__name__)
RSS_FEEDS = {
    'bbc':'https://feeds.bbci.co.uk/news/rss.xml',
    'cnn': 'http://rss.cnn.com/rss/edition.rss',
    'fox': 'http://feeds.foxnews.com/foxnews/latest',
    'iol': 'http://www.iol.co.za/cmlink/1.640',
}

def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULTS[key]

@app.route('/')
def home():
    # get customized headlines, based on user input or default
    publication = get_value_with_fallback('publication')
    articles = get_news(publication)
    city = get_value_with_fallback('city')
    weather = get_weather(city)
    # get customized currency based on user input or default
    currency_from = get_value_with_fallback('currency_from')
    currency_to = get_value_with_fallback('currency_to')
    rate, currencies = get_rate(currency_from, currency_to)
    response = make_response(render_template('home.html', articles=articles,publication=publication, weather=weather,
    currency_from=currency_from, currency_to=currency_to, 
    rate=rate, currencies=sorted(currencies)))
    expires = datetime.datetime.now() + datetime.timedelta(days=365) # Meaning it's going to expire in 365 days(1 year)
    response.set_cookie('publication', publication, expires=expires) # set_cookie(name of cookie, value, expiry_date)
    response.set_cookie('city', city, expires=expires)
    response.set_cookie('currency_from', currency_from, expires=expires)
    response.set_cookie('currency_to', currency_to, expires=expires)
    return response

def get_news(query):
    if not query or query.lower() not in RSS_FEEDS:
        publication = DEFAULTS['publication']
    else:
        publication = query.lower()
    feed = feedparser.parse(RSS_FEEDS[publication])
    #weather = get_weather('London, UK')
    feed_articles = feed['entries']
    return feed_articles

def get_weather(query):
    query = urllib.parse.quote(query)
    url = WEATHER_URL.format(query)
    data = urllib.request.urlopen(url).read()
    parsed = json.loads(data)
    weather = None
    if parsed.get('weather'):
        weather = {'description': parsed['weather'][0]['description'],
        'temperature': parsed['main']['temp'],
        'city':parsed['name'],
        'country':parsed['sys']['country']}
    return weather

def get_rate(frm, to):
    all_currency=urllib.request.urlopen(CURRENCY_URL).read()
    parsed = json.loads(all_currency).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return (to_rate/frm_rate, parsed.keys())

if __name__ == '__main__':
    app.run(port=5000, debug=True)
