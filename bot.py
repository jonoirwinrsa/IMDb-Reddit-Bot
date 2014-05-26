#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

#===============
# Python Script for getting info from IMDb links
#  By /u/zd9
#
# Written in Python 2.7.6
#===============

import praw
import time  # for sleep
import signal  # for setting up signal handler and signal constant
import imdb
import sys
import re
import requests

# pull in onboard data and establish connection
version = 1.0

user_agent = ('IMBBot/v' + str(version) + ' by /u/zd9')
reddit = praw.Reddit(user_agent=user_agent)
reddit.login(username=sys.argv[1], password=sys.argv[2])
ia = imdb.IMDb(accessSystem='http', adultSearch=0)

keep_on = True


def kill_handler(sig, frame):
    global keep_on
    keep_on = False
signal.signal(signal.SIGUSR1, kill_handler)


def get_imdb_data(imdb_id):
    if (imdb_id[0] + imdb_id[1] == 'tt'):
        movies = ia.search_movie(imdb_id)
        movie = movies[0]
        ia.update(movie)
        return(movie)

    elif (imdb_id[0] + imdb_id[1] == 'ch'):
        characters = ia.search_character(imdb_id)
        character = characters[0]
        ia.update(character)
        return(character)

    elif (imdb_id[0] + imdb_id[1] == 'nm'):
        names = ia.search_person(imdb_id)
        name = names[0]
        ia.update(name)
        return(name)
    else:
        return('No Data')


while (keep_on):
    try:

        print("running...")
        # pull comments
        #subreddit_comments = reddit.get_comments('all')
        # for debug
        subreddit_comments = reddit.get_submission(submission_id="24fduc")

        all_done = reddit.get_submission(submission_id='24f9ig')
        already_done = all_done.comments
        done = ""
        done_new = ""
        banned_subreddits = []
        user_blacklist = []
        for comment in already_done:
            if not hasattr(comment, 'body'):
                continue
            else:
                done = done + "\n" + comment.body

        for comment in subreddit_comments.comments:
            if (comment.subreddit not in banned_subreddits) or (comment.author.name not in user_blacklist):
                pattern1 = re.compile("http://www\.imdb\.com/(?:character/|title/|name/)(?P<id1>ch|tt|nm)(?P<id2>\d{7})/")
                match = pattern1.search(comment.body)
                if not match:
                    continue

                if (match and comment.id not in already_done):
                    imdb = "".join(match.group('id1', 'id2'))

                    info = get_imdb_data(imdb)

                    dl = [d['name'] for d in info['director']]
                    pl = [p['name'] for p in info['producer']]
                    cl = [c['name'] for c in info['cast'][0:10]]
                    director = ', '.join(dl)
                    producer = ', '.join(pl)
                    cast = ', '.join(cl)
                    genre = ', '.join(info['genres'])

                    comment.reply('***[' + info['long imdb canonical title'] + '](' + match.group(0) + ')***\n\n'
                     + '\n\n**IMDB Rating:** ' + str(info['rating']) + '/10\n\n**Director(s):** ' + director
                     + '\n\n**Producer(s):** ' + producer
                     + '\n\n**Cast:** ' + cast
                     + '...\n\n**Plot:** ' + info['plot outline']
                     + '\n\n**Genre:** ' + genre
                     + '\n\n------------------------\n\n^^^[Questions/Comments/Suggestions?](http://www.reddit.com/message/compose/?to=zd9&subject=IMDbBot) ^^^Version ^^^' + str(version) + ' ^^^[Source](https://github.com/zd9/IMDb-Reddit-Bot)')

                    all_done.add_comment(comment.id)

    except requests.exceptions.HTTPError as err:
        if err.response.status_code in [502, 503, 504]:
            # these errors may only be temporary
            pass
        else:
            # assume other errors are fatal
            print str(err)
            print "Terminating"
    time.sleep(5)
