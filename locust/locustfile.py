from locust import HttpLocust, TaskSet

def login(l):
    response = l.client.get("/auth/")
    csrftoken = response.cookies['csrftoken']

    response=l.client.post("/auth/", {"username":"ram.narayan", "password":"varuna"}, headers={"X-CSRFToken": csrftoken})

def index(l):
    l.client.get("/")

def usertable(l):
    l.client.get("/userstable/")

class UserBehavior(TaskSet):
    tasks = {index:1, usertable:2}

    def on_start(self):
        login(self)

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait=5000
    max_wait=9000
