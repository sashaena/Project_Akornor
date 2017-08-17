from flask import Flask, session, render_template, request, redirect, url_for, escape, flash
import requests, uuid, os, face_recognition as fr
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_ , exc
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
from sqlalchemy.exc import IntegrityError
from flask_sockets import Sockets
import base64, json
from flask import send_from_directory

# import flask_whooshalchemy as wa
# import unicodedata

UPLOADED_FOLDER = join(dirname(realpath(__file__)),'images')
# UPLOAD_FOLDER_ENCODING = join(dirname(realpath(__file__)),'images_encodings')

ALLOWED_EXTENTIONS = set(['jpg', 'jpeg'])

# initialize the flask app
app = Flask(__name__)
sockets = Sockets(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student.db'
#allows whooshalchemy to know if something has changed so set to true. By default it is enabled
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UPLOAD_FOLDER'] = UPLOADED_FOLDER
# app.config['UPLOAD_FOLDER_ENCODING'] = UPLOAD_FOLDER_ENCODINGS



#initialize sqlalchemy database object
db = SQLAlchemy(app)

app.secret_key = os.urandom(24)

# This is a mock databse
class Student(db.Model):
	# __searchable__ = ['firstname','lastname','year_group']
	"""docstring for student"""
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.Integer, unique=True)
	firstname = db.Column(db.String(90))
	lastname = db.Column(db.String(120))
	year_group = db.Column(db.String(10))

	def __init__(self, student_id, firstname, lastname, year_group):
		# super(student, self).__init__()
		self.student_id = student_id
		self.firstname = firstname
		self.lastname = lastname
		self.year_group = year_group

	def __repr__(self):
		return '<Student %r>' % self.firstname 

class Face_recognition_database(db.Model):
	"""docstring for face_recognition_database"""
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.Integer, unique=True)
	firstname = db.Column(db.String(120), unique=True)
	lastname = db.Column(db.String(120), unique=True)
	year_group = db.Column(db.String(10))
	face_encodings = db.Column(db.String, unique=True)


	def __init__(self, student_id, firstname, lastname, year_group, face_encodings):
		# super(face_recognition_database, self).__init__()
		self.student_id = student_id
		self.firstname = firstname
		self.lastname = lastname
		self.year_group = year_group
		self.face_encodings = face_encodings
		

	def __repr__(self):
		return '<Face_recognition_database %r>' % self.firstname     


#creating whoosh index(pass in app and the name of your databse class)
# wa.whoosh_index(app, Student) 

# first function describing the login
@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		res = login(email, password)
		if res:
			session['key'] = res
			return redirect(url_for('search'))
		else:
			flash("Retype details")
	return render_template('index.html')

	
@app.route('/search', methods=['GET'])
def search():
	if 'key' in session:
		value = request.args.get('query')
		students = []
		if value:
			#This is a less accurate way to search thrugh a databse with wild cards ie like....
			students = Student.query.filter(or_(Student.firstname.like("%"+value+"%"), Student.lastname.like("%"+value+"%"))).all()
			print(students)
			# students = Student.query.whoosh_search(value).all()
			# print('You tried to search for:', students)		
		return render_template('search.html', students=students)
	return redirect(url_for('index'))

def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENTIONS

@app.route('/learn', methods=['GET', 'POST'])
def learn():
	if 'key' in session:
		#getting the id a student based on the link clicked ie. user input
		id = request.args['id']
		#getting the rest of student info based on the single id(use the id to search through the database and stores corresponding information about student)
		student = Student.query.filter_by(id=id).first()
		print('STUDENT',student)
		print(id)

		# if 'file' not in request.files:
		# 	flash ('Zero!')
		# 	return redirect(request.url)
		# else:
		# 	file = request.files['file']
		# 	if file.filename == '':
		# 		return redirect (request.url)
		if request.method == 'POST':
			file = request.files['file']
			if file and allowed_file(file.filename):
				filename = secure_filename(str(student.student_id) + '.jpg')
				file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
				# print('Requests!!!! : ', request.args['firstname'], request.args['lastname'], request.args['year_group'], request.args['student_id'])
				# firstname = request.args['firstname']
				# lastname = request.args['lastname']
				# year_group = request.args['year_group']
				# student_id = request.args['student_id']
	
				generate_face_encoding = generate_face_encodings(file, id, student.firstname, student.lastname, student.year_group, student.student_id)
				if generate_face_encoding:
					flash('STUDENT STORED')
					print("student stored")
				else:
					flash('ERRoR!')
					print('error')
				return render_template('learn.html', student=student)
		return render_template('learn.html', student=student)
	return redirect(url_for('index'))

