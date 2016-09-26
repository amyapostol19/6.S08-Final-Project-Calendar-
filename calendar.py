import _mysql
import urllib.request
import urllib.parse
import cgi
from datetime import datetime
import json
import re
import codecs
import html.parser

exec(open("/var/www/html/student_code/LIBS/s08libs.py").read())
print( "Content-type:text/html\r\n\r\n")
print('<html>')

api_key = "AIzaSyCij-F-zB3y7MbjL4C7LgcI64BFqoYweI0"


method_type = get_method_type()
form = cgi.FieldStorage() 

if method_type == 'POST':

        event_name = form['event_name'].value
        location = form['location'].value
        time = form['time'].value
        #connect to database:
        cnx = _mysql.connect(user='amya_davebam', passwd='S3Dc3tdf',db='amya_davebam') 
        #make sure that the time was correctly entered; otherwise, the database converts it to '0000-00-00 00:00:00'
        if time[4] == '-' and time[7] == '-' and time[13] == ':' and time[16] == ':':
                #create a mySQL query and commit to database relevant information for logging event
                query = ("INSERT INTO calendar_events (event_name, location, time) VALUES ('%s','%s','%s')" %(event_name,location,time))
                cnx.query(query)
                cnx.commit()
        else:
                print("Event time incorrectly formatted. Please submit another event.")

elif method_type == 'GET':
        origin = form['origin'].value + " Boston, MA"
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
                event_list = []
                for i in range(len(events)):
                        event = events[i]
                        event_name = event[2]
                        location = event[3]
                        time = event[4]
                        event_data = {}

                        #gathering API info on events within next 24 hours
                        time_obj = datetime.strptime(time, "%Y-%m-%d %H:%M:%S") 
                        time_delta = time_obj - datetime.now()
                        if time_delta.total_seconds() <= 86400 and time_delta.total_seconds() >= 0 and location != origin:

                                #sending request to Google Directions API:   
                                mass_loc = location + " Boston, MA"
                                url_origin = urllib.parse.quote(origin)
                                url_loc = urllib.parse.quote(mass_loc)
                                api_url = "https://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&mode=walking&region=us&key=%s" %(url_origin,url_loc,api_key)
                                api_resp = urllib.request.urlopen(api_url)
                                api_content = api_resp.read().decode('utf-8')
                                result = json.loads(api_content)

                                #unpacking API data
                                points = result['geocoded_waypoints']
                                pi_1 = points[0]['place_id']
                                pi_2 = points[1]['place_id']
                                routes = result['routes']
                                status = result['status']


                                if len(routes) > 0:
                                        #pulling info from json response, assigning to variables
                                        legs = routes[0]['legs'] #'legs' contains each 'leg' of the trip, from one destination to another; thus we only have 1 leg
                                        duration = legs[0]['duration']
                                        distance = legs[0]['distance']
                                        steps = legs[0]['steps'] #steps gives us detailed information for each directional step of each leg (only 1 here)
                                        duration_seconds = duration['value']
                                        distance_meters = distance['value']
                                        
                                        step_instructions = []
                                        #putting together a list of the step-by-step directions
                                        for i in range(len(steps)):
                                                current_step = steps[i]

                                                string = current_step['html_instructions']

                                                #parsing out the HTML tags, which aren't compatible with Teensy touchscreen display
                                                split1 = string.split('<b>')
                                                first_step = ''
                                                for i in range(len(split1)):
                                                        first_step += split1[i]
                                                        
                                                split2 = first_step.split('</b>')
                                                second_step = ''
                                                for i in range(len(split2)):
                                                        second_step += split2[i]

                                                #this <div style="font-size:0.9em"> tag is sometimes included for sub-instructions,
                                                #like 'the destination will be on your right'; if these are present, this 
                                                #block finds them, parses them out, and adds the main instruction and sub-instruction 
                                                #as separate steps to the overall list
                                                font_tag = '<div style="font-size:0.9em">'
                                                font_endtag = '</div>'
                                                if second_step.find(font_tag) != -1:
                                                        ind_1 = second_step.index(font_tag)+ len(font_tag)
                                                        ind_2 = second_step.index(font_endtag)
                                                        sub_direction = second_step[ind_1:ind_2]

                                                        multi_direction = []
                                                        multi_direction.append(second_step[:second_step.index(font_tag)])
                                                        multi_direction.append(sub_direction)

                                                        for i in range(len(multi_direction)):
                                                                step_instructions.append(multi_direction[i])

                                                        second_step = multi_direction[0] + multi_direction[1]
                                                else:
                                                        step_instructions.append(second_step)
                                
                                        duration_mins = duration_seconds/60
                                        time_statement = ""
                                        #if scheduled event time is within duration of trip + 5min, creates a string relaying this info
                                        #this string is used later on as a conditional to determine whether or not to print to the display 
                                        if time_delta.total_seconds() <= (duration_seconds + 300) and time_delta.total_seconds() >= 0:
                                                time_statement = ("It will take you about %.1f minutes to arrive to %s at %s. %s" %(duration_mins, event_name, location, "You're going to be late!" if time_delta.total_seconds()<duration_seconds else "You should leave soon."))

                                        #the 'event_info' list contains all the database-sourced info for each event
                                        event_data["event_info"] = []
                                        for i in range(len(event)):
                                                event_data["event_info"].append(event[i])

                                        #each event has a dictionary of relevant information
                                        event_data["duration_seconds"] = duration_seconds
                                        event_data["distance_meters"] = distance_meters
                                        event_data["step_instructions"] = step_instructions
                                        event_data["time_statement"] = time_statement
                                        event_data["direction_error"] = ''

                                        #'event_list' is a list of 'event_data' dictionaries, one for each event
                                        event_list.append(event_data)
                                        

                                else:
                                        event_data['direction_error'] = ("No directions found to %s." %event_name)
                        
                
                print("You have %s scheduled for the next 24 hours%s" %(("1 event" if len(event_list)==1 else (str(len(event_list))+" events") if len(event_list) > 1 else "no events"),(":" if len(event_list) > 0 else ".")))

                if len(event_list) > 0:
                        for i in range(len(event_list)):
                                event = event_list[i]
                                time = event["event_info"][4] #YYYY-MM-DD HH:MM:SS
                                year = time[2:4]
                                month = time[5:7]
                                day = time[8:10]
                                hour = time[11:13]
                                minute = time[14:16]

                                #reformatting the date and time 
                                info_marker = month+"/"+day+"/"+year+", "
                                if hour == '00':
                                        info_marker += "12:"+minute+" am, "
                                else:
                                        if int(hour) <= 12:
                                                info_marker += hour+":"+minute
                                        else:
                                                info_marker += str(int(hour)-12)+":"+minute
                                        if int(hour) < 12:
                                                info_marker += " am, "
                                        else:
                                                info_marker += " pm, "
                                info_marker += event["event_info"][3]




                                print("> "+event["event_info"][2]+" ("+info_marker+")")
                        print('')
                        for i in range(len(event_list)):
                                event = event_list[i]
                                if event['time_statement'] != '': #using the earlier time_statement string to determine whether or not to send alert and directions
                                                print(event['time_statement'])
                                                print('')
                                                if event['direction_error'] != '':
                                                        print(event['direction_error'])
                                                else:
                                                        print('Directions:')
                                                        for i in range(len(event['step_instructions'])):
                                                                print("("+str(i+1)+") "+event['step_instructions'][i])
                                                        print('')


        else:
                print("Database Error")

print('</html>')
                

        
        
        


