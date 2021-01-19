from flask import Flask,render_template,request,redirect,flash,session
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re
import datetime


EMAIL_REGEX=re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app=Flask(__name__)
bcrypt=Bcrypt(app)
app.secret_key='thisissecret'

@app.route('/')
def start():
    return render_template('login.html')

@app.route('/createaccount', methods=["POST"])
def creation():
    if len(request.form['firstname'])<1:
        flash("First name cannot be empty","flashfirstname")
    elif request.form['firstname'].isalpha() == False:
        flash("Invalid, number input not valid in first name","flashfirstname")
    if len(request.form['lastname'])<1:
        flash("Last name cannot be empty", "flashlastname")
    elif request.form['lastname'].isalpha() == False:
        flash("Invalid, number input not valid in last name","flashlastname")
    mysql=connectToMySQL("simplewall")
    query= "Select * from users where username = %(username)s;"
    data={ "username": request.form["username"]}
    checkingforduplicateusers=mysql.query_db(query,data)
    if len(checkingforduplicateusers) != 0:
            flash("User name already exists","flashusername")
    elif len(request.form['username'])<1:
        flash("Username cannot be empty","flashusername")
    if len(request.form['password'])<8:
        flash("Password must be at least 8 characters long","flashpassword")
    elif len(request.form['password'])>15:
        flash("Password must be less than 15 characters long","flashpassword")
    elif request.form['password'] != request.form['confirmpassword']:
        flash("Password and Password Confirmation do not match","flashpassword")
    else:
        hashedpass=bcrypt.generate_password_hash(request.form['password'])
    mysql=connectToMySQL("simplewall")
    query= "Select * from users where email = %(email)s;"
    data={ "email": request.form["email"]}
    checkingforduplicateemails=mysql.query_db(query,data)
    if len(checkingforduplicateemails) != 0:
        flash("Email name already exists","flashemail")
    elif len(request.form['email']) <1:
        flash("Email cannot be left empty","flashemail")
    elif not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email, must follow name@domain.com","flashemail")
    if len(request.form['telephone'])<10:
        flash("Invalid Phone Number", "flashtelephone")
    if request.form['telephone'].isdigit()== False:
        flash("Invalid, must be all numbers", "flashtelephone")
    if len(request.form['address']) <1:
        flash("Address must be provided", "flashaddress")
    if '_flashes' in session.keys():
        return redirect('/')
    else:
        mysql=connectToMySQL("simplewall")
        query="insert into users (first_name,last_name,username,email,password,telephone,address,created_at) values (%(firstname)s,%(lastname)s,%(username)s,%(email)s,%(password_hash)s,%(telephone)s,%(address)s,NOW());"
        data={
            "firstname":request.form["firstname"],
            "lastname":request.form["lastname"],
            "username":request.form["username"],
            "email":request.form["email"],
            "password_hash":hashedpass,
            "telephone":request.form["telephone"],
            "address":request.form["address"]
        }
        mysql.query_db(query,data)
        return redirect('/simplewall')

@app.route('/login', methods=["POST"])
def log():
    if len(request.form['loginusername'])<1:
        flash("Invalid User name","flashloginusername")
    mysql=connectToMySQL("simplewall")
    query= "Select * from users where username = %(username)s;"
    data={ "username": request.form["loginusername"]}
    answers=mysql.query_db(query,data)
    if len(answers)==0:
        flash("User name does not exist","flashloginusername")
    if answers:
        if bcrypt.check_password_hash(answers[0]["password"],request.form["loginpassword"]):
            session['usernameid']=answers[0]['id']
        else:
            flash("Incorrect password","flashloginpassword")
    if '_flashes' in session.keys():
        return redirect('/')
    else:
        return redirect('/simplewall')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/simplewall')
def thewall():

    mysql=connectToMySQL("simplewall")
    query="select concat(users.first_name,' ',users.last_name) as full_name,users.id,users.first_name,users.username,users.email,users.telephone from users where users.id <> %(myid)s;"
    data={
        'myid':session['usernameid']
    }
    recipientkeylist = mysql.query_db(query,data)

    # this is how i was able to display data for the senders
    mysql=connectToMySQL("simplewall")
    query="select concat(users.first_name,' ',users.last_name) as full_name,users.id,users.first_name,users.username,users.email,users.telephone from users where users.id = %(myid)s;"
    data={
        'myid':session['usernameid']
    }
    displaydataforuser=mysql.query_db(query,data)

    # this is where i am able to grab information for displaying messages
    mysql=connectToMySQL("simplewall")
    query="select users.id, concat(users.first_name,' ',users.last_name)as full_name, users.username,users.telephone,users.email,messages.message, messages.id, messages.created_at, messages.user_sender_id, messages.user_receiver_id from users inner join messages on users.id = messages.user_sender_id where messages.user_receiver_id= %(myid)s order by messages.created_at desc;"
    data={
        'myid':session['usernameid']
    }
    showingmessages=mysql.query_db(query,data)
    print(showingmessages)
# inputing time since 
    for i in range(len(showingmessages)):
        session['time']=(showingmessages[i]['created_at'])
        print(session['time'])
    print(session['time'])
    return render_template('simplewall.html', usersidlist=recipientkeylist,infoforuser=displaydataforuser,messages=showingmessages)

@app.route('/simplewallmessages',methods=["POST"])
def writtenonthewall():
    mysql=connectToMySQL("simplewall")
    query="insert into messages (message,created_at,user_sender_id,user_receiver_id) values (%(message)s,NOW(),%(sender)s,%(receiver)s);"
    data={
        "message": request.form["textarea"],
        "sender": session['usernameid'],
        "receiver": request.form['receiver_id']
    }
    mysql.query_db(query,data)
    return redirect('/simplewall')

@app.route('/delete', methods=['POST'])
def byeforever():
    mysql=connectToMySQL("simplewall")
    query="delete from messages where messages.id= %(delete)s;"
    data={
        'delete':request.form["deletion"]
    }
    mysql.query_db(query,data)
    return redirect('/simplewall')
    
@app.route('/', methods=["GET"])
def get_my_ip():
    print('\n\n\n\n',request.remote_addr,'\n\n\n\n')
    return redirect('/simplewall')

if __name__=="__main__":
    app.run(debug=True)