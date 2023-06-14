import peewee as pw
from playhouse.db_url import connect
from datetime import datetime


db_url = 'sqlite:///sms_validator/sms_validator.db'
db = connect(db_url)


class BaseModel(pw.Model):
    class Meta:
        database = db


class Promoter(BaseModel):
    name = pw.CharField(unique=True)


class Supervisor(BaseModel):
    name = pw.CharField(unique=True)


class Location(BaseModel):
    name = pw.CharField(unique=True)


class Lead(BaseModel):
    promoter = pw.ForeignKeyField(Promoter, backref='leads')
    location = pw.ForeignKeyField(Location, backref='leads')
    supervisor = pw.ForeignKeyField(Supervisor, backref='leads')
    name = pw.CharField()
    direction = pw.CharField()
    type = pw.CharField()
    phone = pw.CharField(null=True)
    created_at = pw.DateTimeField(default=datetime.now)
