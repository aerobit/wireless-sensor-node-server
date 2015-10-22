import time
import json
import datetime

import tornado.web
import settings
import tornado
from data import Session, Reading, Setpoint, Name
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound


class HistoricalReadingsHandler(tornado.web.RequestHandler):
    def get(self):
        sess = Session()

        self.set_header("Content-Type", "application/json")

        self.write('{"num_nodes":3,"readings":[')
        i = 0
        last_timestamp = {}
        now = datetime.datetime.utcnow()
        one_month_ago = now - datetime.timedelta(days=30)
        one_year_ago = now - datetime.timedelta(days=365)
        one_week_ago = now - datetime.timedelta(days=7)
        one_day_ago = now - datetime.timedelta(days=1)
        for r in (sess.query(Reading).
                      filter(Reading.checksum_calc == Reading.checksum_sent).
                      filter(Reading.created_at > one_year_ago).
                      order_by(Reading.created_at)):
            if r.created_at < one_month_ago:
                min_delta = datetime.timedelta(hours=4)
            elif r.created_at < one_week_ago:
                min_delta = datetime.timedelta(hours=2)
            elif r.created_at < one_day_ago:
                min_delta = datetime.timedelta(hours=1)
            else:
                min_delta = datetime.timedelta()
            if (last_timestamp.get(r.node_id, None) is None or
                r.created_at > last_timestamp[r.node_id] + min_delta):
                self.write(("" if i == 0 else ",") +
                       json.dumps([time.mktime(r.created_at.timetuple()), #@UndefinedVariable
                                     r.reading if r.node_id == 1 else None,
                                     r.reading if r.node_id == 2 else None,
                                     r.reading if r.node_id == 3 else None]))
                last_timestamp[r.node_id] = r.created_at
            i += 1
            if (i % 20) == 0:
                self.flush()

        self.finish("]}")

class TemperaturesHandler(tornado.web.RequestHandler):
    def get(self):
        sess = Session()
        self.set_header("Content-Type", "application/json")
        node_ids = sess.query(Reading.node_id).distinct().all()
        i = 0
        self.write('{"readings":[')
        for node_id in [node_id[0] for node_id in node_ids]:
            reading = sess.query(Reading).filter(Reading.node_id == node_id).order_by(desc(Reading.created_at)).first()
            setpoint = sess.query(Setpoint).filter(Setpoint.zone_id == node_id).order_by(desc(Setpoint.created_at)).first()
            try:
                name = sess.query(Name).filter(Name.zone_id == node_id).one().name
            except NoResultFound:
                name = node_id
            self.write(("" if i == 0 else ",") + 
                json.dumps({'id':node_id, 'name':name, 'desired':setpoint.temperature, 'actual':reading.reading}))
            i += 1
        self.flush()
        self.finish("]}")

class SetpointsHandler(tornado.web.RequestHandler):
    def post(self):
        sess = Session()
        zone_id = self.get_argument('id')
        temperature = self.get_argument('temperature')
        setpoint = Setpoint()
        setpoint.zone_id = int(zone_id)
        setpoint.temperature = float(temperature)
        sess.add(setpoint)
        sess.commit()

class NameHandler(tornado.web.RequestHandler):
    def post(self):
        sess = Session()
        zone_id = self.get_argument('id')
        new_name = self.get_argument('name')
        try:
            name = sess.query(Name).filter(Name.zone_id == zone_id).one()
        except NoResultFound:
            name = Name()
            name.zone_id = int(zone_id)
        name.name = new_name
        sess.add(name)
        sess.commit()

URLS = [
    (r'^/historicalreadings/?$', HistoricalReadingsHandler),
    (r'^/setpoints/?$', SetpointsHandler),
    (r'^/temperatures/?$', TemperaturesHandler),
    (r'^/names/?$', NameHandler),
    (r'^/(.*)$', tornado.web.StaticFileHandler, {"path": settings.STATIC_DIR, "default_filename": "index.html"}),
]
