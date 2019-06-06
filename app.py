#!/usr/bin/env python3

from flask import Flask, Response, Blueprint, g, redirect, send_file, url_for
import records
import json
from configparser import ConfigParser, ExtendedInterpolation

cfg = ConfigParser(interpolation=ExtendedInterpolation())
cfg.read('config.ini')
settings = dict(cfg.items('database'))
db = None

def path_to_nirvana():
  global db
  try:
    db = records.Database("postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}".format(**settings), pool_size=10)
    print(db)
  except Exception as e:
    raise e

  if not existence():
        samsara()
  return Flask(__name__)


def existence():
  exists = db.query(
  """SELECT EXISTS (
   SELECT 1 
   FROM   pg_catalog.pg_class c
   JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
   WHERE  n.nspname = 'public'
   AND    c.relname = 'meditation'
   AND    c.relkind = 'r'    -- only tables
   );""").first().exists
  if not exists:
    return exists

  exists = db.query("""SELECT EXISTS (
  SELECT 1 
  FROM   pg_catalog.pg_class c
  JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE  n.nspname = 'public'
  AND    c.relname = 'meditation_session'
  AND    c.relkind = 'r'    -- only tables
  );""").first().exists
  return exists


def samsara():
  global db
  db.query("create table meditation (meditation_id serial primary key, meditation_date date default now())")
  try:
    db.query("create table meditation_session (meditation_session_id serial primary key, meditation_id integer references meditation not null, meditation_time datetime default now() not null)")
  except Exception as e:
    raise e



app = path_to_nirvana()


@app.before_request
def get_db():
  g.db = db.get_connection()


@app.route("/api/meditate")
def post_meditate():
  res = meditate()
  return Response(res, mimetype="application/json") # I feel like there has to be a way to just default this mimetype


@app.route("/api/yesterdays-meditation")
def get_api_yesterdays_meditation():
  return meditation(1)


@app.route("/api/todays-meditation")
def get_api_todays_meditation():
  return meditation()


@app.route("/api/meditation")
def get_api_meditation():
  return all_meditation()


def meditation(day_delta=0):
  sql = "select * from meditation natural left join meditation_session where meditation.meditation_date = now()::date - interval ':delta day'"
  return g.db.query(sql, delta=day_delta).export('json')


def all_meditation():
  sql = "select * from meditation natural left join meditation_session"
  return g.db.query(sql).export('json')


def meditate():
  if not have_meditated():
    sql = "insert into meditation values (default, default) returning meditation_id"
  else:
    sql = "select meditation_id from meditation where meditation_date = now()::date"

  id = g.db.query(sql).first().meditation_id

  sql = "insert into meditation_session values (default, :meditation_id, default)"
  g.db.query(sql, meditation_id=id)

  return json_response("success")


def have_meditated():
  sql = "select count(*) from meditation where meditation_date = now()::date"
  return bool(g.db.query(sql).first().count)


def json_response(type="status", message="unknown"):
  return (json.dumps({type: message}))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


