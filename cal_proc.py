import _mysql
import cgi
from datetime import datetime



method_type = get_method_type()
form = cgi.FieldStorage() 

if method_type == 'POST':
	event_name = form['event_name'].value
    location = form['location'].value
    time = form['time'].value
    #connect to database:
    cnx = _mysql.connect(user='amya_davebam',passwd='S3Dc3tdf',db='amya_davebam') 
    #create a mySQL query and commit to database relevant information for logging event
	query = ("INSERT INTO calendar_events (event_name,location,time) VALUES ('%s','%s','%s')" %(event_name,location,time))
	cnx.query(query)
	cnx.commit()

elif method_type == 'GET':
	event_name = form['event_name'].value
	cnx = _mysql.connect(user='amya_davebam', passwd='S3Dc3tdf',db='amya_davebam')
	query = ("SELECT * FROM calendar_events")
	cnx.query(query)
	results = cnx.store_result()
	table = result.fetch_row(maxrows=0,how=0)
	events = []
	for row in table:
		events.append([e.decode('utf-8') if type(e) is bytes else e for e in row])
	for event in events:
		event_name = event[0]
		location = event[1]
		time = event[2]
		date_n_time = datetime.strptime(time, '%d/%m/%Y %H:%M:%S')

