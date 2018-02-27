# -*- coding: utf-8 -*-

from flask import Flask, request, Response
from kik import KikApi, Configuration, KikError
from kik.messages import messages_from_json, TextMessage
from kik_hangman_session import Hangman
import json
import logging
from kik_sql import KikDB

logging.basicConfig(filename='hangmanlog.log',level=logging.INFO, format="[%(asctime)s] %(message)s")

app = Flask(__name__)
kik = KikApi('*********', '****************************')
Hangman.kik = kik
code = kik.create_code({'hung': 'code'})

kik.set_configuration(Configuration(webhook="http://beea37b6.ngrok.io/incoming"))

def logprint(msg, *args):
    logging.info(msg)
    for i in args:
        logging.info(str(i))
    print(msg, *args)

@app.route('/incoming', methods=['POST'])
def incoming():

    if not kik.verify_signature(request.headers.get('X-Kik-Signature'), request.get_data()):
        return Response(status=403)

    messages = messages_from_json(request.json['messages'])

    for message in messages:
        game_chat_id = message.chat_id
        temp_game = Hangman()

        if message.from_user in ["furrylife100"]:
            logprint("BLOCKING: " + message.from_user + " said " + message.body)
            return Response(status=200)

        with KikDB() as kikdb:
            try:
                kikdb.cursor.execute(KikDB.query_checkExist,(game_chat_id,))
                existance = tuple(kikdb.cursor.fetchone())
                print(existance)
                if not existance[0]:
                    logprint("RECORD DOES NOT EXIST\nMain: Creating game")
                    kikdb.mysqlExec(KikDB.query_reg, (game_chat_id, json.dumps(temp_game.jsondump())))
                    temp_game.initiateSession(message)
                    kikdb.mysqlDelScheduler(False, game_chat_id, False)
                else:
                    logprint("RECORD EXISTS, RETRIEVING DATA")
                    # kikdb.cursor.execute("select json_contains((select `session_data` from "
                    #                      "game_sessions where chat_id = %s), 'true', '$.catch_custom_phrase');", (game_chat_id,))
                    # custom_check = tuple(kikdb.cursor.fetchone())
                    # print(custom_check)

                    kikdb.mysqlExec(KikDB.query_retrieve, (game_chat_id,))
                    result = kikdb.cursor.fetchone()
                    temp_game.loadFromDB(json.loads(result[0]))
                    #temp_game.loadFromDB(json.loads(result[0].decode("utf-8", "ignore")))
                    logprint("END RETRIEVING DATA")
                    temp_game.initiateSession(message)
                    kikdb.mysqlDelScheduler(True, game_chat_id, temp_game.game_status)
                    if temp_game.check:
                        logprint("Main: Game ended. Deleting chat session from database")
                        kikdb.mysqlExec(KikDB.query_del, (game_chat_id,))
                        logprint("Main: Deleting scheduler if it exists as well")
                        label_game_chat_id = "EVENT" + game_chat_id[:55]						
                        query = KikDB.query_drop_event % (label_game_chat_id,)
                        kikdb.mysqlExec(query, None)
                        break
            except KikError as e:
                logprint("Something went wrong:", str(e))
                logging.error(e, exc_info=True)
                #traceback.print_tb(e.__traceback__)
                logprint("="*150)
                return Response(status=200)
            except Exception as err:
                logprint("Something that wasn't Kik went wrong:", str(err))
                logprint("KIK SEND_MESSAGE")
                kik.send_messages([TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body="Sorry, service is currently down. Try again later!"
                )])
                logging.error(err, exc_info=True)
                #traceback.print_tb(err.__traceback__)
                logprint("="*150)
                return Response(status=200)

            #logprint("UPDATING DATABASE with %s" % temp_game.jsondump())
            kikdb.mysqlExec(KikDB.query_overwrite, (json.dumps(temp_game.jsondump()), (game_chat_id,)))

    logprint("="*150)
    return Response(status=200)


if __name__ == "__main__":
    app.run(port=8080)
