# -*- coding: utf-8 -*-

from kik import KikError
import requests, json
from kik.messages import TextMessage, PictureMessage, SuggestedResponseKeyboard, TextResponse, \
    StartChattingMessage, ScanDataMessage, StickerMessage, VideoMessage, LinkMessage
import random
import threading
import time
#from kik_trivlib import categories
from gevent import select
from gevent import Greenlet
from gevent.pool import Pool
import gevent
import logging
from PIL import Image, ImageFont, ImageDraw
import os
import shutil
from bs4 import BeautifulSoup
import urllib
import urllib.request
import asyncio
import re
import yaml

good_e = [u"\U0001F600", u"\U0001F601", u"\U0001F603", u"\U0001F604", u"\U0001F60A", u"\U0001F60B", u"\U0001F60E",
           u"\U0001F642", u"\U0001F44C", u"\U0001F44D", u"\U0000270A", u"\U0000270C", u"\U0001F918", u"\U0001F525"]
winner_e = [u"\U0001F396", u"\U0001F3C6", u"\U0001F3C5", u"\U0001F947", u"\U0001F64C", u"\U0001F61B", u"\U0001F389",
            u"\U00002728"]
bad_e = [u"\U0001F44E", u"\U0001F605", u"\U0001F914", u"\U0001F928", u"\U0001F610", u"\U0001F611", u"\U0001F623",
         u"\U0001F625", u"\U0001F62B", u"\U0001F634", u"\U0001F612", u"\U0001F613", u"\U0001F614", u"\U0001F615",
         u"\U0001F632", u"\U00002639", u"\U0001F641", u"\U0001F61E", u"\U0001F616", u"\U0001F61F", u"\U0001F622",
         u"\U0001F62D", u"\U0001F626"]
sure = ["Great!", "Cool!", "Nice!", "Awesome!", "Neat!", "Alright!", "Swell!"]
no_thanks = ["Very well, carry on!", "Ok, come again!", "See you next time!", "Thanks for playing!"]
greet = ["Hello, {}!", "Greetings, {}!", "Hi, {}!", "Nice to meet you, {}!", "Welcome, {}!", "Pleasure to see you, {}!",
         "Howdy {}!", "Well if it isn't {}!", "{}!"]
miss1 = ["Shoot,", "Uh oh,", "Hmm,", "Darn,", "Huh,"]
miss2 = ["that's not in there!", "that wasn't it!", "you'll get it!", "better luck next time!"]


def logprint(msg, *args):
    logging.info(msg)
    for i in args:
        logging.info(str(i))
    print(msg, *args)

