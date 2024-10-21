import os
import google.generativeai as genai
from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS, cross_origin
from mysql.connector import pooling

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

genai.configure(api_key="AIzaSyATvgsCmTJ_6_lPiWh1slcacEt6bA1ZlTU")

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

db_config = {
    "host": "193.203.184.66",
    "user": "u484908010_TestDB",
    "password": "TestDB@123",
    "database": "u484908010_TestDB"
}

connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    **db_config
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

chat_session = model.start_chat(
    history=[]
)

def queryGenerator(input_text):
    schema_description = (
        "The Faculty Management System has the following tables with their respective keys: 1. departments: DepartmentID INT (Primary Key), DepartmentName VARCHAR(255); 2. faculties: FacultyID INT (Primary Key), FacultyName VARCHAR(255), DepartmentID INT (Foreign Key referencing departments(DepartmentID)); 3. courses: CourseID INT (Primary Key), CourseName VARCHAR(255), FacultyID INT (Foreign Key referencing faculties(FacultyID)); 4. students: StudentID INT (Primary Key), StudentName VARCHAR(255), DepartmentID INT (Foreign Key referencing departments(DepartmentID)), CourseID INT (Foreign Key referencing courses(CourseID)); 5. exams: ExamID INT (Primary Key), ExamName VARCHAR(255), CourseID INT (Foreign Key referencing courses(CourseID)), ExamDate DATE; 6. assignments: AssignmentID INT (Primary Key), AssignmentTitle VARCHAR(255), CourseID INT (Foreign Key referencing courses(CourseID)), DueDate DATE; 7. attendance: AttendanceID INT (Primary Key), StudentID INT (Foreign Key referencing students(StudentID)), CourseID INT (Foreign Key referencing courses(CourseID)), AttendanceDate DATE, Status ENUM('Present', 'Absent'); 8. grades: GradeID INT (Primary Key), StudentID INT (Foreign Key referencing students(StudentID)), ExamID INT (Foreign Key referencing exams(ExamID)), AssignmentID INT (Foreign Key referencing assignments(AssignmentID)), Grade VARCHAR(5);"
    )
    input_text = " input text : " + input_text
    last_part = " create query from input text that can be executed on Faculty Management System schema do not give any kind of explanation or any other text just give query"
    full_input = schema_description + " " + input_text + last_part

    response = chat_session.send_message(full_input)
    return response.text

@app.route('/', methods=['POST'])
def text_to_query():
    input_text = request.json.get("query")
    query = queryGenerator(input_text)

    query = query[6:-3]
    print(query)

    try:
        db = connection_pool.get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        results = []
        for row in rows:
            results.append(dict(zip(column_names, row)))

        cursor.close()
        db.close()
        return jsonify(results)

    except mysql.connector.Error as err:
        print("-------------------------Error MSG----------------------")
        print(err.msg)
        return jsonify({"error": str(err.msg)}), 500

if __name__ == '__main__':
    app.run(debug=True)