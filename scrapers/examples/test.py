# This line keeps pyflakes from getting mad when it can't find the `scheduler`
# object declared in narcissa.py.
scheduler = globals()['scheduler']


# Write everything inside one giant function so that function can be scheduled
# for later execution.

# This function MUST be named uniquely so it doesn't interfere with other
# scrapers or Narcissa functions. One safe way to name functions is to use the
# scrape_ prefix with the filename of the scraper.

def scrape_test():
    """
    This scraper illustrates the following:
        * How to access Narcissa's config
        * How to store and access local config variables
        * How to schedule a scraper
        * How to run a scraper immediately
    """

    # Config usually comes first so the user sees it right away.

    MY_NAME = 'Lil B the Based God'

    # Imports usually come next.

    import config
    from datetime import datetime

    # Program logic goes here. Whatever you use in a normal Python script will
    # work as long as it's inside this function.

    class MyClass:
        def __init__(self):
            self.greeting = 'Hello!'

    def get_my_name():
        return MY_NAME

    c = MyClass()
    print(c.greeting + ' My name is ' + get_my_name())
    print('DB_URI: %s' % config.DB_URI)
    print('Right now: %s' % datetime.now())


# Schedule this task to run every 3 seconds.
# It will run immediately as well.
scheduler.every(3).seconds.do(scrape_test)
