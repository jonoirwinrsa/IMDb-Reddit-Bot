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
    try:
        if (imdb_id[0] + imdb_id[1] == 'tt'):
            movies = ia.search_movie(imdb_id)
            movie = movies[0]
            ia.update(movie)
            #for debug
            #print('found')
            return(movie)

        elif (imdb_id[0] + imdb_id[1] == 'nm'):
            names = ia.search_person(imdb_id)
            name = names[0]
            ia.update(name)
            #for debug
            #print('found')
            return(name)

    except IndexError:
        #for debug
        #print('not found')
        return('No Data')


def reply(type, info):
    ml = ''.join(m)

    if (type == 'tt'):
        dl = [d['name'] for d in info['director']] if (len(info['director']) > 1) else [info['director'][0]['name']] if (len(info['director']) == 1) else ['None']
        pl = [p['name'] for p in info['producer']] if (len(info['producer']) > 1) else [info['producer'][0]['name']] if (len(info['producer']) == 1) else ['None']
        cl = [c['name'] for c in info['cast'][0:10]] if (len(info['cast']) > 1) else [info['cast'][0]['name']] if (len(info['cast']) == 1) else ['None']
        director = ', '.join(dl) if (len(dl) < 10) else ', '.join(dl) + '...'
        producer = ', '.join(pl) if (len(pl) < 10) else ', '.join(pl) + '...'
        cast = ', '.join(cl) if (len(cl) < 10) else ', '.join(cl) + '...'
        genre = ', '.join(info['genres'])

        com = ('***[' + info['long imdb canonical title'] + '](http://imdb.com/' + ml + ')***\n\n'
         + '\n\n**IMDB Rating:** ' + str(info['rating']) + '/10\n\n**Director(s):** ' + director
         + '\n\n**Producer(s):** ' + producer
         + '\n\n**Cast:** ' + cast
         + '\n\n**Synopsis:** ' + info['plot outline']
         + '\n\n**Genre:** ' + genre)

        return(com)

    elif (type == 'nm'):
        dl = [str(d.get('title')) for d in info.get('director')[0:10]] if info.get('director') is not None else ['None']
        director = ', '.join(dl) if (len(dl) < 10) else ', '.join(dl) + '...'
        pl = [str(p.get('title')) for p in info.get('producer')[0:10]] if info.get('producer') is not None else ['None']
        producer = ', '.join(pl) if (len(pl) < 10) else ', '.join(pl) + '...'
        wl = [str(w.get('title')) for w in info.get('writer')[0:10]] if info.get('writer') is not None else ['None']
        writer = ', '.join(wl) if (len(wl) < 10) else ', '.join(wl) + '...'
        al = [str(a.get('title')) for a in info.get('actor')[0:10]] if info.get('actor') is not None else ['None']
        actor = ', '.join(al) if (len(al) < 10) else ', '.join(al) + '...'

        com = ('***[' + info['long imdb canonical name'] + '](http://imdb.com/' + ml + ')***\n\n'
         + '\n\n**Born:** ' + str(info.get('birth date'))
         + '\n\n**Directed:** ' + director
         + '\n\n**Produced:** ' + producer
         + '\n\n**Wrote:** ' + writer
         + '\n\n**Acted in:** ' + actor)

        return(com)

    else:
        com = ''
        return(com)


while (keep_on):
    try:

        print("running...")
        # pull comments
        subreddit_comments = reddit.get_comments('all')
        # for debug
        #subreddit_comments = reddit.get_submission(submission_id="24fduc")

        all_done = reddit.get_submission(submission_id='24f9ig')
        already_done = all_done.comments
        done = ""
        done_new = ""
        banned_subreddits = ['AskHistorians', 'askscience', 'unitedkingdom', 'guns', 'WTF', 'xkcdfeed', 'funny', 'IAmA', 'conspiratard', 'gaming', 'Games', 'AdviceAnimals', 'tipofmytongue', 'science', 'malefashionadvice']
        user_blacklist = []
        for comment in already_done:
            if not hasattr(comment, 'body'):
                continue
            else:
                done = done + "\n" + comment.body

        for comment in subreddit_comments.comments:
            if (comment.subreddit not in banned_subreddits) or (comment.author.name not in user_blacklist):
                pattern1 = re.compile("http://www\.imdb\.com/(?:title/|name/)(?P<id1>tt|nm)(?P<id2>\d{7})/")
                match = pattern1.findall(comment.body)
                if not match:
                    continue

                if (match and comment.id not in already_done):
                    coms = []
                    for m in match:
                        imdb = "".join(m)

                        info = get_imdb_data(imdb)

                        if (info == 'No Data'):
                            continue

                        else:
                            com = reply(m[0], info)
                            if (com == ''):
                                continue
                            else:
                                coms.append(com)
                    try:
                        if (len(coms) > 0):
                            comment.reply('\n\n-----------------\n\n'.join(coms)
                            + '\n\n------------------------\n\n^^^[Questions/Comments/Suggestions?](http://www.reddit.com/message/compose/?to=zd9&subject=IMDbBot) ^^^Version ^^^'
                            + str(version) + ' ^^^[Source](https://github.com/zd9/IMDb-Reddit-Bot)')

                            all_done.add_comment(comment.id)
                        else:
                            continue
                    except (praw.errors.APIException, praw.errors.ClientException) as e:
                        print(str(e))

    except requests.exceptions.HTTPError as err:
        if err.response.status_code in [502, 503, 504]:
            # these errors may only be temporary
            pass
        else:
            # assume other errors are fatal
            print str(err)
            print "Terminating"
    time.sleep(5)
    #for debug
    #keep_on = False
