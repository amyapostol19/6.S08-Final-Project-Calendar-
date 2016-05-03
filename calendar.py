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

        cnx = _mysql.connect(user='amya_davebam', passwd='S3Dc3tdf',db='amya_davebam')
        #access database, pull event and relevant information:
        query = ("SELECT * FROM calendar_events")
        cnx.query(query)
        results = cnx.store_result()
        table = results.fetch_row(maxrows=0,how=0)
        events = []
        for row in table:
                events.append([e.decode('utf-8') if type(e) is bytes else e for e in row])
        if len(events) > 0:
                for i in range(3,len(events)):
                        event = events[i]
                        event_name = event[2]
                        location = event[3]
                        time = event[4]
                        event_info = {}

                        time_obj = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
                        time_delta = datetime.now() - time_obj
                        if time_delta.total_seconds() <= 86400:
                
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

                                if len(routes) > 0:
                                        legs = routes[0]['legs']
                                        duration = legs[0]['duration']
                                        distance = legs[0]['distance']
                                        steps = legs[0]['steps']
                                        duration_seconds = duration['value']
                                        distance_meters = distance['value']
                                        
                                        step_instructions = []
                                        for i in range(len(steps)):
                                                current_step = steps[i]
                                                step_instructions.append(current_step['html_instructions'])
                                
                                        duration_mins = duration_seconds/60
                                        if time_delta.total_seconds() <= (duration_seconds + 300):
                                                time_statement = ("It will take you about %.1f minutes to arrive. You should leave for %s now." %(duration_mins, event_name))

                                        event_info["<b>event</b>"] = []
                                        for i in range(len(event)):
                                                event_info["<b>event</b>"].append(event[i])
                                        event_info["<b>duration_seconds</b>"] = duration_seconds
                                        event_info["<b>distance_meters</b>"] = distance_meters
                                        event_info["<b>step_instructions</b>"] = step_instructions
                                        event_info["<b>time_statement</b>"] = time_statement

                                        print(event_info)
                                        print("<br>")

                                else:
                                        print("No directions found to %s." %event_name)
                
        else:
                print("Database Error")
                

        
        
        


