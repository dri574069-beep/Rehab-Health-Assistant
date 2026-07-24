from flask import Flask,request,redirect,render_template,session,flash,jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import sqlite3
import smtplib
from email.message import EmailMessage
import json
import os
app=Flask(__name__)
app.secret_key="Sara_Craige881"

scheduler=BackgroundScheduler()
med=[]
history=[]
@app.route("/")
def initTable():
    db=sqlite3.connect("patientHealth.db")
    cursor=db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS patientInfo(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT ,
                   gender TEXT ,
                   age INTEGER) """)
    db.commit()
    cursor.execute("""CREATE TABLE IF NOT EXISTS reminder(
                    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    user_chat TEXT,
                    water_history TEXT,
                    water_status TEXT,
                    recog INTEGER,
                    FOREIGN KEY(patient_id) REFERENCES patientinfo(id))""")
    db.commit()
    cursor.close()
    db.close()
    return redirect("/register")
@app.route("/sendKey")
def sendKey():
    KEY=os.environ.get("API_KEY")
    return jsonify({"api_key":KEY})
@app.route("/register",methods=["GET","POST"])
def register():
    db=sqlite3.connect("patientHealth.db")
    db.execute("PRAGMA foreign_keys = ON")
    cursor=db.cursor()
    if request.method=="POST":
        name=request.form.get("user_name")
        gender=request.form.get("gender")
        age=int(request.form.get("age"))
        cursor.execute("SELECT id from patientinfo WHERE name=?",(name,))
        existing_id=cursor.fetchone()
        if existing_id:
            patient_id=existing_id[0]
            print(patient_id)
            session["patient_id"]=patient_id
        else:
            cursor.execute("INSERT  INTO patientinfo (name,gender,age) VALUES (?,?,?)",(name,gender,age))
            patient_id=cursor.lastrowid
        session["patient_id"]=patient_id
        db.commit()
        session["name"]=name
        session["gender"]=gender
        session["age"]=age
        cursor.close()
        db.close()
        flash(f"Welcome {name}, click on this link to use the website")
        return render_template("index.html",name=name,age=age,gender=gender)
    return render_template("index.html")
@app.route("/assis.html")
def assis():
    return render_template("/assis.html")
@app.route("/fetchData")
def fetchData():
    if "name" not in session:
        return jsonify({"status":'not registered'})
    db=sqlite3.connect("patientHealth.db")
    db.execute("PRAGMA foreign_keys = ON")
    cursor=db.cursor()

    cursor.execute("SELECT name,age,gender FROM  patientinfo  WHERE  id=?",(session["patient_id"],))
    information=cursor.fetchone()
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"name":information[0],
                    "age":information[1],
                    "gender":information[2]})
@app.route("/pageTwo.html")
def pageTwo():
    return render_template("pageTwo.html")
@app.route("/medInfo.html")
def medinfo():
    return render_template("medInfo.html")
@app.route("/waterintake.html")
def waterReminder():
    return render_template("waterintake.html")
@app.route("/medReminder.html")
def medReminder():
    return render_template("medReminder.html")
def getMedicine(medicine,email):
    EMAIL=os.environ.get("EMAIL")
    PASSWORD=os.environ.get("EMAIL_PASSWORD")
    newMed=f"Hey its time for your medicine {medicine}"
    med.append(newMed)
    msg=EmailMessage()
    
    msg["Subject"]="Medicine Reminder"
    msg["To"]=email
    msg["From"]=EMAIL
    msg.set_content(f"hey Its time To take your medicine: {medicine}")
    with smtplib.SMTP_SSL("smtp.gmail.com",465)as smtp:
        smtp.login(EMAIL,PASSWORD)
        smtp.send_message(msg)
@app.route("/sendMed")
def sendMed():
    return jsonify({"medicine":med})
@app.route("/schedule",methods=["POST"])
def schedule():
    data=request.get_json()
    medicine=data.get("medicine")
    time=data.get("time")
    date=data.get("date")
    email=data.get("email")
    combined_time=f"{date} {time}"
    try:
        date_time=datetime.strptime(combined_time,"%Y-%m-%d %H:%M")
        scheduler.add_job(
            getMedicine,
            trigger="date",
            run_date=date_time,
            args=[medicine,email]
        )
        return jsonify({"status":"success","message":"message scheduled successfuly"})
    except Exception as e:
        return jsonify({"status":"error","message":f"{e}"})
scheduler.start()
@app.route("/send_mail",methods=["POST"])
def send_mail():
    EMAIL=os.environ.get("EMAIL")
    PASSWORD=os.environ.get("EMAIL_PASSWORD")
    cred=request.get_json()
    email=cred.get("email")
    times=cred.get('times')
    try:
        mes=EmailMessage()
        mes["Subject"]="Drinking Water Reminder!!"
        mes["To"]=email
        mes["From"]=EMAIL
        mes.set_content(f"Hello its time to drink water the {times} time")
        with smtplib.SMTP_SSL("smtp.gmail.com",465)as smtp:
            smtp.login(EMAIL,PASSWORD)
            smtp.send_message(mes)
        return jsonify({"status":"successfull","message":"Successfully send email"})
    except Exception as e:
        return jsonify({"status":"error","message":f"{e}"})
@app.route("/save_data",methods=["POST"])
def save_data():
    try:
        data=request.get_json()
        user_chat=json.dumps(data.get("chat"))
        session["user_chat"]=data.get("chat")
        db=sqlite3.connect("patientHealth.db")
        db.execute("PRAGMA foreign_keys = ON")
        cursor=db.cursor()
        cursor.execute("SELECT MAX(schedule_id) FROM reminder WHERE patient_id=?",(session["patient_id"],))
        result=cursor.fetchone()
        if result[0] is None:
            schedule_id=1
        else:
            schedule_id=result[0]+1
        session["schedule_id"]=schedule_id
        cursor.execute("INSERT INTO reminder (patient_id,user_chat,recog) VALUES (?,?,?)",(session["patient_id"],user_chat,session["recogId"]))
        db.commit()
        cursor.execute("SELECT * FROM reminder")
        Data=cursor.fetchall()
        # user_chat=json.loads(user_chat)
        return jsonify({"status":"success","message":"successfully saved data"})
    except Exception as e:
        return jsonify({"chat":f"{e}"})
    finally:
        cursor.close()
        db.close()
@app.route("/get_data")
def get_data():
    db=sqlite3.connect("patientHealth.db")
    db.execute("PRAGMA foreign_keys = ON")
    cursor=db.cursor()

    cursor.execute("SELECT user_chat FROM reminder WHERE schedule_id=?",(session["schedule_id"],))
    chat=cursor.fetchone()
    db.commit()
    cursor.close()
    db.close()
    if chat is None or chat[0] is None:
        return jsonify({"chat":[]})
    return jsonify({
        "chat":json.loads(chat[0])
    })
@app.route("/sendTime",methods=["POST"])
def sendTime():
    db=sqlite3.connect("patientHealth.db")
    db.execute("PRAGMA foreign_keys = ON")
    cursor=db.cursor()
    cursor.execute("SELECT MAX(recog) FROM reminder WHERE patient_id=?",(session["patient_id"],))
    Id=cursor.fetchone()
    if Id is None or Id[0] is None:
            recogId=1
            session["recogId"]=recogId
    else:
            recogId=Id[0]+1
            session["recogId"]=recogId
    try:
        data=request.get_json()
        tim=data.get("time")
        times=int(tim)
        time=1
        while (time <= times):
            cursor.execute("UPDATE reminder SET water_history=? WHERE patient_id=? AND recog=?",(times,session["patient_id"],session["recogId"]))
            db.commit()
            time+=1
        return jsonify({"times":time})
    except Exception as e:
        return jsonify({"times":f"{e}"})
    finally:
        cursor.close()
        db.close()
@app.route("/fetchTime")
def fetchTime():
    db=sqlite3.connect("patientHealth.db")
    db.execute("PRAGMA foreign_keys = ON")
    cursor=db.cursor()
    try:
        cursor.execute("SELECT water_history FROM reminder WHERE patient_id=? AND recog=?",(session["patient_id"],session["recogId"]))
        row=cursor.fetchone()
        db.commit()
        return jsonify({"water_his":f"{row[0]}"})
    except Exception as e:
        return jsonify({"water-his":e})
    finally:
        cursor.close()
        db.close()
@app.route("/changeState",methods=["POST"])
def changeState():
    db=sqlite3.connect("patientHealth.db")
    db.execute("PRAGMA foreign_keys = ON")
    cursor=db.cursor()

    try:
        data=request.get_json()
        status=data.get("status")
        cursor.execute("INSERT INTO reminder (water_status,patient_id,recog) VALUES (?,?,?)",(status,session["patient_id"],session["recogId"]))
        db.commit()
        return jsonify({"status":f"{status}"})
    except Exception as e:
        return jsonify({"status":f"{e}"})
    finally:
         cursor.close()
         db.close()
@app.route("/manipulatedStatus")
def manipulatedStatus():
    db=sqlite3.connect("patientHealth.db")
    db.execute("PRAGMA foreign_keys = ON")
    cursor=db.cursor()

    try:
        cursor.execute(
        "SELECT schedule_id, patient_id, water_history, water_status FROM reminder"
            )
        sus=cursor.fetchall()
        cursor.execute("SELECT water_status FROM reminder WHERE  patient_id=? AND recog=? AND water_status IS NOT NULL",(session["patient_id"],session["recogId"],))
        manStatus=cursor.fetchall()
        cursor.execute("SELECT water_history FROM  reminder WHERE patient_id=?",(session["patient_id"],))
        water=cursor.fetchone()
        water_time=water[0]
        water_times=int(water_time)
        i=1
        history.clear()
        while (i <= water_times):
             history.append(i)
             i+=1
        return jsonify({"Status":manStatus,"Time":history})
    except Exception as e:
        return jsonify({"Status":f"{e}","Time":f"{e}"})
    finally:
        cursor.close()
        db.close()
if __name__=="__main__":
    initTable()
    app.run(debug=True)

