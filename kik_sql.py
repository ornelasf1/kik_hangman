import MySQLdb
import logging

def logprint(msg, *args):
    logging.info(msg)
    for i in args:
        logging.info(str(i))
    print(msg, *args)


class KikDB():
    query_reg = "INSERT INTO game_sessions(chat_id, session_data) VALUES (%s, %s)"
    query_overwrite = "UPDATE game_sessions SET session_data = %s WHERE chat_id = %s"
    query_retrieve = "SELECT session_data FROM game_sessions WHERE chat_id = %s"
    query_checkExist = "SELECT COUNT(1) FROM game_sessions WHERE chat_id = %s"
    query_del = "DELETE FROM game_sessions WHERE chat_id = %s"
    query_timed = "CREATE EVENT %s %s ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 30 SECOND " \
                  "DO DELETE FROM game_sessions WHERE chat_id = '%s'"
    query_newtime = "ALTER EVENT %s ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 30 SECOND ENABLE"
    query_newlowtime = "ALTER EVENT %s ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 30 SECOND ENABLE"
    query_drop_event = "DROP EVENT IF EXISTS %s"

    query_LB_checkExist = "SELECT COUNT(1) FROM leaderboards WHERE name = %s"
    query_LB_insert = "INSERT INTO leaderboards(id, name, stats) VALUES(null, %s, %s)"
    query_LB_update = "UPDATE leaderboards SET stats = %s WHERE name = %s"
    query_LB_retrieve = "SELECT stats FROM leaderboards WHERE name = %s"

    query_custom_checkExist = "SELECT COUNT(1) FROM user_values WHERE name = %s"
    query_custom_checkMode = "select json_contains((select `session_data` from game_sessions where chat_id = %s), " \
                             "'true', '$.catch_custom_phrase')"
    query_custom_userCheck = "select json_contains((select `variables` from user_values where name = %s), " \
                             "'true', '$.custom_chooser')"
    query_custom_delete = "DELETE FROM user_values WHERE name = %s"
    query_userinfo_insert = "INSERT INTO user_values(id, name, variables) VALUES (null, %s, %s)"
    query_update_json = "update game_sessions set session_data = JSON_SET(session_data, '$.answer_url', %s)" \
                   " where chat_id = %s"



    def __init__(self):
        self.db = MySQLdb.connect(host="*********", user="*******", passwd="*********", db="*******", port=1234)
        self.cursor = self.db.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def mysqlDelScheduler(self, schedExists, game_chat_id, game_status):
        label_game_chat_id = "EVENT" + game_chat_id[:55]
        try:
            if not schedExists:
                logprint("Creating new scheduler")
                schedmysql = KikDB.query_timed % ("IF NOT EXISTS", label_game_chat_id, game_chat_id)
                logprint("Using QUERY: " + schedmysql)
                self.cursor.execute(schedmysql)
            else:
                logprint("Updating scheduler")
                if game_status:
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
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            logprint("MYSQL ERROR: ", e)
            logging.error(e, exc_info=True)
