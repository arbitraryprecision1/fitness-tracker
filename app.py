import sqlite3
import sys
from pathlib import Path
import argparse

import fitparse

from field_types import *

from server import app


def main():
    # parse arguments from command line
    parser = argparse.ArgumentParser(
                    prog = 'Garmin FitFile Webapp',
                    description = 'Parses unseen fitfiles and adds their data to db. Runs local webpage to view data in browser. ',
                    epilog = '`app.py` defaults to `app.py -src ./FitFiles -r -u`')
    
    parser.add_argument("-src", default="FitFiles", required=False, 
        help="directory of FitFiles to be used, expected to contain src/Activity and src/Monitor as subdirectories")
    update_or_reset_group = parser.add_mutually_exclusive_group()
    update_or_reset_group.add_argument("-u", "--update", default=False, action="store_true", required=False, 
        help="update the db using unseen files from src")
    update_or_reset_group.add_argument("-t", "--reset", default=False, action="store_true", required=False, 
        help="reset the db to exactly match files at src")
    parser.add_argument("-r", "--run", default=False, action="store_true", required=False, help="run the local webapp")

    args = parser.parse_args()

    # set the default of updating db then running web server if none of -u, -t, -r are given
    if not any([args.update, args.reset, args.run]):
        args.run = True
        args.update = True

    # ----- dealing with db and fitfiles -----

    # if directory malformed and we will need to use it
    if (args.update or args.reset) and not all((
        Path(args.src).is_dir(),
        Path(args.src+"/Activity").is_dir(),
        Path(args.src+"/Monitor").is_dir()
    )):
        print("fitfiles src directory specified (or the default ./FitFiles) is malformed or missing")
        return 1

    if args.update:
        update_db(args.src)
    elif args.reset:
        reset_db(args.src)

    # ----- running webserver ---------

    if args.run:
        app.run(debug=False)
        
    return 0



def update_db(src):
    # creates db if not already exists
    con = sqlite3.connect("fitdata.db")
    cur = con.cursor()

    # create any tables if not present already
    setup_db(cur)

    # parse all unseen fitfiles and add to db
    activity_count = 0
    lap_count = 0
    record_count = 0

    # TODO: more elegant way than attempting insert and catching unique constraint violation?
    for f in Path(src+"/Activity").iterdir():
        try:
            counts = add_fitfile(f, con, cur)

            activity_count+=counts["activity_count"]
            lap_count+=counts["lap_count"]
            record_count+=counts["record_count"]

        except sqlite3.IntegrityError as e:
            print(f"[FILE ERROR] Already seen file {f}, skipping it.")
            print(e)

            continue

    print("-----------------------------------")
    print(f"successfully added {activity_count} activities to db, containing {lap_count} laps and {record_count} individual records")
    print("-----------------------------------")
    con.close()


def reset_db(src):
    # creates db if not already exists
    con = sqlite3.connect("fitdata.db")
    cur = con.cursor()

    # clear and recreate db
    cur.execute("DROP TABLE IF EXISTS Activity")
    cur.execute("DROP TABLE IF EXISTS Lap")
    cur.execute("DROP TABLE IF EXISTS ActivityRecord")
    # cur.execute("DROP TABLE IF EXISTS Monitoring")
    # cur.execute("DROP TABLE IF EXISTS Settings")

    # recreate all the tables
    setup_db(cur)

    # parse all the fitfiles and add them to db
    activity_count = 0
    lap_count = 0
    record_count = 0
    for f in Path(src+"/Activity").iterdir():
        counts = add_fitfile(f, con, cur)

        activity_count+=counts["activity_count"]
        lap_count+=counts["lap_count"]
        record_count+=counts["record_count"]


    print("-----------------------------------")
    print(f"successfully added {activity_count} activities to db, containing {lap_count} laps and {record_count} individual records")
    print("-----------------------------------")
    con.close()


