import _mysql
import urllib.request
import urllib.parse
import cgi
from datetime import datetime
import json
import re
import codecs

exec(open("/var/www/html/student_code/LIBS/s08libs.py").read())
print( "Content-type:text/html\r\n\r\n")

api_key = "AIzaSyCij-F-zB3y7MbjL4C7LgcI64BFqoYweI0"


method_type = get_method_type()
form = cgi.FieldStorage() 

if method_type == 'POST':

        event_name = form['event_name'].value
        location = form['location'].value
        time = form['time'].value
        #connect to database:
        cnx = _mysql.connect(user='amya_davebam', passwd='S3Dc3tdf',db='amya_davebam') 
        #create a mySQL query and commit to database relevant information for logging event
        query = ("INSERT INTO calendar_events (event_name, location, time) VALUES ('%s','%s','%s')" %(event_name,location,time))
        cnx.query(query)
        cnx.commit()

elif method_type == 'GET':

        event = form['event_name'].value
        cnx = _mysql.connect(user='amya_davebam', passwd='S3Dc3tdf',db='amya_davebam')
        #access database, pull event and relevant information:
        query = ("SELECT * FROM calendar_events WHERE event_name='%s'" %event)
        cnx.query(query)
        results = cnx.store_result()
        table = results.fetch_row(maxrows=0,how=0)
        events = []
        for row in table:
                events.append([e.decode('utf-8') if type(e) is bytes else e for e in row])
        if len(events) > 0:
                print(events)
                event_name = events[0][2]
                location = events[0][3]
                time = events[0][4]

        

                #sending request to Google Directions API:   
                home = "Maseeh Hall"
                mass_loc = location + " Boston, MA"
                url_home = urllib.parse.quote(home)
                url_loc = urllib.parse.quote(mass_loc)
                api_url = "https://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&mode=walking&region=us&key=%s" %(url_home,url_loc,api_key)
                api_resp = urllib.request.urlopen(api_url)
                api_content = api_resp.read().decode('utf-8')
                result = json.loads(api_content)

                points = result['geocoded_waypoints']
                pi_1 = points[0]['place_id']
                pi_2 = points[1]['place_id']
                routes = result['routes']
                status = result['status']

                print(pi_1,pi_2)
                print(status)
                if len(routes) > 0:
                        legs = routes[0]['legs']
                        duration = legs[0]['duration']
                        distance = legs[0]['distance']
                        steps = legs[0]['steps']
                        duration_seconds = duration['value']
                        distance_meters = distance['value']
                        print(duration_seconds, distance_meters)
                        step_instructions = []
                        for i in range(len(steps)):
                                current_step = steps[i]
                                step_instructions.append(current_step['html_instructions'])
                        

                
                time_obj = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                time_d = datetime.now() - time_obj
                duration_mins = duration_seconds/60
                
                if time_d.total_seconds() <= duration_seconds:
                        print("It will take you about %.1f minutes to arrive. You should leave for %s now." %(duration_mins, event_name))
                	print(step_instructions)
                	
        else:
                print("Database Error")

        
        
        


