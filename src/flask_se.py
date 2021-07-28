# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, make_response, redirect, url_for, jsonify, Response
from flask_frozen import Freezer

import sys, os, json
from datetime import datetime
from se_forms import ThesisFilter
from os.path import splitext
from transliterate import translit
from urllib.parse import urlparse
from sqlalchemy.sql.expression import func
from werkzeug.exceptions import HTTPException

from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_basicauth import BasicAuth
from flask_migrate import Migrate

from se_models import db, init_db, Staff, Users, Thesis, Worktype, Curriculum, SummerSchool, Courses
from wtforms import TextAreaField

app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')

# Flask configs
app.config['APPLICATION_ROOT'] = '/'

# Freezer config
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_DESTINATION'] = '../docs'
app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True

# SQLAlchimy config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///se.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(16).hex()

# Secret for API
app.config['SECRET_KEY_THESIS'] = os.urandom(16).hex()

# Basci auth config
app.config['BASIC_AUTH_USERNAME'] = 'se_staff'
app.config['BASIC_AUTH_PASSWORD'] = app.config['SECRET_KEY_THESIS']

# Init Database
db.app = app
db.init_app(app)

# Init Migrate
migrate = Migrate(app, db)

app.logger.error('SECRET_KEY_THESIS: %s', str(app.config['SECRET_KEY_THESIS']))

# Init Freezer
freezer = Freezer(app)

# Init Sitemap
zero_days_ago = (datetime.now()).date().isoformat()

# Init BasicAuth
basic_auth = BasicAuth(app)

# Extend FlaskAdmin classes for BasicAuth (https://stackoverflow.com/questions/54834648/flask-basicauth-auth-required-decorator-for-flask-admin-views)
"""
The following three classes are inherited from their respective base class,
and are customized, to make flask_admin compatible with BasicAuth.
"""


class AuthException(HTTPException):
    def __init__(self, message):
        super().__init__(message, Response(
            "You could not be authenticated. Please refresh the page.", 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}))


class SeModelView(ModelView):
    def is_accessible(self):
        if not basic_auth.authenticate():
            raise AuthException('Not authenticated.')
        else:
            return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(basic_auth.challenge())


class UsersModelView(ModelView):
    column_exclude_list = ['password_hash']

    def is_accessible(self):
        if not basic_auth.authenticate():
            raise AuthException('Not authenticated.')
        else:
            return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(basic_auth.challenge())


class SummerSchoolView(ModelView):
    form_overrides = {
        'description': TextAreaField,
        'repo': TextAreaField,
        'demos': TextAreaField
    }

    form_widget_args = {
        'description': {
            'rows': 10,
            'style': 'font-family: monospace; width: 680px;'
        },
        'project_name': {
            'style': 'width: 680px;'
        },
        'tech': {
            'rows': 3,
            'style': 'font-family: monospace; width: 680px;'
        },
        'repo': {
            'rows': 3,
            'style': 'font-family: monospace; width: 680px;'
        },
        'demos': {
            'rows': 3,
            'style': 'font-family: monospace; width: 680px;'
        },
        'advisors': {
            'rows': 2,
            'style': 'font-family: monospace; width: 680px;'
        },
        'requirements': {
            'rows': 3,
            'style': 'font-family: monospace; width: 680px;'
        },
    }

    def is_accessible(self):
        if not basic_auth.authenticate():
            raise AuthException('Not authenticated.')
        else:
            return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(basic_auth.challenge())


class StaffModelView(ModelView):
    form_choices = {
        'science_degree': [
            ('', ''),
            ('д.ф.-м.н.', 'д.ф.-м.н.'),
            ('д.т.н.', 'д.т.н.'),
            ('к.ф.-м.н.', 'к.ф.-м.н.'),
            ('к.т.н.', 'к.т.н.')
        ]
    }

    column_exclude_list = ['supervisor', 'adviser']
    form_excluded_columns = ['supervisor', 'adviser']

    def is_accessible(self):
        if not basic_auth.authenticate():
            raise AuthException('Not authenticated.')
        else:
            return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(basic_auth.challenge())


class SeAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not basic_auth.authenticate():
            raise AuthException('Not authenticated.')
        else:
            return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(basic_auth.challenge())


# Init Flask-admin
admin = Admin(app, index_view=SeAdminIndexView())


# Flask routes goes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/index.html')
def indexhtml():
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@app.route('/404.html')
def status_404():
    return render_template('404.html')


@app.route('/contacts.html')
def contacts():
    return render_template('contacts.html')


@app.route('/students/index.html')
def students():
    return render_template('students.html')


@app.route('/students/scholarships.html')
def scholarships():
    return render_template('students_scholarships.html')


@app.route('/bachelor/application.html')
def bachelor_application():
    return render_template('bachelor_application.html')


@app.route('/bachelor/programming-technology.html')
def bachelor_programming_technology():
    curricula1 = Curriculum.query.filter(Curriculum.course_id == 1).filter(Curriculum.study_year == 1).order_by(
        Curriculum.type).all()
    curricula2 = Curriculum.query.filter(Curriculum.course_id == 1).filter(Curriculum.study_year == 2).order_by(
        Curriculum.type).all()
    curricula3 = Curriculum.query.filter(Curriculum.course_id == 1).filter(Curriculum.study_year == 3).order_by(
        Curriculum.type).all()
    curricula4 = Curriculum.query.filter(Curriculum.course_id == 1).filter(Curriculum.study_year == 4).order_by(
        Curriculum.type).all()

    return render_template('bachelor_programming-technology.html', curricula1=curricula1, curricula2=curricula2,
                           curricula3=curricula3, curricula4=curricula4)


@app.route('/bachelor/software-engineering.html')
def bachelor_software_engineering():
    curricula1 = Curriculum.query.filter(Curriculum.course_id == 2).filter(Curriculum.study_year == 1).order_by(
        Curriculum.type).all()
    curricula2 = Curriculum.query.filter(Curriculum.course_id == 2).filter(Curriculum.study_year == 2).order_by(
        Curriculum.type).all()
    curricula3 = Curriculum.query.filter(Curriculum.course_id == 2).filter(Curriculum.study_year == 3).order_by(
        Curriculum.type).all()
    curricula4 = Curriculum.query.filter(Curriculum.course_id == 2).filter(Curriculum.study_year == 4).order_by(
        Curriculum.type).all()

    return render_template('bachelor_software-engineering.html', curricula1=curricula1, curricula2=curricula2,
                           curricula3=curricula3, curricula4=curricula4)


@app.route('/master/information-systems-administration.html')
def master_information_systems_administration():
    return render_template('master_information-systems-administration.html')


@app.route('/master/software-engineering.html')
def master_software_engineering():
    return render_template('master_software-engineering.html')


@app.route('/department/staff.html')
def department_staff():
    records = Staff.query.filter_by(still_working=True).all()
    staff = []

    # TODO: no need loop
    for s in records:
        position = s.position
        if s.science_degree:
            position = position + ", " + s.science_degree

        staff.append({'name': s.user, 'position': position, 'contacts': s.official_email,
                      'avatar': s.user.avatar_uri, 'id': s.id})

    return render_template('department_staff.html', staff=staff)


@app.route('/bachelor/admission.html')
def bachelor_admission():
    students = []

    records = Thesis.query.filter_by(recomended=True)
    if records.count():
        theses = records.order_by(func.random()).limit(4).all()
    else:
        theses = []
    staff = Staff.query.filter_by(still_working=True).limit(6).all()
    return render_template('bachelor_admission.html', students=students, theses=theses, staff=staff)


@app.route('/frequently-asked-questions.html')
def frequently_asked_questions():
    return render_template('frequently_asked_questions.html')


@app.route('/nooffer.html')
def nooffer():
    return render_template('nooffer.html')


