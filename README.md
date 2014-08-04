# Narcissa

Quantify yourself, free your data, and share it with the world.

# WTF is this?

Narcissa is a personal dashboard. It lets you connect to all your favorite APIs, scrape and store large amounts of data over long periods of time, and access that data in a form that makes it easy to show to people.

# Why did you build it?

I've been [trying to build](https://github.com/mplewis/locality) a personal dashboard on my own for years. Services come and go—[Google Latitude](https://support.google.com/gmm/answer/3001634?hl=en) was my jam until Google shut it down.

Anand Sharma built [April Zero](http://aprilzero.com/), the coolest personal dashboard I've ever seen. But it's not open source (yet), so I can't just spin one up for myself. And he probably uses different services and APIs to track his life than I do.

Shopify built [Dashing](https://github.com/Shopify/dashing), a beautifully simple way to plop arbitrary data into your own personal dashboard layout. We use it at [Punch Through Design](http://punchthrough.com/) to track Important Business Metrics™ such as Twitter and Facebook follower counts. But Dashing doesn't let you keep data over time—it just stores the last few points in any given category. And if the Dashing server restarts, you have to scrape all your data again.

I built Narcissa to combine the best bits of each one.

This framework:

* Stores data over long periods of time and saves it for later
* Can tie into all your favorite APIs with its dead simple plugin interface
* Makes it easy to query your data and display it with whatever frontend you want

# How does it work?

## The Basics

`python3 narcissa.py`

* Starts the web server
* Schedules scrapers for future runs
* Runs all scrapers once

## The Server

* Runs on Flask
* Receives SQL queries and runs them on the SQLite DB (read-only)
* Answers SQL queries with JSON data
* Sends CORS headers to make your client-side apps happy

## The Scrapers

* Run at set intervals
* Connects to whatever web APIs you want
* Stores their data into the SQLite DB

## The Frontend

* Probably static HTML/CSS/JS
* Connects to the Server and sends SQL queries
* Receives JSON data and poops it into the view controller or whatever
* This is whatever you want it to be, really. Go gorillas.

# oh god it's so un-Pythonic!

Yeah, yeah. I confess to my sins:

* `server.py` is started via `subprocess.Popen()` with a shell command
* Scraper plugins are read from file then `exec()`ed into being
* The plugin runner just catches all exceptions, prints them to the console, and keeps chugging
* Scrapers are single functions, "namespaced" by their name alone
* You have to use a stupid `globals()` hack to make pyflakes happy about using the `scheduler` global variable when you haven't declared it inside the scraper file

In response: I don't care. I liked [Dashing](https://github.com/Shopify/dashing) because it was dead simple to get started with its job API:

1. Poop some scraper code into `jobs/my_poopy_scraper.rb`
2. Enclose it in a `SCHEDULER.every` block
3. Use `send_event` to get data to the main thread
4. **There is no step 4**.

When I started using Dashing, I spent about 60 seconds learning how a Job worked, and then I started writing my own jobs from scratch. In other words: programming is fun again. Thanks for reminding me of that, Ruby folk. Sometimes the easy way out is the best way.

# Contributions

Bug reports, fixes, or features? Feel free to open an issue or pull request any time. You can also tweet me at [mplewis](http://twitter.com/mplewis) or email me at [matt@mplewis.com](mailto:matt@mplewis.com).

# License

Copyright (c) 2014 Matthew Lewis. Licensed under [the MIT License](http://opensource.org/licenses/MIT).

# That's it?

Nope. More info coming soon.
