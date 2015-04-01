from django.contrib.auth.models import User
from django.contrib import auth
import xmlrpclib as xmlrpc 	#Used for authenticating against wordpress using xmlrpc client

from uploadeXe.models import Role
from uploadeXe.models import User_Roles
from django.forms import ModelForm
from organisation.models import Organisation
from organisation.models import UMCloud_Package
from organisation.models import User_Organisations
from users.models import UserProfile
from django import forms


class MyCustomBackend:

    # Create an authentication method
    # This is called by the standard Django login procedure

    def authenticate(self, username=None, password=None):

        try:
            # Try to find a user matching your username
            user = User.objects.get(username=username)
	    
	    #Check username and password here..
	    if password == user.password:
                # Yes? return the Django user object
		print("Username and Password check success")
                return user
            else:
                # No? return None - triggers default login failed
		print("Username and Password check unsuccessfull")
                return None

        except User.DoesNotExist:
            # No user was found, return None - triggers default login failed
	    print("User: " + username + " Does Not Exists")

	    #Check user credentials

	    s = xmlrpc.ServerProxy('http://www.ustadmobile.com/xmlrpc.php')	#Getting the xmlrpc link for ustadmobile.com wordpress
	    try:
	        if s.wpse39662.login(username,password):				#Returns true if user is successfully authenticated, False if not
	    	    print("Username and Password check success for new user.")
		    print("Checking new user in Django..")
		    #Create user.
		    user_count = User.objects.filter(username=username).count()
        	    if user_count == 0:
			print ("User doesn't exist, creating user..")
			user = User(username=username, email=username)
    			user.set_password(password)
			user.is_active=False
    			user.save()
			print("User created!")

			student_role = Role.objects.get(pk=6)
    			new_role_mapping = User_Roles(name="customauth-wordpress", user_userid=user, role_roleid=student_role)
    			new_role_mapping.save()
			print("User role mapping created for new user from custom authentication backend: ustadmobile.com wordpress")
	
    			individual_organisation = Organisation.objects.get(pk=1)
    			new_organisation_mapping = User_Organisations(user_userid=user, organisation_organisationid=individual_organisation)
    			new_organisation_mapping.save()
			print("User organisation mappting created for new user from custom authentication backend: ustadmobile.com wordpress")

			user.is_active = True
			user.save()

        		#return auth_and_login(request)
			return user;
    		    else:
        		#Show message that the username/email address already exists in our database.
			print("Error in creating user. User already exists!")
        		return redirect("/login/")
	        else:
		    print("Username and Password check unsuccessfull for new user. Not creating new user.")
		    return None
	    except:
		print("!!Unable to establish a connection with ustadmobile.com's xmlrpcr!!")
		return None

            #return None

    # Required for your backend to work properly - unchanged in most scenarios
    def get_user(self, user_id):
	print("In get_user")
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
	    print("User does not exist")
            return None