@app.route('/theses.html')
def theses_search():
    filter = ThesisFilter()
    filter.worktype.choices = [(worktype.id, worktype.type) for worktype in Worktype.query.all()]

    for sid in Thesis.query.with_entities(Thesis.course_id).distinct().all():
        course = Courses.query.filter_by(id=sid[0]).first()

        filter.course.choices.append((sid[0], course.name))
        filter.course.choices.sort(key=lambda tup: tup[1])
    filter.course.choices.insert(0, (0, 'Все'))

    dates = [theses.publish_year for theses in
             Thesis.query.filter(Thesis.temporary == False).with_entities(Thesis.publish_year).distinct()]
    dates.sort(reverse=True)
    filter.startdate.choices = dates
    filter.enddate.choices = dates

    for sid in Thesis.query.with_entities(Thesis.supervisor_id).distinct().all():
        staff = Staff.query.filter_by(id=sid[0]).first()
        last_name = ""
        initials = ""

        if staff.user.last_name:
            last_name = staff.user.last_name

        if staff.user.first_name:
            initials = initials + staff.user.first_name[0] + "."

        if staff.user.middle_name:
            initials = initials + staff.user.middle_name[0] + "."

        filter.supervisor.choices.append((sid[0], last_name + " " + initials))
        filter.supervisor.choices.sort(key=lambda tup: tup[1])

    filter.supervisor.choices.insert(0, (0, "Все"))

    return render_template('theses.html', filter=filter)


@app.route('/fetch_theses')
def fetch_theses():
    worktype = request.args.get('worktype', default=1, type=int)
    page = request.args.get('page', default=1, type=int)
    supervisor = request.args.get('supervisor', default=0, type=int)
    course = request.args.get('course', default=0, type=int)

    dates = [theses.publish_year for theses in
             Thesis.query.filter(Thesis.temporary == False).with_entities(Thesis.publish_year).distinct()]
    dates.sort(reverse=True)

    if dates:
        startdate = request.args.get('startdate', default=dates[-1], type=int)
        enddate = request.args.get('enddate', default=dates[0], type=int)
    else:
        startdate = 2020
        enddate = 2020

    # Check if end date less than start date
    if enddate < startdate:
        enddate = startdate

    records = Thesis.query.filter(Thesis.temporary == False).filter(Thesis.publish_year >= startdate).filter(
        Thesis.publish_year <= enddate).order_by(Thesis.publish_year.desc())

    if course:

        # Check if course exists
        ids = Thesis.query.with_entities(Thesis.course_id).distinct().all()
        if [item for item in ids if item[0] == course]:
            records = records.filter(Thesis.course_id == course)
        else:
            course = 0

    if supervisor:

        # Check if supervisor exists
        ids = Thesis.query.with_entities(Thesis.supervisor_id).distinct().all()
        if [item for item in ids if item[0] == supervisor]:
            records = records.filter(Thesis.supervisor_id == supervisor)
        else:
            supervisor = 0

    if worktype > 1:
        records = records.filter_by(type_id=worktype).paginate(per_page=10, page=page, error_out=False)
    else:
        records = records.paginate(per_page=10, page=page, error_out=False)

    if len(records.items):
        return render_template('fetch_theses.html', theses=records, worktype=worktype, course=course, startdate=startdate,
                               enddate=enddate, supervisor=supervisor)
    else:
        return render_template('fetch_theses_blank.html')


