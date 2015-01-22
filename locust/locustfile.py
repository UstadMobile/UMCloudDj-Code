from locust import HttpLocust, TaskSet

def login(l):
    response = l.client.get("/auth/")
    csrftoken = response.cookies['csrftoken']

    response=l.client.post("/auth/", {"username":"ram.narayan", "password":"varuna"}, headers={"X-CSRFToken": csrftoken})

def index(l):
    l.client.get("/")

def assigned_courses(l):
    #response = l.client.get("/assigned_courses/")
    response = l.client.post("/assigned_courses/", {"username":"ram.narayan", "password":"varuna"})

def getepubfile(l):
    l.client.get("/media/eXeExport/elps/test.epub")

def dump_statement(l):
    statement1=json.dumps({"actor":{"mbox":"mailto:student1@ustadmobile.com","name":"Student One","objectType":"Agent"},"verb":{"id":"http://adlnet.gov/expapi/verbs/launched","display":{"en-US":"launched"}},"object":{"id":"http://www.ustadmobile.com/um-tincan/activities/ThisIsTheUniqueElpID","objectType":"Activity","definition":{"name":{"en-US":"Course Title"},"description":{"en-US":"Example activity definition"}}},"context":{"contextActivities":{"parent":[{"id":"http://www.ustadmobile.com/um-tincan/course/1"}]}}})
    statement2=json.dumps({"actor":{"mbox":"mailto:student1@ustadmobile.com","name":"Student One","objectType":"Agent"},"object":{"definition":{"description":{"en-US":"Motivational"},"name":{"en-US":"Motivational"},"type":"http://adlnet.gov/expapi/activities/module"},"id":"http://www.ustadmobile.com/um-tincan/activities/ThisIsTheUniqueElpID/Motivational","objectType":"Activity"},"result":{"duration":"PT0H0M2S"},"verb":{"display":{"en-US":"experienced"},"id":"http://adlnet.gov/expapi/verbs/experienced"}})


    l.username = "ram.narayan"
    l.email = "student1@ustadmobile.com"
    l.password = "varuna"
    l.auth = "Basic %s" % base64.b64encode("%s:%s" % (self.username, self.password))

    view_url="/umlrs/statements"
    response = l.client.post(view_url, statement1, content_type="application/json",
        Authorization=self.auth, X_Experience_API_Version="1.0.0")

def logout(l):
    l.client.get("/logout")

def usertable(l):
    l.client.get("/userstable/")

class StudentBehavior(TaskSet):
    tasks = {index:1, usertable:2, assigned_courses:2, getepubfile:2, logout:1}

    def on_start(self):
        login(self)

class StudentUser(HttpLocust):
    task_set = StudentBehavior
    min_wait=50
    max_wait=90

class BasicBehaviour(TaskSet):
    tasks = { index:1}
    def on_start(self):
        login(self)

class BasicUser(HttpLocust):
    task_set = BasicBehaviour

def access_report_page(l):
    l.client.get("/reports/")

def allstatements(l):
    l.client.get("/reports/pagi_allstatements/")
    l.client.get("/reports/pagi_allstatements/?page=2")

def usage_report(l):
    pass

class TeacherBehaviour(TaskSet):
    tasks = { index:1, usertable:2, access_report_page:2, allstatements:4, usage_report:2 }
    def on_start(self):
        login(self):

class TeacherUser(HttpLocust):
    task_set = TeacherBehaviour