@sockets.route('/webSocket')
def webSocket(webS):
	while True:
		# get a message from the client wither in the form of text or images
		message = webS.receive()
		# raw = message.decode('utf8')

		if message == None:
			none_error = {"error": "Message sent is null"}
			webS.send(json.dumps(none_error))

		# this is a check mechanism to make sure that message received is an image file
		head = "data:image/jpeg;base64,"
		# if the head which contains a what makes the message an image is an image
		if(head in message):
			print("1")
			# base64 allows you to store images as strings
			# decode the image and extract the rest of the message out
			imgdata = base64.b64decode(message[len(head):])
			filename = secure_filename("temp.jpg")
			try:
				with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'wb') as imgFile:
					imgFile.write(imgdata)
					res = check_face_encodings(filename)
					if res:
						res_dict = {"name":res.firstname + " " + res.lastname, "id":res.student_id}
						webS.send(json.dumps(res_dict))
					else:
						error_dict = {"error":"Could not recognize face"}
						webS.send(json.dumps(error_dict))
			except OSError:
				os_error = {"error":"Hold on for a bit"}
				webS.send(json.dumps(os_error))

		else:
			print("0")



@app.route('/rec')
def rec():
	if 'key' in session:
		return render_template('rec.html')

@app.route('/upload/<filename>')
def get_uploaded_file(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/account')
def account():
	if 'key' in session:
		return render_template('account.html')
	return redirect(url_for('index'))

def login(email, password):
# give some mock credentials so as to get feedback
	if email == 'akornor.canteen@ashesi.edu.gh':
		if password == 'akornor':
			return "hello"
	return None

def generate_face_encodings(file, id, firstname, lastname, year_group, student_id,):
	try:
		# Filename stores the complete path of where the image file is plus the name of the file
		# There is no need to get into the database to get the student by the id because this has
		# already been passed in the generate_face_encoding
		filename = os.path.join(app.config['UPLOAD_FOLDER'], str(student_id) + ".jpg")
		# student = Student.query.filter_by(id=id).first()
		image_file = fr.load_image_file(filename)
		f_encodings = fr.face_encodings(image_file)[0]
		print ("face encodings = " , f_encodings)
		encodings_string = "|".join(map(str, f_encodings))
		print("encoding string =", encodings_string)

		student_encodings = Face_recognition_database(student_id, firstname, lastname, year_group, encodings_string)
		db.session.add(student_encodings)
		db.session.commit()

	except exc.IntegrityError as e:
	# better way to do this is to flash a modal-------To do
		# flash ("Student already in database")
		db.session.rollback()
		return False
	return True

def check_face_encodings(filename):
	image = fr.load_image_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	encoding_list = fr.face_encodings(image)
	if len(encoding_list) > 0:
		u_encoding = encoding_list[0]
		print("Generated encoding! " + str(len(encoding_list)))
		# get into the database and get all its records
		all_records = Face_recognition_database.query.all()
		# for each record in the records from the database
		for record in all_records:
			#create an empty string called encoding
			encodings = []
			splitted = record.face_encodings.split("|")
			encodings.append([float (ir) for ir in splitted])
			match = fr.compare_faces(encodings, u_encoding, 0.5)
			print(match, "matched")

			if match[0] == True:
				return record
		return None
				# tru = records.face_encodings
			# else:
			# 	return None
				


			# try:
			# 	position = match.index(True)
			# 	name = records[position][1]
			# 	print(name, "name")
			# except:
			# 	name = 'Not sure'

			# faces_names.append(name)


			# if u_encoding == record.face_encodings:
			# 	student_id = record.student_id
			# 	firstname , lastname = record.firstname, record.lastname 
			# 	print ('Student with an ID number of ', student_id, 'and name', firstname , lastname, 'has been matched correctly')
	
		# print("Could not generate encoding :(;")


if __name__ == "__main__":
	# app.run(debug=True)
	from gevent import pywsgi
	from geventwebsocket.handler import WebSocketHandler
	server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
	server.serve_forever()

