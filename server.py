from flask import Flask, request

import sqlite3
import sys

app = Flask(__name__, static_url_path="")

@app.route("/")
def hello_world():
    return app.send_static_file("index.html")

@app.route("/api/activity/<datetime>/totals")
def activity_totals(datetime):
    con = sqlite3.connect("fitdata.db")
    cur = con.cursor()

    try:
        q = cur.execute("SELECT * FROM Activity WHERE start_time = ?", (datetime,)).fetchall()
    except sqlite3.Error:
        return "invalid date given", 400

    return [row[1:] for row in q]

@app.route("/api/activity/<datetime>/records")
def activity_records(datetime):
    con = sqlite3.connect("fitdata.db")
    cur = con.cursor()

    try:
        q = cur.execute("""
            SELECT timestamp,enhanced_speed,heart_rate,cadence,enhanced_altitude 
            FROM ActivityRecord 
            WHERE activity_id=(
                SELECT activity_id FROM Activity WHERE start_time = ?
            )
        """, (datetime,)).fetchall()

    except sqlite3.Error:
        return "invalid date given", 400

    return q

def activity_laps():
    return "unimplemented"

@app.route("/api/summary/totals")
def totals():
    # eg. /api/summary/totals?group_by=week&start=date&end=date
    # return total num activities, distance, time per week, month, year, all

    start = request.args.get("start", default="0001-01-01")
    end = request.args.get("end", default="9999-01-01")

    group_by = request.args.get("group_by", default="week")
    con = sqlite3.connect("fitdata.db")
    cur = con.cursor()

    if group_by=="week":
        representative_date = "weekday 1"
    elif group_by=="month":
        representative_date = "start of month"
    elif group_by=="year":
        representative_date = "start of year"
    elif group_by=="all":
        q = cur.execute(
            """
            select 
                count(*) as num_activities,
                sum(total_distance) as total_distance,
                sum(total_timer_time) as total_time
            from Activity
            where start_time between ? and ?
            """, (start,end)).fetchall()

        con.close()
        return q
    else:
        con.close()
        return "invalid group_by argument", 400

    q = cur.execute(
                """
                select 
                    date(start_time, ?) summary_date,
                    count(*) as num_activities,
                    sum(total_distance) as total_distance,
                    sum(total_timer_time) as total_time
                from Activity
                where start_time between ? and ?
                group by summary_date;
                """, (representative_date,start,end)).fetchall()

    con.close()
    return q

@app.route("/api/summary/personalrecords")
def prs():
    return "unimplemented"

@app.route("/api/summary")
def summary():
    # eg. /api/summary?avg_speed&avg_heart_rate&start=date&end=date
    # return json of [{time, col1, col2, ...}] for all activities in date range

    start = request.args.get("start", default="0001-01-01")
    end = request.args.get("end", default="9999-01-01")

    cols = ["start_time",
            "end_time",
            "total_elapsed_time",
            "total_timer_time",
            "start_position_lat" , 
            "start_position_long" ,
            "total_ascent" ,
            "total_descent",
            "total_distance" ,
            "total_strides" ,
            "total_calories" ,
            "enhanced_avg_speed",
            "avg_speed",
            "enhanced_max_speed",
            "max_speed",
            "avg_heart_rate",
            "max_heart_rate",
            "avg_running_cadence",
            "max_running_cadence",
            "avg_fractional_cadence",
            "max_fractional_cadence",
            "total_training_effect",
            "total_anaerobic_training_effect"
        ]

    remaining_args = [k for k in request.args.keys() if k != "start" and k != "end"]

    # if any of the remaining args are not valid column names return error
    if not all([k in cols for k in remaining_args]):
        return "invalid parameter", 400

    con = sqlite3.connect("fitdata.db")
    cur = con.cursor()

    q = cur.execute(f"SELECT {','.join(['start_time']+remaining_args)} FROM Activity WHERE start_time BETWEEN ? AND ?", (start, end)).fetchall()

    con.close()

    return q
