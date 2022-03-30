import requests
import json

with open("intents.json", "r", encoding="utf8") as f:
    intents = json.load(f)
    resp = requests.post('http://localhost:5000/login', json={ "email":"pancho.fernandez@ryerson.ca",  "password": "FYEO1234"})
    for intent in intents["intents"]:
        resp = requests.post('http://localhost:5000/faq', json=intent)
        print(resp)







#    {
#       "tag": "greeting",
#       "patterns": ["Hi", "How are you", "Is anyone there?", "Hello", "Good day", "Hey"],
#       "responses": ["Hello, how can I help you today?", "Hi there, how can I help?"]
#     },
#     {
#       "tag": "goodbye",
#       "patterns": ["Bye", "Thank you", "Thanks for the help", "Alright"],
#       "responses": ["Bye!, thanks for visiting", "Take care!"]
#     },
#  {
#       "tag": "Plan Change Decision 2",
#       "patterns": [
#         "When will I hear back?",
#         "How will I know if it is approved?",
#         "I still haven't heard anything about a decision",
#         "When will I know the decision?"
#       ],
#       "responses": [
#         "All Plan Change decisions will be emailed out after final grades have been released and reviewed. Students are required to enroll in the appropriate courses themselves.\n"
#       ],
#       "context_set": "plan-change"
#     },
#  {
#       "tag": "Transition Courses 2",
#       "patterns": [
#         "Are these courses offered in both the spring and summer?",
#         "Can i take these courses in the Spring and Summer?",
#         "Can i take these courses in the summer?"
#       ],
#       "responses": [
#         "No, Ryerson does not offer engineering transition courses both in Spring and in Summer. First-year Engineering Transition Courses are generally offered in the Spring\n"
#       ],
#       "context_filter": "transition"
#     },

#  {
#       "tag": "Plan Change Denial 2",
#       "patterns": ["What if it is denied?", "What do i do if it is denied", "What do i do if it isn't approved?"],
#       "responses": [
#         "Students can re-submit a Plan Change for the following semester to be re-considered.\nStudents may also want to meet with the First-Year Academic Services and Success Facilitator\n"
#       ],
#       "context_filter": "plan-change"
#     },

#  {
#       "tag": "Liberals When 2",
#       "patterns": ["Can I take them in the spring/summer?", "When can I take them?", "When should I take them"],
#       "responses": [
#         "When do you recommend taking your liberal studies?\nThis varies for every student. Some students decide to take it in the Fall along with the required 5 (or less courses) and some decide to do them in the spring or in upper years. **We don’t encourage a full course load (of 6 courses) especially with online learning.**\nAll Engineering students are required to complete four Liberal Studies Courses as per their graduation requirements. You do not have to take your Liberal courses in your first year of study; liberal courses just have to be completed before you apply to graduate. Many students use the Spring/Summer term to complete their liberals or complete them in their later years so they can concentrate more on their Engineering courses, especially in their first year. In total, students must take TWO (2) Table A - Lower Level Liberals, ONE (1) Table B - Upper Level Liberal, and ONE (1) Engineering Upper Level Liberal. \n\nPlease note that first-year engineering midterms are often held on Fridays from 6 p.m. - 8 p.m., so you should ensure that you do not enroll in a Liberal studies course that conflicts with this time.\n"
#       ],
#       "context_filter": "liberals"
#     },


#  {
#       "tag": "FYEO Office Hours 2",
#       "patterns": ["What time is it open?", "What time can I go to visit?", "Is it open today?"],
#       "responses": [
#         "The FYEO operates from Monday to Friday, 9am to 5pm, unless otherwise posted. The FYEO Drop-in Zoom Virtual Advisement Room, is Open weekdays Monday - Friday from 10am - 12pm EST.  Students can always email the FYEO at firstyeareng@ryerson.ca.\n"
#       ],
#       "context_filter": "fyeo-office"
#     },