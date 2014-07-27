scheduler = globals()['scheduler']


def scrape_test():
    import config
    print("Hello, I'm test.py.")
    print('DB_URI: %s' % config.DB_URI)
    print('Thanks!')


scheduler.every(3).seconds.do(scrape_test)
scrape_test()