@app.route('/post_theses', methods=['GET', 'POST'])
def post_theses():
    error_status = 500
    success_status = 0
    thesis_text = None
    presentation = None
    supervisor_review = None
    reviewer_review = None
    thesis_info = None
    source_uri = None

    thesis_filename = None
    presentation_filename = None
    supervisor_review_filename = None
    reviewer_review_filename = None

    type_id_string = ['', 'Bachelor_Report', 'Bachelor_Thesis', 'Master_Thesis']
    supervisor_id = None

    if 'thesis_text' in request.files:
        thesis_text = request.files['thesis_text']

    if 'presentation' in request.files:
        presentation = request.files['presentation']

    if 'supervisor_review' in request.files:
        supervisor_review = request.files['supervisor_review']

    if 'reviewer_review' in request.files:
        reviewer_review = request.files['reviewer_review']

    if 'thesis_info' in request.files:
        thesis_info = json.load(request.files['thesis_info'])

    if not thesis_text:
        return jsonify(
            status=error_status,
            string='No thesis text found.'
        )

    if not thesis_info:
        return jsonify(
            status=error_status,
            string='No thesis_info found.'
        )

    try:
        name_ru = thesis_info['name_ru']
        secret_key = thesis_info['secret_key']
        type_id = thesis_info['type_id']
        course_id = thesis_info['course_id']
        author = thesis_info['author']
        supervisor = thesis_info['supervisor']
        publish_year = thesis_info['publish_year']
    except KeyError as e:
        return jsonify(
            status=error_status,
            string='Key ' + str(e) + ' not found'
        )

    if secret_key != app.config['SECRET_KEY_THESIS']:
        return jsonify(
            status=error_status,
            string='Invalid secret key: ' + str(secret_key)
        )

    if 'source_uri' in thesis_info:
        source_uri = thesis_info['source_uri']

    if type_id < 2 or type_id > len(type_id_string):
        return jsonify(
            status=error_status,
            string='Wrong type_id: ' + str(type_id)
        )

    if course_id < 1 or course_id > 7:
        return jsonify(
            status=error_status,
            string='Wrong course_id: ' + str(course_id)
        )

    # Try to get SuperVisor Id
    q = Users.query.filter_by(last_name=supervisor).first()
    if q:
        r = Staff.query.filter_by(user_id=q.id).first()
        supervisor_id = r.id
    else:
        return jsonify(
            status=error_status,
            string='Can\'t find supervisor: ' + str(supervisor)
        )

    author_en = translit(author, 'ru', reversed=True)
    author_en = author_en.replace(" ", "_")
    thesis_filename = author_en
    thesis_filename = thesis_filename + '_' + type_id_string[type_id - 1]
    thesis_filename = thesis_filename + '_' + str(publish_year) + '_text'

    path = urlparse(thesis_text.filename).path
    extension = splitext(path)[1]
    thesis_filename = thesis_filename + extension

    # Before we going on, check if this thesis already exists?
    records = Thesis.query.filter_by(text_uri=thesis_filename)
    if records.count():
        return jsonify(
            status=error_status,
            string='Work already exists: ' + str(thesis_filename)
        )

    # Save file to TMP
    thesis_text.save(os.path.join('./static/tmp/texts/', thesis_filename))

    if presentation:
        presentation_filename = author_en
        presentation_filename = presentation_filename + '_' + type_id_string[type_id - 1]
        presentation_filename = presentation_filename + '_' + str(publish_year) + '_slides'

        path = urlparse(presentation.filename).path
        extension = splitext(path)[1]
        presentation_filename = presentation_filename + extension

        presentation.save(os.path.join('./static/tmp/slides/', presentation_filename))

    if supervisor_review:
        supervisor_review_filename = author_en
        supervisor_review_filename = supervisor_review_filename + '_' + type_id_string[type_id - 1]
        supervisor_review_filename = supervisor_review_filename + '_' + str(publish_year) + '_supervisor_review'

        path = urlparse(supervisor_review.filename).path
        extension = splitext(path)[1]
        supervisor_review_filename = supervisor_review_filename + extension

        supervisor_review.save(os.path.join('./static/tmp/reviews/', supervisor_review_filename))

    if reviewer_review:
        reviewer_review_filename = author_en
        reviewer_review_filename = reviewer_review_filename + '_' + type_id_string[type_id - 1]
        reviewer_review_filename = reviewer_review_filename + '_' + str(publish_year) + '_reviewer_review'

        path = urlparse(reviewer_review.filename).path
        extension = splitext(path)[1]
        reviewer_review_filename = reviewer_review_filename + extension

        reviewer_review.save(os.path.join('./static/tmp/reviews/', reviewer_review_filename))

    if source_uri:
        t = Thesis(name_ru=name_ru, text_uri=thesis_filename,
                   presentation_uri=presentation_filename,
                   supervisor_review_uri=supervisor_review_filename, reviewer_review_uri=reviewer_review_filename,
                   author=author, supervisor_id=supervisor_id, reviewer_id=2,
                   publish_year=publish_year, type_id=type_id, course_id=course_id, source_uri=source_uri,
                   temporary=True)
    else:
        t = Thesis(name_ru=name_ru, text_uri=thesis_filename,
                   presentation_uri=presentation_filename,
                   supervisor_review_uri=supervisor_review_filename, reviewer_review_uri=reviewer_review_filename,
                   author=author, supervisor_id=supervisor_id, reviewer_id=2,
                   publish_year=publish_year, type_id=type_id, course_id=course_id,
                   temporary=True)

    db.session.add(t)

    try:
        db.session.commit()
    except AssertionError as err:
        db.session.rollback()
        app.logger.error(err)
    except Exception as err:
        db.session.rollback()
        app.logger.error(err)

    return jsonify(
        status=success_status,
        string='Success'
    )