def setup_db(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Activity(
        activity_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        start_time INTEGER UNIQUE NOT NULL,
        end_time INTEGER NOT NULL,
        total_elapsed_time REAL NOT NULL,
        total_timer_time REAL NOT NULL,

        start_position_lat INTEGER, 
        start_position_long INTEGER,
        total_ascent INTEGER,
        total_descent INTEGER,

        total_distance REAL NOT NULL,
        total_strides INTEGER NOT NULL,
        total_calories INTEGER NOT NULL,
        enhanced_avg_speed REAL NOT NULL,
        avg_speed REAL NOT NULL,
        enhanced_max_speed REAL NOT NULL,
        max_speed REAL NOT NULL,
        avg_heart_rate REAL NOT NULL,
        max_heart_rate INTEGER NOT NULL,
        avg_running_cadence INTEGER NOT NULL,
        max_running_cadence INTEGER NOT NULL,
        avg_fractional_cadence REAL NOT NULL,
        max_fractional_cadence REAL NOT NULL,
        total_training_effect REAL NOT NULL,
        total_anaerobic_training_effect REAL NOT NULL
        )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Lap(
        lap_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        activity_id INTEGER NOT NULL,
        start_time INTEGER UNIQUE NOT NULL,
        end_time INTEGER NOT NULL,
        total_elapsed_time REAL NOT NULL,
        total_timer_time REAL NOT NULL,

        start_position_lat INTEGER, 
        start_position_long INTEGER,
        total_ascent INTEGER,
        total_descent INTEGER,

        total_distance REAL NOT NULL,
        total_strides INTEGER NOT NULL,
        total_calories INTEGER NOT NULL,
        enhanced_avg_speed REAL NOT NULL,
        avg_speed REAL NOT NULL,
        enhanced_max_speed REAL NOT NULL,
        max_speed REAL NOT NULL,
        avg_heart_rate REAL NOT NULL,
        max_heart_rate INTEGER NOT NULL,
        avg_running_cadence INTEGER NOT NULL,
        max_running_cadence INTEGER NOT NULL,
        avg_fractional_cadence REAL NOT NULL,
        max_fractional_cadence REAL NOT NULL,

        FOREIGN KEY(activity_id) REFERENCES Activity(activity_id)
        )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ActivityRecord(
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_id INTEGER NOT NULL,
        timestamp INTEGER UNIQUE NOT NULL,
        distance REAL NOT NULL,
        enhanced_speed REAL NOT NULL,
        speed REAL NOT NULL,
        heart_rate INTEGER NOT NULL,
        cadence INTEGER NOT NULL,
        fractional_cadence REAL NOT NULL,

        enhanced_altitude FLOAT,
        altitude FLOAT,
        position_long INTEGER,
        position_lat INTEGER,

        FOREIGN KEY(activity_id) REFERENCES Activity(activity_id)
    )
    """)
    # cur.execute("CREATE TABLE IF NOT EXISTS Monitoring()")
    # cur.execute("CREATE TABLE IF NOT EXISTS Settings")

def add_fitfile(f, con, cur):
    activity_count = 0
    lap_count = 0
    record_count = 0

    try:
        fitfile = fitparse.FitFile(str(f.resolve()))
    except fitparse.FitParseError as e:
        print(f"[FILE ERROR] failed to parse fit file {f}, skipping it.")
        print(e)

        return {"activity_count": activity_count, "lap_count": lap_count, "record_count": record_count}

    try:
        session_data = SessionData(next(fitfile.get_messages("session")))
    except ValueError as e:
        print(f"[ACTIVITY ERROR] problem with activity in fit file {f}, skipping it.")
        print(e)
        
        return {"activity_count": activity_count, "lap_count": lap_count, "record_count": record_count}

    cur.execute(f"""INSERT INTO Activity (
                activity_id,
                start_time,
                end_time ,
                total_elapsed_time,
                total_timer_time ,

                start_position_lat , 
                start_position_long ,
                total_ascent ,
                total_descent,

                total_distance ,
                total_strides ,
                total_calories ,
                enhanced_avg_speed,
                avg_speed,
                enhanced_max_speed,
                max_speed ,
                avg_heart_rate ,
                max_heart_rate ,
                avg_running_cadence ,
                max_running_cadence ,
                avg_fractional_cadence,
                max_fractional_cadence,
                total_training_effect ,
                total_anaerobic_training_effect
            ) VALUES (NULL,{"?,"*22}?) 
            """, (
                    session_data.start_time, 
                    session_data.timestamp,
                    session_data.total_elapsed_time,
                    session_data.total_timer_time,
                    session_data.start_position_lat,
                    session_data.start_position_long,
                    session_data.total_ascent,
                    session_data.total_descent,
                    session_data.total_distance,
                    session_data.total_strides,
                    session_data.total_calories,
                    session_data.enhanced_avg_speed,
                    session_data.avg_speed,
                    session_data.enhanced_max_speed,
                    session_data.max_speed,
                    session_data.avg_heart_rate,
                    session_data.max_heart_rate,
                    session_data.avg_running_cadence,
                    session_data.max_running_cadence,
                    session_data.avg_fractional_cadence,
                    session_data.max_fractional_cadence,
                    session_data.total_training_effect,
                    session_data.total_anaerobic_training_effect
                )
            )

    # activity data was successfully parsed so can be committed to db
    con.commit()

    activity_count+=1
    current_activity_id = cur.lastrowid

    laps = []
    for message in fitfile.get_messages("lap"):
        try:
            lap = LapData(message)
            laps.append(lap)
            lap_count+=1
        except ValueError as e:
            print(f"[LAP ERROR] problem with a lap in fit file {f}, skipping this lap but continuing with file.")
            print(e)

            continue

    cur.executemany(f"""INSERT INTO Lap (
        lap_id,
        activity_id,
        start_time,
        end_time ,
        total_elapsed_time,
        total_timer_time ,

        start_position_lat , 
        start_position_long ,
        total_ascent ,
        total_descent,

        total_distance ,
        total_strides ,
        total_calories ,
        enhanced_avg_speed,
        avg_speed,
        enhanced_max_speed,
        max_speed ,
        avg_heart_rate ,
        max_heart_rate ,
        avg_running_cadence ,
        max_running_cadence ,
        avg_fractional_cadence,
        max_fractional_cadence
    ) VALUES (NULL,{"?,"*21}?) 
    """, [(
            current_activity_id,
            lap.start_time, 
            lap.timestamp,
            lap.total_elapsed_time,
            lap.total_timer_time,
            lap.start_position_lat,
            lap.start_position_long,
            lap.total_ascent,
            lap.total_descent,
            lap.total_distance,
            lap.total_strides,
            lap.total_calories,
            lap.enhanced_avg_speed,
            lap.avg_speed,
            lap.enhanced_max_speed,
            lap.max_speed,
            lap.avg_heart_rate,
            lap.max_heart_rate,
            lap.avg_running_cadence,
            lap.max_running_cadence,
            lap.avg_fractional_cadence,
            lap.max_fractional_cadence
        ) for lap in laps]
    )

    con.commit()

    records = []
    for message in fitfile.get_messages("record"):
        try:
            record = RecordData(message)
            records.append(record)
            record_count+=1
        except ValueError as e:
            print(f"[RECORD ERROR] problem with a record in fit file {f}, skipping this record but continuing with file.")
            print(e)

            continue

    cur.executemany(f"""INSERT INTO ActivityRecord(
                record_id ,
                activity_id,
                timestamp ,
                distance ,
                enhanced_speed ,
                speed ,
                heart_rate ,
                cadence,
                fractional_cadence ,

                enhanced_altitude ,
                altitude ,
                position_long ,
                position_lat
            ) VALUES (NULL,{"?,"*11}?) 
            """, [(
                current_activity_id,
                record.timestamp,
                record.distance,
                record.enhanced_speed,
                record.speed,
                record.heart_rate,
                record.cadence,
                record.fractional_cadence,
                record.enhanced_altitude,
                record.altitude,
                record.position_long,
                record.position_lat
                ) for record in records]
            )

    con.commit()

    return {"activity_count": activity_count, "lap_count": lap_count, "record_count": record_count}





if __name__ == '__main__':
    sys.exit(main())