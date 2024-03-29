#!/usr/bin/env python3
import psycopg2
from flask import Flask


HTML_WRAP = '''\
<!DOCTYPE html>
<html>
  <head>
    <title>Log Analysis</title>
    <style>
      textarea { width: 400px; height: 100px; }
      div.post { border: 1px solid #999;
                 padding: 10px 10px;
                 margin: 10px 20%%; }
      hr.postbound { width: 50%%; }
      em.date { color: #999 }
    </style>
  </head>
  <body>
%s
  </body>
</html>
'''


app = Flask(__name__)


@app.route('/')
def index():
    sections = append_section(get_three_most_popular_article(), "Top 3 Most Popular Articles")
    sections += append_section(get_most_popular_article_authors(), "The most popular article authors of all time")
    sections += append_section(get_day_with_most_errors(), "Day with the most errors", "% errors")
    html = HTML_WRAP % sections
    return html


def append_section(data, title, label="view"):
    items = "<h1>" + title + "</h1><br>"
    for item in data:
        items += " — ".join(map(str, item)) + " " + label + "<br>"
    return items


def get_three_most_popular_article():
    db, cursor = connect('news')
    cursor.execute("SELECT articles.title, count(path) "
                   "FROM log, articles "
                   "WHERE path like '%article%' "
                   "AND log.path ~ articles.slug "
                   "GROUP BY path, articles.title "
                   "ORDER BY count(path) desc "
                   "LIMIT 3;")
    data = cursor.fetchall()
    db.close()
    return data


def get_most_popular_article_authors():
    db, cursor = connect('news')
    cursor.execute("SELECT authors.name, count(path) "
                   "FROM log, articles, authors "
                   "WHERE path like '%article%' "
                   "AND log.path ~ articles.slug "
                   "AND authors.id = articles.author "
                   "GROUP BY authors.name "
                   "ORDER BY count(path) desc "
                   "LIMIT 4;")
    data = cursor.fetchall()
    db.close()
    return data


def get_day_with_most_errors():
    db, cursor = connect('news')
    cursor.execute("SELECT to_char(normal.time::date, 'DD/MM/YYYY'), "
                   "CAST(count(err.status) AS float) / CAST(count(normal.status) AS float) * 100 "
                   "FROM log as normal "
                   "FULL JOIN (select * from log where status like '4%') as err "
                   "ON err.time = normal.time "
                   "GROUP BY normal.time::date "
                   "HAVING CAST(count(err.status) AS float) / CAST(count(normal.status) AS float) > 0.01;")
    data = cursor.fetchall()
    db.close()
    return data


def connect(database_name):
    """Connect to the PostgreSQL database.  Returns a database connection."""
    try:
        db = psycopg2.connect("dbname={}".format(database_name))
        c = db.cursor()
        return db, c
    except psycopg2.Error as e:
        print("Unable to connect to database")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