@app.route('/theses_tmp.html')
def theses_tmp():
    records = Thesis.query.filter_by(temporary=True)
    return render_template('theses_tmp.html', theses=records)


@app.route('/theses_delete_tmp')
def theses_delete_tmp():
    thesis_id = request.args.get('thesis_id', default=1, type=int)
    thesis = Thesis.query.filter_by(id=thesis_id).filter_by(temporary=True).first()

    if thesis:
        db.session.delete(thesis)
        db.session.commit()

    return redirect(url_for('theses_tmp'))


@app.route('/theses_add_tmp')
def theses_add_tmp():
    thesis_id = request.args.get('thesis_id', default=1, type=int)
    thesis = Thesis.query.filter_by(id=thesis_id).filter_by(temporary=True).first()

    if thesis:
        thesis.temporary = False
        db.session.commit()

        if thesis.text_uri:
            os.rename('./static/tmp/texts/' + thesis.text_uri, './static/thesis/texts/' + thesis.text_uri)

        if thesis.presentation_uri:
            os.rename('./static/tmp/slides/' + thesis.presentation_uri,
                      './static/thesis/slides/' + thesis.presentation_uri)

        if thesis.supervisor_review_uri:
            os.rename('./static/tmp/reviews/' + thesis.supervisor_review_uri,
                      './static/thesis/reviews/' + thesis.supervisor_review_uri)

        if thesis.reviewer_review_uri:
            os.rename('./static/tmp/reviews/' + thesis.reviewer_review_uri,
                      './static/thesis/reviews/' + thesis.reviewer_review_uri)

    return redirect(url_for('theses_tmp'))


@app.route('/summer_school_2021.html')
def summer_school():
    projects = SummerSchool.query.filter_by(year=2021).all()
    return render_template('summer_school.html', projects=projects)


@app.route('/sitemap.xml', methods=['GET'])
@app.route('/Sitemap.xml', methods=['GET'])
def sitemap():
    """Generate sitemap.xml. Makes a list of urls and date modified."""
    pages = []
    skip_pages = ['/nooffer.html', '/fetch_theses', '/Sitemap.xml', '/sitemap.xml', '/404.html', '/post_theses',
                  '/theses_tmp.html', '/theses_delete_tmp', '/theses_add_tmp']

    # static pages
    for rule in app.url_map.iter_rules():

        if rule.rule in skip_pages:
            continue

        if "GET" in rule.methods and len(rule.arguments) == 0:
            pages.append(
                ["https://se.math.spbu.ru" + str(rule.rule), zero_days_ago]
            )

    sitemap_xml = render_template('sitemap_template.xml', pages=pages)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response


# Add views to the Flask-admin
admin.add_view(UsersModelView(Users, db.session))
admin.add_view(StaffModelView(Staff, db.session))
admin.add_view(SeModelView(Thesis, db.session))
admin.add_view(SummerSchoolView(SummerSchool, db.session))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "build":
            freezer.freeze()
        elif sys.argv[1] == "init":
            init_db()
    else:
        app.run(port=5000, debug=True)