class Hangman():
    kik = None
    list_of_chatids = []
    winners = []
    responses = [TextResponse("Used Letters"), TextResponse("Players"), TextResponse("Scoreboard"),
                 TextResponse("Display"), TextResponse("End Game")]

    def __init__(self):
        self.session_chatid = ""
        self.used_abcs = ""
        self.slots = []
        self.game_status = False
        self.cat_chosen = False
        self.chosen_cat = ""
        self.game_mode = ""
        self.multi_mode = ""
        self.list_of_chatusers = []
        self.list_of_availables = []
        self.list_of_threadplayers = []
        self.catch_custom_phrase = False
        self.custom_chooser = ""
        self.user_list = []
        self.comp_points = {}
        self.turn = 0
        self.game_single_user = None
        self.attempt_num = 6
        self.question = ""
        self.answer = ""
        self.answer_partitions = []
        self.check = False
        self.search_for_players = False
        self.all_players_ready = False
        self.progress_pic = 0
        self.answer_url = ""
        self.LB_updated = False

        self.LB_name = ""
        self.LB_single_wins = 0
        self.LB_single_loss = 0
        self.LB_mult_comp_wins = 0
        self.LB_mult_comp_loss = 0
        self.LB_mult_coop_wins = 0
        self.LB_mult_coop_loss = 0

    def jsondumpLB(self):
        return {
            "LB_name": self.LB_name,
            "LB_single_wins": self.LB_single_wins,
            "LB_single_loss": self.LB_single_loss,
            "LB_mult_comp_wins": self.LB_mult_comp_wins,
            "LB_mult_comp_loss": self.LB_mult_comp_loss,
            "LB_mult_coop_wins": self.LB_mult_coop_wins,
            "LB_mult_coop_loss": self.LB_mult_coop_loss
        }

    def jsondump(self):
        return {"session_chatid": self.session_chatid,
                "used_abcs": self.used_abcs,
                "slots": self.slots,
                "game_status": self.game_status,
                "cat_chosen": self.cat_chosen,
                "chosen_cat": self.chosen_cat,
                "game_mode": self.game_mode,
                "multi_mode": self.multi_mode,
                "list_of_chatusers": self.list_of_chatusers,
                "list_of_availables": self.list_of_availables,
                "list_of_threadplayers": self.list_of_threadplayers,
                "catch_custom_phrase": self.catch_custom_phrase,
                "custom_chooser": self.custom_chooser,
                "user_list": self.user_list,
                "comp_points": self.comp_points,
                "turn": self.turn,
                "game_single_user": self.game_single_user,
                "attempt_num": self.attempt_num,
                "question": self.question,
                "answer": self.answer,
                "answer_partitions": self.answer_partitions,
                "check": self.check,
                "search_for_players": self.search_for_players,
                "all_players_ready": self.all_players_ready,
                "progress_pic": self.progress_pic,
                "answer_url": self.answer_url,
                "LB_updated": self.LB_updated
        }

    def loadLBfromDB(self, dic):
        self.LB_name = dic["LB_name"]
        self.LB_single_wins = dic["LB_single_wins"]
        self.LB_single_loss = dic["LB_single_loss"]
        self.LB_mult_comp_wins = dic["LB_mult_comp_wins"]
        self.LB_mult_comp_loss = dic["LB_mult_comp_loss"]
        self.LB_mult_coop_wins = dic["LB_mult_coop_wins"]
        self.LB_mult_coop_loss = dic["LB_mult_coop_loss"]

    def loadFromDB(self, dic):
        self.session_chatid = dic["session_chatid"]
        self.used_abcs = dic["used_abcs"]
        self.slots = dic["slots"]
        self.game_status = dic["game_status"]
        self.cat_chosen = dic["cat_chosen"]
        self.chosen_cat = dic["chosen_cat"]
        self.game_mode = dic["game_mode"]
        self.multi_mode = dic["multi_mode"]
        self.list_of_chatusers = dic["list_of_chatusers"]
        self.list_of_availables = dic["list_of_availables"]
        self.list_of_threadplayers = dic["list_of_threadplayers"]
        self.catch_custom_phrase = dic["catch_custom_phrase"]
        self.custom_chooser = dic["custom_chooser"]
        self.user_list = dic["user_list"]
        self.comp_points = dic["comp_points"]
        self.turn = dic["turn"]
        self.game_single_user = dic["game_single_user"]
        self.attempt_num = dic["attempt_num"]
        self.question = dic["question"]
        self.answer = dic["answer"]
        self.answer_partitions = dic["answer_partitions"]
        self.check = dic["check"]
        self.search_for_players = dic["search_for_players"]
        self.all_players_ready = dic["all_players_ready"]
        self.progress_pic = dic["progress_pic"]
        self.answer_url = dic["answer_url"]
        self.LB_updated = dic["LB_updated"]

    def run(self):
        logprint("Running thread...")
        self.initiateSession(self.messageObj)
        logprint("...Ending thread")

    def resetThread(self):
        self.thread = threading.Thread(target=self.run)

    def setQA(self, loop, categories):
        randkey = random.randrange(len(categories[self.chosen_cat]))

        for i, key in enumerate(categories[self.chosen_cat].keys()):
            if i == randkey:
                self.question = key
                break

        randvalue = random.randrange(len(categories[self.chosen_cat][self.question]))
        self.answer = categories[self.chosen_cat][self.question][randvalue]
        self.answer = self.answer.strip()
        
        details = ""
        if self.answer.find("_") != -1:
            details = self.answer.split("_")[0] + " "
            self.answer = self.answer.split("_")[1]

        # asyncio.set_event_loop(loop)
        # loop.run_until_complete(self.getKikPicMessage(self.answer, None))
        self.confirmImgGrab(loop, details)


    def confirmImgGrab(self, loop, details):
        asyncio.set_event_loop(loop)
        if self.chosen_cat in ["geography", "history"]:
            logprint("Not funny dude")
            adj = ""
        else: 
            adj = " funny" if random.randrange(2) == 0 else ""
        loop.run_until_complete(self.getKikPicMessage(details + self.answer + adj, loop))

    def task(self, pid):
        """
        Some non-deterministic task
        """
        gevent.sleep(random.randint(0, 2) * 1)
        logprint('Task %s done' % pid)

    def synchronous(self):
        for i in range(1, 10):
            self.task(i)

    def asynchronous(self):
        threads = [gevent.spawn(self.task, i) for i in range(10)]
        gevent.joinall(threads)

    def thr(self, n):
        logprint("Start greenlet")
        gevent.sleep(n)
        logprint("End greenlet")

    #pool = Pool(100)

    def initiateSession(self, message):
        with open("kik_library.yml") as lib:
            categories = yaml.safe_load(lib)

        response_messages = []

        self.session_chatid = message.chat_id
        try:

            # logprint('Synchronous:')
            # self.synchronous()
            #
            # logprint('Asynchronous:')
            # self.asynchronous()
            #logprint("Thread ID: ", self.threadID)


            if self.game_mode == "single" and message.from_user != self.game_single_user:
                logprint("Game mode is single and %s is not chosen(%s)" % (message.from_user, self.game_single_user))
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Woah, you're not {}".format(self.getName(self.game_single_user))
                ))
                #logprint("KIK SEND_MESSAGE")
                #Hangman.kik.send_messages(response_messages)
                return

            if self.catch_custom_phrase and isinstance(message, TextMessage):
                if message.from_user == self.custom_chooser:
                    if self.question == "":
                        self.question = message.body.title()
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            body="What will be the hidden phrase? (50 characters max. 12 characters max per word. "
                                 "Allowed characters: A-z, &, ., /, -, ', ,, [0-9])"
                        ))
                    else:
                        message_body = message.body
                        result, msg = self.customIsPhraseClean(message_body)
                        if result:
                            self.answer = message_body
                            self.catch_custom_phrase = False
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                body="Awesome! Game is ready!"
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Custom entries are set!"
                            ))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                body=msg
                            ))
                else:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Please wait, {} is creating the entry".format(self.getName(self.custom_chooser))
                    ))
                logprint("KIK SEND MESSAGE")
                Hangman.kik.send_messages(response_messages)
                return


            #user = Hangman.kik.get_user(message.from_user)
            list_of_chatusers = message.participants
            #TODO I called bot with no subscribers and it identified 3 players but only recognized me. Another player called bot and only identified 1 player and
            #recognized 1 player.
            logprint("People in the chat(%i): " % len(list_of_chatusers), ", ".join(list_of_chatusers)) 
            logprint("Length of user_list: %i" % len(self.user_list))
            if len(self.list_of_availables) == 0:
                for user in list_of_chatusers:
                    try:
                        logprint("Adding: " + user)
                        #logprint(Hangman.kik.get_user(user).first_name)
                        #self.user_list.append(Hangman.kik.get_user(user).first_name)
                        self.list_of_availables.append(user)
                    except KikError:
                        continue
            logprint("Available Players that are RECOGNIZED(%i)" % len(self.list_of_availables), ", ".join(self.user_list))


            if isinstance(message, StickerMessage) or isinstance(message, VideoMessage) \
                    or isinstance(message, LinkMessage) or isinstance(message, PictureMessage):
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="That's nice, {}".format(self.getName(message.from_user))
                ))

            elif isinstance(message, StartChattingMessage) or isinstance(message, ScanDataMessage):
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Hello, {}! " + good_e[random.randrange(len(good_e))] +
                         " I'm the Hangman Bot. Want to play?".format(self.getName(message.from_user)),
                    keyboards=[
                        SuggestedResponseKeyboard(responses=[TextResponse("Sure!"), TextResponse("No thanks!")])]))
            # Check if the user has sent a text message.
            elif isinstance(message, TextMessage):
                #self.deleteImages() #From previous game
                message_body = message.body.lower()
                logprint("CHAT_ID: %s" % self.session_chatid)
                logprint(message.from_user + " said: " + message.body)

                if self.specialMessage(message, response_messages):
                    a = 1/0

                if message_body in ["how to play", "used letters", "players", "scoreboard", "display", "end game"]:
                    if message_body == "how to play":
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="How to play:\nChoose a category, pick your game mode, and guess the letters of the "
                                 "term (or one word at a time) until you're all out of tries or you think you know the answer!\n\n"
                                 "Every game will grant players 6 attempts, because that's the number of limbs being counted."
                        ))
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Single Player\nA player can play solo, disallowing other players to interfere until the"
                                 " game is over or until the game expires.\n"
                                 "Multiplayer - Competitively\nA player will earn points based on the number of occurrences"
                                 " of unique letters in a term. Ending the game will grant 2 points, the score will"
                                 " determine the winner.\n"
                                 "Multiplayer - Cooperatively\nPlayers can play alongside each other without taking turns"
                                 " or taking points."
                        ))
                    elif message_body == "used letters":
                        if self.game_status:
                            if self.multi_mode == "comp":
                                user = self.list_of_availables[self.turn]
                            else:
                                user = message.from_user
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Used letters:\n{}".format(" ".join(sorted(self.used_abcs))
                                                                if len(self.used_abcs)!=0 else "<empty>"),
                                keyboards=self.keyboardOptions(user)
                            ))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Not in an active game!",
                                keyboards=self.keyboardOptions(message.from_user)
                            ))
                    elif message_body == "players":
                        if self.game_status:
                            if self.multi_mode == "comp":
                                user = self.list_of_availables[self.turn]
                            else:
                                user = message.from_user
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Players:\n{}".format("\n".join(self.getName(x) for x in self.list_of_availables)),
                                keyboards=self.keyboardOptions(user)
                            ))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Not in an active game!",
                                keyboards=self.keyboardOptions(message.from_user)
                            ))
                    elif message_body == "scoreboard":
                        if self.multi_mode == "comp" and self.game_status:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body=self.scoreboard(),
                                keyboards=self.keyboardOptions(self.list_of_availables[self.turn])
                            ))
                        elif self.multi_mode == "coop":
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Not playing competitively!",
                                keyboards=self.keyboardOptions(message.from_user)
                            ))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Not in a multiplayer game!",
                                keyboards=self.keyboardOptions(message.from_user)
                            ))
                    elif message_body == "display":
                        if self.game_status:
                            response_messages.append(PictureMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                pic_url=self.display_hangman(self.attempt_num)
                            ))
                            if self.multi_mode == "comp":
                                user = self.list_of_availables[self.turn]
                            else:
                                user = message.from_user
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body=self.display_slots(self.slots),
                                keyboards=self.keyboardOptions(user)
                            ))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Not in an active game!"
                            ))
                    elif message_body == "end game":
                        if self.game_status:
                            if self.game_mode == "single" and self.game_single_user == message.from_user:
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Ending game..."
                                ))
                                self.reset()
                                self.check = True
                            #elif self.multi_mode == "comp" and self.list_of_availables[self.turn] == message.from_user:
                            elif self.multi_mode == "comp":                               
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Game ended by %s..." % (self.getName(message.from_user),)
                                ))
                                self.reset()
                                self.check = True
                            elif self.multi_mode == "coop":
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Game ended by %s..." % (self.getName(message.from_user),)
                                ))
                                self.reset()
                                self.check = True
                            else:
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body="Only the active player can end the game",
                                    keyboards=self.keyboardOptions(self.list_of_availables[self.turn])
                                ))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Not in an active game!"
                            ))
                    else:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Invalid command"
                        ))

                elif (message_body == "sure!") and not self.game_status:
                    category_texts = [TextResponse(cat.title()) for cat in categories.keys()]
                    category_texts.append(TextResponse("Custom"))
                    category_texts.append(TextResponse("Random"))
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body=sure[random.randrange(len(sure))] + " " + good_e[random.randrange(len(good_e))] + " " +
                             "Which category would you like to play?",
                        keyboards=[SuggestedResponseKeyboard(responses=category_texts)]
                    ))

                elif (message_body == "no thanks!") and not self.game_status:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body=no_thanks[random.randrange(len(no_thanks))] + " " + good_e[random.randrange(len(good_e))]
                    ))

                elif ([i for i in categories.keys() if i == message_body] or message_body == "random"
                      or message_body == "custom") and not self.game_status:
                    if message_body != "custom":
                        if message_body == "random":
                            self.chosen_cat = list(categories.keys())[random.randrange(len(categories.keys()))]
                            #self.chosen_cat = list(categories.keys())[random.randrange(len(categories.keys()))]
                        else:
                            self.chosen_cat = message_body
                        self.cat_chosen = True
                        # self.setQA()
                        loop = asyncio.new_event_loop()
                        t = threading.Thread(target=self.setQA, args=(loop, categories))
                        t.start()

                        # response_messages.append(TextMessage(
                        #     to=message.from_user,
                        #     chat_id=message.chat_id,
                        #     body="Cool! Is this a single-player or multi-player game?",
                        #     keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Single-Player"),
                        #                                                     TextResponse("Multi-Player")])]
                        # ))
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body=sure[random.randrange(len(sure))] + " What game mode would you like to play?",
                            keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Single-Player"),
                                                                            TextResponse("Multi-Player / Cooperative"),
                                                                            TextResponse("Multi-Player / Competitive")])]
                        ))
                    else:
                        if len(self.list_of_availables) > 1:
                            self.catch_custom_phrase = True
                            self.custom_chooser = message.from_user
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Phrase is being created by %s..." % (self.getName(message.from_user),)
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                body="Hello %s, you're creaating the custom entry!\n"
                                     "What will be the description of your hidden phrase?" % (self.getName(message.from_user),)
                            ))
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Custom phrase requires more than 1 player!"
                            ))


                elif self.search_for_players and message.body.lower() == "count me in!":
                    if message.from_user not in self.list_of_threadplayers:
                        self.list_of_threadplayers.append(message.from_user)
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Player {}: {}".format(len(self.list_of_threadplayers),message.from_user),
                            keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Count me in!")])]
                        ))
                    else:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="You've already been counted {}".format(message.from_user),
                            keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Count me in!")])]
                        ))

                elif (message_body == "single-player" or self.game_mode == "single") and not self.game_status\
                        and self.cat_chosen:
                    self.game_mode = "single"
                    self.game_single_user = message.from_user
                    self.game_status = True
                    self.create_slots()

                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body="Good Luck!"
                    ))
                    response_messages.append(PictureMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        pic_url=self.display_hangman(self.attempt_num)
                    ))
                    response_messages.append(TextMessage(
                          to=message.from_user,
                          chat_id=message.chat_id,
                          body=self.display_slots(self.slots)
                    ))
                    # response_messages.append(PictureMessage(
                        # to=message.from_user,
                        # chat_id=message.chat_id,
                        # pic_url=self.hangmanImg(self.attempt_num, self.display_slots(self.slots), None)
                    # ))

                    # response_messages.append(TextMessage(
                    #     to=message.from_user,
                    #     chat_id=message.chat_id,
                    #     body="Guess a letter!",
                    #     keyboards=self.keyboardOptions(message.from_user)
                    # ))

                elif (message_body.split(" / ")[0] == "multi-player" or self.game_mode == "multi") \
                        and not self.game_status:
                    self.game_mode = "multi"

                    if len(self.list_of_availables) < 2:
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body="Need 2 players or more to play this game mode!"
                        ))
                        self.game_mode = ""  # Todo Maybe replace with reset_multiplayer()

                    elif message_body.split(" / ")[1] == "competitive":
                        self.beginMulti("comp", response_messages, message)
                        # if not self.all_players_ready:
                        #     self.list_of_threadplayers.append(message.from_user)
                        #     self.invitePlayers(response_messages, message)
                        # # else:
                        # #     self.beginMulti("comp", response_messages, message)

                    elif message_body.split(" / ")[1] == "cooperative":
                        self.beginMulti("coop", response_messages, message)
                        # if not self.all_players_ready:
                        #     self.list_of_threadplayers.append(message.from_user)
                        #     self.invitePlayers(response_messages, message)
                        # # else:
                        # #     self.beginMulti("coop", response_messages, message)


                    # elif len(self.list_of_availables) >= 2:
                    #     response_messages.append(TextMessage(
                    #         to=message.from_user,
                    #         chat_id=message.chat_id,
                    #         body="Would you like to play cooperatively or competitively with your friends?",
                    #         keyboards=[
                    #             SuggestedResponseKeyboard(responses=[TextResponse("Co-Op"), TextResponse("Competitive")])]
                    #     ))
                    #
                    # else:
                    #     response_messages.append(TextMessage(
                    #         to=message.from_user,
                    #         chat_id=message.chat_id,
                    #         body="Need 2 players or more to play this game mode!"
                    #     ))
                    #     self.game_mode = ""  # Todo Maybe replace with reset_multiplayer()





                elif self.game_status == True and self.game_mode == "single":
                    logprint("Selected Phrase: " + self.answer)
                    if len(message_body) == 1 and message_body != int:
                        if message_body not in self.used_abcs:
                            self.used_abcs += message_body
                            logprint("Used Letters: " + self.used_abcs)
                            if message_body in self.answer.lower():
                                msg = sure[random.randrange(len(sure))] + " You got one! " + \
                                      good_e[random.randrange(len(good_e))]
                                self.update_slots(None, message_body)
                                if not self.is_game_won(self.slots):
                                    # response_messages.append(TextMessage(
                                    #     to=message.from_user,
                                    #     chat_id=message.chat_id,
                                    #     body=sure[random.randrange(len(sure))] + " You got one! "
                                    #          + good_e[random.randrange(len(good_e))]
                                    # ))
                                    self.progress_pic += 1
                            else:
                                self.attempt_num -= 1
                                msg = miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))] + \
                                      " " + bad_e[random.randrange(len(bad_e))] + \
                                      " \n[" + str(self.attempt_num) + " attempts left]"
                                # response_messages.append(TextMessage(
                                #     to=message.from_user,
                                #     chat_id=message.chat_id,
                                #     body=miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))]
                                #          + " " + bad_e[random.randrange(len(bad_e))] +
                                #          " \n[" + str(self.attempt_num) + " attempts left]"
                                # ))
                            response_messages.append(PictureMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                pic_url=self.display_hangman(self.attempt_num)
                            ))
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body=msg + "\n\n" + self.display_slots(self.slots),
                                keyboards=self.keyboardOptions(self.game_single_user)
                            ))
                            # response_messages.append(PictureMessage(
                                # to=message.from_user,
                                # chat_id=message.chat_id,
                                # pic_url=self.hangmanImg(self.attempt_num, self.display_slots(self.slots), None)
                            # ))
                            if self.is_game_won(self.slots):
                                response_messages += self.game_won(message)
                                self.reset()
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Looks like you've already given that letter. Try another!",
                                keyboards=self.keyboardOptions(message.from_user)
                            ))
                    elif message_body in self.answer_partitions:
                        self.slots, null = self.update_slots(message_body, None)
                        response_messages.append(PictureMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            pic_url=self.display_hangman(self.attempt_num)
                        ))
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body=self.display_slots(self.slots),
                            keyboards=self.keyboardOptions(self.game_single_user)
                        ))
                        if self.is_game_won(self.slots):
                            response_messages += self.game_won(message)
                            self.reset()

                    elif message_body == self.answer.lower():
                        #SinglePlayer: Check if given message matches entire answer OR matches a word in the answer
                        self.slots, tmp = self.update_slots(message_body, None)
                        response_messages.append(PictureMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            pic_url=self.display_hangman(self.attempt_num)
                        ))
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body=self.display_slots(self.slots),
                            keyboards=self.keyboardOptions(self.game_single_user)
                        ))
                        # response_messages.append(PictureMessage(
                            # to=message.from_user,
                            # chat_id=message.chat_id,
                            # pic_url=self.hangmanImg(self.attempt_num, self.display_slots(self.slots), None)
                        # ))
                        if self.is_game_won(self.slots):
                            response_messages += self.game_won(message)
                            self.reset()
                    else:
                        #SinglePlayer: Given message is invalid or not correct
                        self.attempt_num -= 1
                        # response_messages.append(TextMessage(
                        #     to=message.from_user,
                        #     chat_id=message.chat_id,
                        #     body=miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))]
                        #                  + " " + bad_e[random.randrange(len(bad_e))] +
                        #                  " \n[" + str(self.attempt_num) + " attempts left]"
                        # ))
                        msg = miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))] + \
                              " " + bad_e[random.randrange(len(bad_e))] + \
                              " \n[" + str(self.attempt_num) + " attempts left]"
                        response_messages.append(PictureMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            pic_url=self.display_hangman(self.attempt_num)
                        ))
                        response_messages.append(TextMessage(
                            to=message.from_user,
                            chat_id=message.chat_id,
                            body=msg + "\n\n" + self.display_slots(self.slots),
                            keyboards=self.keyboardOptions(self.game_single_user)
                        ))
                    #Check if number of attempts are empty
                    if self.attempt_num == 0:
                        response_messages += self.game_lost(message)
                        self.reset()

                elif self.game_status == True and self.game_mode == "multi":
                    logprint("Selected Phrase: " + self.answer)
                    if self.multi_mode == "comp":
                        logprint("Game Mode: Competitive")
                        if message.from_user == self.list_of_availables[self.turn]:
                            if len(message_body) == 1 and message_body != int:
                                if message_body not in self.used_abcs:
                                    self.used_abcs += message_body
                                    logprint("Used Letters: " + self.used_abcs)
                                    if message_body in self.answer.lower():
                                        num_of_occurrances = self.update_slots(None, message_body)
                                        self.incrementScore(message.from_user, num_of_occurrances)
                                        msg = sure[random.randrange(len(sure))] + " You got one! " + \
                                              good_e[random.randrange(len(good_e))]
                                        if not self.is_game_won(self.slots):
                                            pass
                                            # response_messages.append(TextMessage(
                                            #     to=message.from_user,
                                            #     chat_id=message.chat_id,
                                            #     body=sure[random.randrange(len(sure))] + " You got one! "
                                            #  + good_e[random.randrange(len(good_e))]
                                            # ))

                                    else:
                                        self.attempt_num -= 1
                                        msg = miss1[random.randrange(len(miss1))] + " " + miss2[
                                            random.randrange(len(miss2))] + \
                                              " " + bad_e[random.randrange(len(bad_e))] + \
                                              " \n[" + str(self.attempt_num) + " attempts left]"
                                        # response_messages.append(TextMessage(
                                        #     to=message.from_user,
                                        #     chat_id=message.chat_id,
                                        #     body=miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))]
                                        #  + " " + bad_e[random.randrange(len(bad_e))] +
                                        #  " \n[" + str(self.attempt_num) + " attempts left]"
                                        # ))

                                        self.rotate_player()

                                    response_messages.append(PictureMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        pic_url=self.display_hangman(self.attempt_num)
                                    ))
                                    if self.attempt_num != 0:
                                        response_messages.append(TextMessage(
                                            to=message.from_user,
                                            chat_id=message.chat_id,
                                            body=msg + "\n\n" + self.display_slots(self.slots),
                                            keyboards=self.keyboardOptions(self.list_of_availables[self.turn])
                                        ))
                                    if self.is_game_won(self.slots):
                                        self.incrementScore(message.from_user, 1)
                                        response_messages += self.endScore(message)
                                        response_messages += self.game_won(message)
                                        self.reset()
                                else:
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="Looks like that letter has already been given. Try another!",
                                        keyboards=self.keyboardOptions(message.from_user)
                                    ))
                            elif message_body in self.answer_partitions:
                                self.slots, unique_occurrances = self.update_slots(message_body, None)
                                self.incrementScore(message.from_user, unique_occurrances)
                                response_messages.append(PictureMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    pic_url=self.display_hangman(self.attempt_num)
                                ))
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body=self.display_slots(self.slots),
                                    keyboards=self.keyboardOptions(message.from_user)
                                ))
                                if self.is_game_won(self.slots):
                                    self.incrementScore(message.from_user, 2)
                                    response_messages += self.endScore(message)
                                    response_messages += self.game_won(message)
                                    self.reset()
                            elif message_body == self.answer.lower():
                                #Check if given message matches answer
                                self.slots, unique_occurrances = self.update_slots(message_body, None)
                                self.incrementScore(message.from_user, unique_occurrances)
                                response_messages.append(PictureMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    pic_url=self.display_hangman(self.attempt_num)
                                ))
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body=self.display_slots(self.slots),
                                    keyboards=self.keyboardOptions(message.from_user)
                                ))
                                if self.is_game_won(self.slots):
                                    self.incrementScore(message.from_user, 2)
                                    response_messages += self.endScore(message)
                                    response_messages += self.game_won(message)
                                    self.reset()
                            else:
                                self.attempt_num -= 1
                                msg = sure[random.randrange(len(sure))] + " You got one! " + \
                                      good_e[random.randrange(len(good_e))]
                                # response_messages.append(TextMessage(
                                #     to=message.from_user,
                                #     chat_id=message.chat_id,
                                #     body=miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))]
                                #          + " " + bad_e[random.randrange(len(bad_e))] +
                                #          " \n[" + str(self.attempt_num) + " attempts left]"
                                # ))

                                self.rotate_player()

                                response_messages.append(PictureMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    pic_url=self.display_hangman(self.attempt_num)
                                ))
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body=msg + "\n\n" + self.display_slots(self.slots),
                                    keyboards=self.keyboardOptions(message.from_user)
                                ))
                            if self.attempt_num == 0:
                                response_messages += self.endScore(message)
                                response_messages += self.game_lost(message)
                                self.reset()
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Woah, you're not {}".format(self.getName(self.list_of_availables[self.turn])),
                                keyboards=self.keyboardOptions(self.list_of_availables[self.turn])
                            ))

                    else:
                        logprint("Game Mode: Co-Operative, Multi-mode: " + self.multi_mode)
                        #TODO this is new!
                        if message.from_user in self.list_of_availables:
                            if len(message_body) == 1 and message_body != int:
                                if message_body not in self.used_abcs:
                                    self.used_abcs += message_body
                                    logprint("Used Letters: " + self.used_abcs)
                                    if message_body in self.answer.lower():
                                        self.update_slots(None, message_body)
                                        msg = sure[random.randrange(len(sure))] + " You got one! " + \
                                              good_e[random.randrange(len(good_e))]
                                        if not self.is_game_won(self.slots):
                                            pass
                                            # response_messages.append(TextMessage(
                                            #     to=message.from_user,
                                            #     chat_id=message.chat_id,
                                            #     body=sure[random.randrange(len(sure))] + " You got one! "
                                            #  + good_e[random.randrange(len(good_e))]
                                            # ))

                                    else:
                                        self.attempt_num -= 1
                                        msg = miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))] + \
                                        " " + bad_e[random.randrange(len(bad_e))] + \
                                         " \n[" + str(self.attempt_num) + " attempts left]"
                                        # response_messages.append(TextMessage(
                                        #     to=message.from_user,
                                        #     chat_id=message.chat_id,
                                        #     body=miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))]
                                        #  + " " + bad_e[random.randrange(len(bad_e))] +
                                        #  " \n[" + str(self.attempt_num) + " attempts left]"
                                        # ))

                                    response_messages.append(PictureMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        pic_url=self.display_hangman(self.attempt_num)
                                    ))
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body=msg + "\n\n" + self.display_slots(self.slots),
                                        keyboards=self.keyboardOptions(message.from_user)
                                    ))
                                    if self.is_game_won(self.slots):
                                        response_messages += self.game_won(message)
                                        self.reset()
                                else:
                                    response_messages.append(TextMessage(
                                        to=message.from_user,
                                        chat_id=message.chat_id,
                                        body="Looks like that letter has already been given. Try another!",
                                        keyboards=self.keyboardOptions(message.from_user)                                   
                                    ))
                            elif message_body in self.answer_partitions:
                                self.slots, null = self.update_slots(message_body, None)
                                response_messages.append(PictureMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    pic_url=self.display_hangman(self.attempt_num)
                                ))
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body=self.display_slots(self.slots),
                                    keyboards=self.keyboardOptions(message.from_user)
                                ))
                                if self.is_game_won(self.slots):
                                    response_messages += self.game_won(message)
                                    self.reset()
                            elif message_body == self.answer.lower():
                                # Check if given message matches answer
                                self.slots, null = self.update_slots(message_body, None)
                                response_messages.append(PictureMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    pic_url=self.display_hangman(self.attempt_num)
                                ))
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body=self.display_slots(self.slots),
                                    keyboards=self.keyboardOptions(message.from_user)
                                ))
                                if self.is_game_won(self.slots):
                                    response_messages += self.game_won(message)
                                    self.reset()
                            else:
                                # User entered an integer, entered the wrong word, or failed to complete the entire word
                                self.attempt_num -= 1
                                msg = miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))] + \
                                " " + bad_e[random.randrange(len(bad_e))] + \
                                " \n[" + str(self.attempt_num) + " attempts left]"
                                # response_messages.append(TextMessage(
                                #     to=message.from_user,
                                #     chat_id=message.chat_id,
                                #     body=miss1[random.randrange(len(miss1))] + " " + miss2[random.randrange(len(miss2))]
                                #          + " " + bad_e[random.randrange(len(bad_e))] +
                                #          " \n[" + str(self.attempt_num) + " attempts left]"
                                # ))

                                response_messages.append(PictureMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    pic_url=self.display_hangman(self.attempt_num)
                                ))
                                response_messages.append(TextMessage(
                                    to=message.from_user,
                                    chat_id=message.chat_id,
                                    body=msg + "\n\n" + self.display_slots(self.slots),
                                    keyboards=self.keyboardOptions(message.from_user)
                                ))
                            if self.attempt_num == 0:
                                response_messages += self.game_lost(message)
                                self.reset()
                        else:
                            response_messages.append(TextMessage(
                                to=message.from_user,
                                chat_id=message.chat_id,
                                body="Game in session, {}!".format(message.from_user)
                            ))

                else:
                    response_messages.append(TextMessage(
                        to=message.from_user,
                        chat_id=message.chat_id,
                        body=(greet[random.randrange(len(greet))] + " How about a game of Hangman?").format(self.getName(message.from_user)),
                        keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Sure!"), TextResponse("No thanks!")])]
                    ))

            # If its not a text message, give them another chance to use the suggested responses
            else:
                response_messages.append(TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="That's nice, but what does that have to do with me?"
                ))

                # We're sending a batch of messages. We can send up to 25 messages at a time (with a limit of
                # 5 messages per user).
            logprint(response_messages)
            logprint("KIK SEND_MESSAGE")
            #Hangman.kik.send_messages(response_messages)

            #self.isGameOver(self.check)
        except ArithmeticError:
            logprint("Special Message activated")
        except Exception as e:
            self.reset()
            self.check = True
            logprint("Error in message processing: %s" % str(e))
            logging.error(e, exc_info=True)
            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Hi there, {}! Care to play Hangman?".format(message.from_user),
                keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Sure!"), TextResponse("No thanks!")])]))
            logprint(response_messages)
            logprint("KIK SEND_MESSAGE")
            #Hangman.kik.send_messages(response_messages)
        finally:
            new_response_messages = []
            try:
                Hangman.kik.send_messages(response_messages)
            except KikError as e:
                logprint("KikError in initiateSession: attempting to fix...")
                for i in response_messages:
                    if not isinstance(i, PictureMessage) and not isinstance(i, VideoMessage):
                        new_response_messages.append(i)
                    if len(new_response_messages) == 5:
                        break
                logprint(new_response_messages)                               
                Hangman.kik.send_messages(new_response_messages)

        return

    def customModeValidation(self):
        pass
        # from kik_sql import KikDB
        #
        # with KikDB() as kikdb:
        #     kikdb.cursor.execute(KikDB.query_custom_checkExist, (self.custom_chooser,))
        #     existance = tuple(kikdb.cursor.fetchone())
        #     if not existance[0]:
        #         logprint("Custom user doesn't exist, creating one")
        #         kikdb.cursor.execute(KikDB.query_userinfo_insert, (self.custom_chooser,))
        #     else:
        #         logprint("Deleting custom user")
        #         KikDB.mysqlExec(KikDB.query_custom_delete, (self.custom_chooser,))
        #         KikDB.mysql(KikDB.query_userinfo_insert, (self.custom_chooser,))
        #         result = leaderboardDB.cursor.fetchone()
        #         temp_user.loadLBfromDB(json.loads(result[0]))
        #         updateOnModes(outcome, temp_user)
        #         leaderboardDB.mysqlExec(KikDB.query_LB_update, (json.dumps(temp_user.jsondumpLB()), user))



    def customIsPhraseClean(self, message_body):
        if re.search("[^A-Za-z, /&]", message_body) is None:
            if len(message_body) > 50:
                return False, "Phrase is longer than 50 characters."

            words = re.split("[ ,&/]", message_body)
            for word in words:
                if len(word) > 12:
                    return False, "One of your words was longer than 12 characters."

            return True, ""
        else:
            return False, "Only letters and specified characters allowed."

    def specialMessage(self, message, response_messages):
        message_body = message.body.lower()
        if message_body in [":D", ":)", ":*", ":$"]:
            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body=message_body
            ))
            special = True
        else:
            special = False

        return special

    def beginMulti(self, mode, response_messages, message):
        if mode == "coop":
            self.multi_mode = "coop"
            self.game_status = True
            self.create_slots()
            
            tmp = ""
            for i, x in enumerate(self.list_of_availables):
                if i != len(self.list_of_availables)-1:
                    tmp += (x + ", ")
                else:
                    tmp = tmp[0:len(tmp)-2]
                    tmp += (" and " + x)
            
            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Good luck, {}!".format(tmp)
            ))
            response_messages.append(PictureMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                pic_url=self.display_hangman(self.attempt_num)
            ))
            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body=self.display_slots(self.slots)
            ))
            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Guess a letter!",
                keyboards=self.keyboardOptions(message.from_user)
            ))
        elif mode == "comp":
            self.multi_mode = "comp"
            self.game_status = True
            self.create_slots()
            self.determine_first_player()
            self.setScore()

            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="{}".format(" vs ".join(self.getName(x) for x in self.list_of_availables))
            ))
            response_messages.append(PictureMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                pic_url=self.display_hangman(self.attempt_num)
            ))
            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body=self.display_slots(self.slots)
            ))
            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Guess a letter, {}!".format(self.getName(self.list_of_availables[self.turn])),
                keyboards=self.keyboardOptions(self.list_of_availables[self.turn])
            ))
        else:
            logprint("Neither mode ; ending function")
            return

    def keyboardOptions(self, to):
        print("Supplying keyboard...")
        keyboardList = []
        responses = []
        responses.append(TextResponse("How to play"))
        responses.append(TextResponse("Used Letters"))
        responses.append(TextResponse("Players"))
        responses.append(TextResponse("Scoreboard"))
        responses.append(TextResponse("Display"))
        responses.append(TextResponse("End Game"))
        keyboard = SuggestedResponseKeyboard(responses=responses, to=to, hidden=True)
        keyboardList.append(keyboard)

        # if self.game_mode != "single":
            # lst = []
            # lst.append(TextResponse("How to play"))
            # lst.append(TextResponse("Used Letters"))
            # lst.append(TextResponse("Players"))
            # lst.append(TextResponse("Scoreboard"))
            # lst.append(TextResponse("Display"))
            # keyboard = SuggestedResponseKeyboard(responses=lst, hidden=True)
            # keyboardList.append(keyboard)

        return keyboardList

    def getName(self, user):
        try:
            name = Hangman.kik.get_user(user).first_name
        except KikError:
            name = user
        return name

    def has_num(self, s):
        return any(i.isdigit() for i in s)

    def determine_first_player(self):
        self.turn = random.randint(0, len(self.list_of_availables) - 1)

    def rotate_player(self):
        self.turn += 1
        if self.turn == len(self.list_of_availables):
            self.turn = 0

    def updateLeaderboard(self, message, outcome):

        def updateOnModes(outcome, temp_user):
            if outcome == "win":
                if self.game_mode == "single":
                    temp_user.LB_single_wins += 1
                    logprint("WON SINGLE: +1")
                elif self.game_mode == "multi":
                    if self.multi_mode == "comp":
                        if temp_user.LB_name in Hangman.winners:
                            temp_user.LB_mult_comp_wins += 1
                            logprint("WON COMP: +1")
                        else:
                            temp_user.LB_mult_comp_loss += 1
                            logprint("LOSS COMP: +1")
                    elif self.multi_mode == "coop":
                        temp_user.LB_mult_coop_wins += 1
                        logprint("WON COOP: +1")
            elif outcome == "lose":
                if self.game_mode == "single":
                    temp_user.LB_single_loss += 1
                    logprint("LOSS SINGLE: +1")
                elif self.game_mode == "multi":
                    if self.multi_mode == "comp":
                        if temp_user.LB_name in Hangman.winners:
                            temp_user.LB_mult_comp_wins += 1
                            logprint("WON COMP: +1")
                        else:
                            temp_user.LB_mult_comp_loss += 1
                            logprint("LOSS COMP: +1")
                    elif self.multi_mode == "coop":
                        temp_user.LB_mult_coop_loss += 1
                        logprint("LOSS COOP: +1")


        from kik_sql import KikDB
        #leaderboardDB = KikDB()
        try:
            with KikDB() as leaderboardDB:
                logprint("Updating leaderboard...")
                for user in self.list_of_availables:
                    if self.LB_updated:
                        logprint("Leaderboard has already been updated for %s" % (user,))
                        break
                    logprint("Updating info for %s" % (user,))
                    if self.game_mode == "single" and user != self.game_single_user:
                        continue

                    temp_user = Hangman()
                    leaderboardDB.cursor.execute(KikDB.query_LB_checkExist, (user,))
                    existance = tuple(leaderboardDB.cursor.fetchone())
                    if not existance[0]:
                        logprint("Leaderboard record doesn't exist. Creating one")
                        temp_user.LB_name = user
                        updateOnModes(outcome, temp_user)
                        leaderboardDB.mysqlExec(KikDB.query_LB_insert, (user, json.dumps(temp_user.jsondumpLB())))
                    else:
                        logprint("Leaderboard record exists")
                        leaderboardDB.mysqlExec(KikDB.query_LB_retrieve, (user,))
                        result = leaderboardDB.cursor.fetchone()
                        temp_user.loadLBfromDB(json.loads(result[0]))
                        updateOnModes(outcome, temp_user)
                        leaderboardDB.mysqlExec(KikDB.query_LB_update, (json.dumps(temp_user.jsondumpLB()), user))
                logprint("Leaderboard has been updated.")
        except Exception as e:
            logprint("Error updating leaderboard!", str(e))
            logging.error(e, exc_info=True)

        self.LB_updated = True



    def is_game_won(self, list_slots):
        return "__" not in list_slots

    def game_won(self, message):
        messages_to_send = []
        #messages_to_send += getKikPicMessage(self.answer, message)
        try:
            Type = self.answer_url.split("-SPLITMEPLS-")[0]
            imgurl = self.answer_url.split("-SPLITMEPLS-")[1]
            if Type == "gif":
                messages_to_send.append(VideoMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    video_url=imgurl,
                    loop=True,
                    autoplay=True,
                    muted=True
                ))
            else:
                messages_to_send.append(PictureMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    pic_url=imgurl
                ))
            logprint("Sending image with url: %s" % (imgurl,))
            if self.answer_url == "":
                raise Exception
        except:
            messages_to_send.clear()

        self.updateLeaderboard(message, "win")

        if self.multi_mode == "coop":
            winmsg = "Winners! " + winner_e[random.randrange(len(winner_e))] + " Care to play again?"
        elif self.game_mode == "single":
            winmsg = "You win! " + winner_e[random.randrange(len(winner_e))] + " Care to play again?"
        else:
            winmsg = "Play again?"

        messages_to_send.append(TextMessage(
            to=message.from_user,
            chat_id=message.chat_id,
            body=winmsg,
            keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Sure!"), TextResponse("No thanks!")])]
        ))
        self.check = True
        return messages_to_send

    def game_lost(self, message):
        messages_to_send = []

        try:
            Type = self.answer_url.split("-SPLITMEPLS-")[0]
            imgurl = self.answer_url.split("-SPLITMEPLS-")[1]
            if Type == "gif":
                messages_to_send.append(VideoMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    video_url=imgurl,
                    loop=True,
                    autoplay=True,
                    muted=True
                ))
            else:
                messages_to_send.append(PictureMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    pic_url=imgurl
                ))
            logprint("Sending image with url: %s" % (imgurl,))
            if self.answer_url == "":
                raise Exception
        except:
            messages_to_send.clear()

        self.updateLeaderboard(message, "lose")

        # messages_to_send.append(TextMessage(
        #     to=message.from_user,
        #     chat_id=message.chat_id,
        #     body="The answer was %s!" % (self.answer,)
        # ))
        if self.multi_mode == "comp":
            losemsg = "Play again?"
        else:
            losemsg = "You lose " + bad_e[random.randrange(len(bad_e))] + " Want to play again?"
        messages_to_send.append(TextMessage(
            to=message.from_user,
            chat_id=message.chat_id,
            body="The answer was %s!\n%s" % (self.answer, losemsg),
            keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Sure!"), TextResponse("No thanks!")])]
        ))
        self.check = True
        return messages_to_send

    def isGameOver(self, end):
        return end

    def reset(self):
        self.game_status = False
        self.game_single_user = None
        self.game_mode = ""
        self.cat_chosen = False
        self.chosen_cat = ""
        self.multi_mode = ""
        self.slots = []
        self.used_abcs = ""
        self.attempt_num = 6
        self.turn = 0
        self.comp_points = {}
        self.question = ""
        self.answer = ""
        self.answer_partitions = []
        self.list_of_threadplayers = []
        self.all_players_ready = False
        self.progress_pic = 0
        self.answer_url = ""
        self.LB_updated = False

    def create_slots(self):
        temp_word = ""
        for x in list(self.answer):
            if x != " ":
                if x == ",":
                    self.slots.append(", ")
                elif x == "'":
                    self.slots.append("'")
                elif x == "&":
                    self.slots.append(" & ")
                elif x == "/":
                    self.slots.append("/")
                elif x == ".":
                    self.slots.append(".")
                elif x == "-":
                    self.slots.append("-")
                elif x == ":":
                    self.slots.append(": ")
                elif x.isdigit():
                    self.slots.append(x)
                else:
                    temp_word += x
                    self.slots.append("__")
            else:
                self.answer_partitions.append(temp_word.lower())
                temp_word = ""
                self.slots.append("  ")
        self.answer_partitions.append(temp_word.lower())
        logprint("create_slots(): ", self.slots)

    def update_slots(self, phrase, letter):
        # if self.answer_url == "":
        #     logprint("Game is ON and image is not ready. Attempting to grab...")
        #     loop = asyncio.new_event_loop()
        #     t = threading.Thread(target=self.confirmImgGrab, args=(loop,))
        #     t.start()

        temp_slots = []
        if letter != None:
            for i, ltr in enumerate(self.answer):
                if ltr.isupper():
                    if letter == ltr.lower():
                        logprint("update_slots(): ", i)
                        self.slots[i] = letter.upper()
                else:
                    if letter == ltr:
                        logprint("update_slots(): ", i)
                        self.slots[i] = letter
            return 1

        if phrase != None:
            uniques_occurs = 0
            temp_slots = self.slots
            for ltr in phrase:
                print("Looking for %s(%s)" % (phrase, ltr))
                if ltr not in [x.lower() for x in temp_slots]:
                    print("Processing letter %s" % (ltr,))
                    uniques_occurs += 1
                    self.used_abcs += ltr
                    for i, ansLtr in enumerate(self.answer):
                        if ansLtr.lower() == ltr:
                            temp_slots[i] = ansLtr
                else:
                    print("Letter %s exists" % (ltr,))
            logprint("update_slots(): ", self.slots)
            return temp_slots, uniques_occurs

    def display_slots(self, list_slots):
        slots_string = ""
        if len(list_slots) == 0:
            raise Exception
            #return "Error"

        for i, x in enumerate(list_slots):
            slots_string += x
            if x == "__":
                slots_string += " "
            elif x == "  ":
                slots_string += "+"
            print("'" + slots_string + "'" + "(%s)" % (x,))
        #print(slots_string.split("+")[0] + " and " + slots_string.split("+")[1])
        #logprint("Length of slots: ", len(slots_string))
        split_slots = slots_string.split("+")
        print("Split Slots: " + str(split_slots))

        length = 0
        temp = ""
        first_word = True
        for i in range(len(split_slots)):
            if not first_word and split_slots[i].strip(" ")[0] == "_":
                print("Adding space")
                temp += " "
            if first_word:
                first_word = False

            print("Length of %s:%d" % (split_slots[i].strip(" "), len(split_slots[i].strip(" "))))
            length += len(split_slots[i].strip(" "))
            if length > 25:
                temp += ("\n" + split_slots[i].strip(" "))
                length = len(split_slots[i].strip(" "))
            else:
                temp += split_slots[i].strip(" ")
            if temp[len(temp)-1] == "_":
                temp += "   "
            else:
                temp += " "
            print("Temp: " + temp)
        slots_string = temp

        logprint("display_slots(): ", list_slots, " slots_string: ", slots_string)
        logprint("Question: " + self.question)
        question_string = ""
        if self.attempt_num != 0 and self.multi_mode == "comp":
            question_string += ("[Turn: {}]\n".format(self.getName(self.list_of_availables[self.turn])))
        question_string += self.question + "\n"

        return question_string + slots_string

    def display_hangman(self, num):
        hangman_pic = [
            "http://192.241.150.224/images/hangman_pics/hangman_6.png",
            "http://192.241.150.224/images/hangman_pics/hangman_5.png",
            "http://192.241.150.224/images/hangman_pics/hangman_4.png",
            "http://192.241.150.224/images/hangman_pics/hangman_3.png",
            "http://192.241.150.224/images/hangman_pics/hangman_2.png",
            "http://192.241.150.224/images/hangman_pics/hangman_1.png",
            "http://192.241.150.224/images/hangman_pics/hangman_0.png"]

        sequence_num = (len(hangman_pic) - 1) - num

        return hangman_pic[sequence_num]
	
    def topImg(self, text):
        topcanvas = (500, 75)
        im = Image.new('RGBA', topcanvas, (255, 255, 255, 255))
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype('coolvetica.ttf', 40)
        d = ImageDraw.Draw(txt)
        textcen = text.center(21, " ")
        d.text((5, 5), textcen, font=fnt, fill=(0, 0, 0, 255))
        return Image.alpha_composite(im, txt)

    def getSlotsImg(self, text, slots_im, txt_im):
        slotcanvas = (500, 175)
        # get a font
        fnt = ImageFont.truetype('coolvetica.ttf', 30)
        fntslots = ImageFont.truetype('coolvetica.ttf', 40)
        # get a drawing context
        d = ImageDraw.Draw(txt_im)

        str = text.split('\n', 1)
        # question_parts = []
        # temp = ""
        # i = 0
        # for x in str[0]:
        #     temp += x
        #     i += 1
        #     if i > 25:
        #         temp += '\n'
        #         i = 0

        #question = str[0].center(24, " ")
        push_slots_down = 0
        question = str[0].split(" ")
        end_q = ""
        size = 0
        for i in question:
            size += len(i)
            if size > 20:
                end_q += ("\n" + i)
                size = 0
                push_slots_down += 50
            else:
                end_q += i
            end_q += " "
        question = end_q

        #slots = str[1].center(25, " ")
        slots = str[1]
        # temp = ""
        # for i in slots:
            # temp += (i + "\n")
        # slots = temp
		
        logprint("Working with " + question + " and " + slots)

        # draw text, half opacity
        d.multiline_text((75, 25), question, font=fnt, align="center", fill=(0, 0, 0, 255))
        d.multiline_text((40, 75 + push_slots_down), slots, font=fntslots, fill=(0, 0, 0, 255))

        out = Image.alpha_composite(slots_im, txt_im)
        # out.show()
        return out

    def hangmanImg(self, imgnum, slotstring, topText):
        canvas = (500, 700)
        im = Image.new('RGBA', canvas, (255, 255, 255, 255))
        hm_im = Image.open("http://192.241.150.224/images/hangman_pics/hangman_" + str(imgnum) + ".png")
        hm_cut = hm_im.resize((400, 400))
        im.paste(hm_cut, (50, 50))

        slotcanvas = (500, 275)
        slots_im = Image.new('RGBA', slotcanvas, (255, 255, 255, 255))
        txt_im = Image.new('RGBA', slots_im.size, (255, 255, 255, 255))
        
        im.paste(self.getSlotsImg(slotstring, slots_im, txt_im), (0, 425))
        if topText != None:
            im.paste(self.topImg(topText), (0, 0))
        
        slots_im.close()
        txt_im.close()
        # ftp = self.establishConn()
        # temp = io.StringIO()
        # im.save(temp, format="png")
        # ftp.storbinary("STOR 1.png", temp)
        # ftp.close()
        # return "http://192.241.150.224/images/" + str(self.session_chatid) + "/1.png"
        #return im
        self.createImages(im)
        im.close()
        return "http://192.241.150.224/images/" + self.session_chatid + "/progress_pic.png"

    def createImages(self, img):
        path = "/var/www/html/images/"
        if not os.path.exists(path + self.session_chatid):
            os.mkdir(path + self.session_chatid)
        file = os.path.join(path+ self.session_chatid, "progress_pic.png")
        img.save(file, "PNG")

    def deleteImages(self):
        path = "/var/www/html/images/" + self.session_chatid
        if os.path.exists(path):
            shutil.rmtree(path)

    def setScore(self):
        for i in self.list_of_availables:
            self.comp_points[i] = 0

    def incrementScore(self, user, score):
        self.comp_points[user] += score

    def endScore(self, message):
        response_messages = []

        scoreboard = self.scoreboard()
        winners = []
        high_score = 0
        sorted_winners = sorted(self.comp_points, key=self.comp_points.get, reverse=True)
        for winner in sorted_winners:
            if high_score == 0 or high_score == self.comp_points[winner]:
                winners.append(winner)
                high_score = self.comp_points[winner]
                logprint(winner + " : " + str(high_score))

        Hangman.winners = winners

        scoreboard += ("__________________\nWinner: " + " & ".join(self.getName(x) for x in winners))
        logprint(scoreboard)

        response_messages.append(TextMessage(
            to=message.from_user,
            chat_id=message.chat_id,
            body=scoreboard + " " + winner_e[random.randrange(len(winner_e))]
        ))
        return response_messages

    def scoreboard(self):
        scoreboard = ""
        for user in list(self.comp_points.keys()):
            line = (self.getName(user) + " | " + str(self.comp_points[user])).split()
            scoreboard += "{0[0]:<20}{0[1]:>1}{0[2]:>2}\n".format(line)


        headers = ["Players", "Scores"]
        # names = list(self.comp_points.keys())
        # scores = list(self.comp_points.values())
        # data = list(zip(names, (str(self.comp_points[x]) for x in list(self.comp_points.keys()))))
        # print("Trying to output: " + str(data))
        # # for i, d in enumerate(data):
        # #     line = "".join(str(x).ljust(25) for x in d)
        # #     scoreboard += line
        # scoreboard += "".join(str(x).ljust(20) for x in headers) + "\n"
        # for d in data:
        #     user = Hangman.kik.get_user(d[0]).first_name
        #     line = user.ljust(15) + (" "*(20 - len(user))) +d[1] + "\n"
        #     scoreboard += line

        return scoreboard

    def invitePlayers(self, response_mes, mes):
        self.search_for_players = True;
        response_mes.append(TextMessage(
            to=mes.from_user,
            chat_id=mes.chat_id,
            body="Who would like to join {}? (30 seconds)".format(mes.from_user),
            keyboards=[SuggestedResponseKeyboard(responses=[TextResponse("Count me in!")])]

        ))
        self.pool.apply_async(self.waitAndResponse, args=(30,mes))
        self.pool.join()
        #tempthread = threading.Thread(target=self.waitAndResponse, args=[30,mes])
        #tempthread.start()

    def waitAndResponse(self, seconds, message):
        logprint("Beggining waiting")
        time.sleep(seconds)
        logprint("Finish waiting")
        response_messages = []
        if len(self.list_of_threadplayers) <= 1:
            self.list_of_threadplayers = []
            self.all_players_ready = False
            response_messages.append(TextMessage(
                to=message.from_user,
                chat_id=message.chat_id,
                body="Not enough players!"
            ))
        else:
            self.all_players_ready = True

        if self.all_players_ready:
            if message.body.lower() == "co-op":
                self.beginMulti("coop",response_messages, message)
            elif message.body.lower() == "competitive":
                self.beginMulti("comp", response_messages, message)

        logprint("Num of messages in response: {}".format(len(response_messages)))

        self.search_for_players = False
        Hangman.kik.send_messages(response_messages)

    async def getKikPicMessage(self, query, message):
        async def get_soup(url, header):
            return BeautifulSoup(urllib.request.urlopen(urllib.request.Request(url, headers=header)), 'html.parser')
        logprint("Attempting to grab image of: %s" % (query,))
        query = query.split()
        query = '+'.join(query)

        url = "https://www.google.co.in/search?q=" + query + "&source=lnms&tbm=isch&safe=high"
        print(url)
        header = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
            }
        soup = await get_soup(url, header)

        ActualImages = []  # contains the link for Large original images, type of  image
        i = 0
        for a in soup.find_all("div", {"class": "rg_meta"}):
            try:
                link, Type = json.loads(a.text)["ou"], json.loads(a.text)["ity"]
                logprint("Retrieved {} and {} to Actual Images list".format(link, Type))
                if Type != "":
                    ActualImages.append((link, Type))
                if i == 5:
                    break
                i += 1
            except:
                continue
        j = 0
        urlgif = "https://www.google.co.in/search?q=" + query + "&source=lnt&tbm=isch&tbs=itp:animated&safe=high"
        soupgif = await get_soup(urlgif, header)

        for b in soupgif.find_all("div", {"class": "rg_meta"}):
            try:
                link, Type = json.loads(b.text)["ou"], json.loads(b.text)["ity"]
                print("Inserting GIF {} and {} to Actual Images list".format(link, Type))
                if Type != "":
                    ActualImages.append((link, Type))
                if j == 5:
                    break
                j += 1
            except:
                continue

        from kik_sql import KikDB
        from kik_async_sql import AsyncKikDB
        sqlquery = "update game_sessions set session_data = JSON_SET(session_data, '$.answer_url', %s)" \
                   " where chat_id = %s"
        random.shuffle(ActualImages)
        asyncsql = AsyncKikDB()
        for i, (img, Type) in enumerate(ActualImages):
            try:
                self.answer_url = Type + "-SPLITMEPLS-" + img

                print("Attempt to send %s" % (img,))
                self.answer_url = Type + "-SPLITMEPLS-" + img
                logprint("Answer_url has %s, attempting to store into db" % (self.answer_url,))
                asyncio.ensure_future(asyncsql.mysqlExec(sqlquery, (self.answer_url, self.session_chatid), message))
                break
            except Exception as e:
                logprint("Error in saving URL to mysql: %s" % str(e))
                logging.error(e, exc_info=True)
                continue

        #return messages_to_send
