print("Hello, I'm test.py.")
print('DB_URI: %s' % config.DB_URI)


def scrape_test():
    print('Scrape Test')


schedule.every(3).seconds.do(scrape_test)
