import MySQLdb
import logging
import os

def logprint(msg, *args):
    try:
        logging.info(msg)
    except:
        logging.info("Error logging.")
        logging.info(str(msg).encode("utf8"))
    for i in args:
        logging.info(str(i))
    print(msg, *args)

class KikDB():
    query_reg = "INSERT INTO game_sessions(chat_id, session_data) VALUES (%s, %s)"
    query_overwrite = "UPDATE game_sessions SET session_data = %s WHERE chat_id = %s"
    query_retrieve = "SELECT session_data FROM game_sessions WHERE chat_id = %s"
    query_checkExist = "SELECT COUNT(1) FROM game_sessions WHERE chat_id = %s"
    query_del = "DELETE FROM game_sessions WHERE chat_id = %s"
    query_timed = "CREATE EVENT %s %s ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 5 MINUTE " \
                  "DO DELETE FROM game_sessions WHERE chat_id = '%s'"
    query_newtime = "ALTER EVENT %s ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 720 MINUTE ENABLE"
    query_newlowtime = "ALTER EVENT %s ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 10 MINUTE ENABLE"
    query_drop_event = "DROP EVENT IF EXISTS %s"

    query_LB_checkExist = "SELECT COUNT(1) FROM leaderboards WHERE name = %s"
    query_LB_insert = "INSERT INTO leaderboards(id, name, stats) VALUES(null, %s, %s)"
    query_LB_update = "UPDATE leaderboards SET stats = %s WHERE name = %s"
    query_LB_retrieve = "SELECT stats FROM leaderboards WHERE name = %s"
	
    q_catch_custom_phrase = "update game_sessions set session_data = JSON_SET(session_data, '$.catch_custom_phrase', %s)" \
                   " where chat_id = %s"
    q_custom_ready = "update game_sessions set session_data = JSON_SET(session_data, '$.custom_ready', %s)" \
                       " where chat_id = %s"
    q_custom_insert = "insert into routing_table(id, name, origin_id) select * from (select null, %s, %s) as tmp where " \
                      "not exists(select origin_id from routing_table where origin_id = %s) limit 1;"

    q_custom_exists1 = "select origin_id from routing_table where name = %s"
    q_custom_exists2 = "select json_contains((select `session_data` from game_sessions where chat_id = %s), " \
                             "%s, '$.custom_chooser')"
    q_custom_delete = "DELETE FROM routing_table WHERE name = %s limit 1"
    q_custom_emptyQ = "select json_contains((select `session_data` from game_sessions where chat_id = %s), " \
                             "%s, '$.question')"
    q_custom_question = "update game_sessions set session_data = JSON_SET(session_data, '$.question', %s)" \
                 " where chat_id = %s"
    q_custom_answer = "update game_sessions set session_data = JSON_SET(session_data, '$.answer', %s)" \
               " where chat_id = %s"
    def __init__(self):
        self.db = MySQLdb.connect(host=os.environ['KIK_HOSTNAME'], user=os.environ['KIK_SQL_USER'], passwd=os.environ['KIK_SQL_PASSWORD'], db="hangman", port=3306, charset='utf8', use_unicode=True)
        self.cursor = self.db.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
        
    def mysqlDelScheduler(self, schedExists, game_chat_id, game_status, custom_user):
        label_game_chat_id = "EVENT" + game_chat_id[:55]
        try:
            if not schedExists:
                logprint("Creating new scheduler")
                schedmysql = KikDB.query_timed % ("IF NOT EXISTS", label_game_chat_id, game_chat_id)
                logprint("Using QUERY: " + schedmysql)
                self.cursor.execute(schedmysql)
            else:
                logprint("Updating scheduler")
                if game_status or custom_user != "":
                    schedmysql = KikDB.query_newtime % (label_game_chat_id,)
                else:
                    schedmysql = KikDB.query_newlowtime % (label_game_chat_id,)
                logprint("Using QUERY: " + schedmysql)
                self.cursor.execute(schedmysql)
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            logprint("MySqlSched ERROR: ", e)
            logging.error(e, exc_info=True)
            schedmysql = KikDB.query_timed % ("", label_game_chat_id, game_chat_id)
            logprint("Using QUERY: " + schedmysql)
            self.cursor.execute(schedmysql)
        finally:
            self.db.commit()

    def mysqlExec(self, query, tuple):
        try:
            if tuple == None:
                logprint("Using QUERY: " + query)
                self.cursor.execute(query)
            else:
                logprint("Using QUERY: " + query % tuple)
                self.cursor.execute(query, tuple)
            self.db.commit()
        except MySQLdb.IntegrityError:
            logprint("Failed to execute: " + query)
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            logprint("MYSQL ERROR: ", e)
            logging.error(e, exc_info=True)
