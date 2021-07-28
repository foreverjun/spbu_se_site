from flask_wtf import FlaskForm
from wtforms import SelectField


class ThesisFilter(FlaskForm):
    worktype = SelectField('worktype', choices=[])
    course = SelectField('course', choices=[])
    supervisor = SelectField('supervisor', choices=[])
    startdate = SelectField('startdate', choices=[])
    enddate = SelectField('enddate', choices=[])
