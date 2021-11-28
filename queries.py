import pyodbc
import bcrypt

from tools import *

key = b'$2b$12$COnvlB9Kses3CthyxNl9pu'


class Query:
    def __init__(self):
        self.connection_to_db = pyodbc.connect(
            r'Driver={SQL Server};Server=LAPTOP-GT7SSRCR;Database=Matus;Trusted_Connection=yes;')
        self.cursor = self.connection_to_db.cursor()

    def __del__(self):
        self.connection_to_db.close()

    def getTeachersNames(self):
        self.cursor.execute('Select Name from Teachers')
        teachersName = self.cursor.fetchall()
        return teachersName

    def getStudentsNames(self):
        self.cursor.execute('Select idStudent, Name from Students ORDER BY Name')
        return self.cursor.fetchall()

    def getStudentsNamesByClass(self, numClass):
        self.cursor.execute(f"Select idStudent, Name from Students Where NumClass = '{numClass}' ORDER BY Name")

        return self.cursor.fetchall()


    def changeInfoOfUser(self, idLocal, newName, dateOfBirth, phoneNumber, mail, activity=1):
        self.cursor.execute(
            f"Update Teachers Set Name = '{newName}', DateOfBirth = '{dateOfBirth}', PhoneNumber ='{phoneNumber}',Mail = '{mail}', Activity = '{activity}' Where idTeacher = '{idLocal}'")
        self.connection_to_db.commit()


    def getUserLoginByID(self, idUser):
        self.cursor.execute(f"SELECT login from Users where idUser ='{idUser}'")
        return self.cursor.fetchone().login

    def getUserIdByLogin(self, login):
        self.cursor.execute(f"SELECT idUser from Users where login ='{login}'")
        return self.cursor.fetchone().idUser

    def getUserInfo(self, idUser):
        self.cursor.execute(f"SELECT idTeacher from Teachers where idUser ='{idUser}'")
        ifTeacher = self.cursor.fetchone()
        if ifTeacher:
            self.cursor.execute(
                f"Select idTeacher, Name, DateOfBirth, Experience, PhoneNumber, mail, Activity from Teachers where idTeacher = '{ifTeacher.idTeacher}'")
            teacherInfo = self.cursor.fetchone()
            return Teacher(idUser, status[1], teacherInfo.idTeacher, teacherInfo.Name, teacherInfo.DateOfBirth,
                           teacherInfo.Experience, teacherInfo.PhoneNumber, teacherInfo.mail, teacherInfo.Activity)
        else:
            self.cursor.execute(
                f"Select  idStudent, Name, DateOfBirth, ParentPhoneNumber, mail, NumClass, Activity from Students JOIN Users on Users.idUser = Students.idUser where Users.idUser = '{idUser}'")
            studentInfo = self.cursor.fetchone()
            if studentInfo:
                return Student(idUser, status[2], studentInfo.idStudent, studentInfo.Name, studentInfo.DateOfBirth,
                               studentInfo.ParentPhoneNumber, studentInfo.mail, studentInfo.NumClass,
                               studentInfo.Activity)
            else:
                return User(idUser, status[0])

    def getLogin(self, login):
        self.cursor.execute(f"SELECT login from Users where login ='{login}'")
        return self.cursor.fetchone()

    def getPassword(self, login, password):
        self.cursor.execute(f"SELECT password from Users where login ='{login}'")
        ifPass = str.encode(self.cursor.fetchone().password)
        password = bcrypt.hashpw(str.encode(password), key)
        if ifPass == password:
            return True
        return None

    def changePassword(self, idUser, password):
        password = bcrypt.hashpw(str.encode(password), key)
        self.cursor.execute(f"UPDATE Users Set password = '{password.decode()}' where idUser ='{idUser}'")
        self.connection_to_db.commit()


    # Вывод предметов, закрепленных за учителем
    def getTeacherSubjects(self, idTeacher):
        self.cursor.execute(f"Select nameOfSubject from Subjects " 
                            f"JOIN TeacherSubjects ON TeacherSubjects.idSubject=Subjects.idSubject "
                            f"JOIN Teachers ON TeacherSubjects.idTeacher=Teachers.idTeacher "
                            f"WHERE Teachers.idTeacher ='{idTeacher}'")
        subjects = []
        while True:
            sub = self.cursor.fetchone()
            if sub == None:
                break
            subjects.append(sub.nameOfSubject)

        return subjects

    def getTimeTableForTeacher(self, idTeacher):
        self.cursor.execute(f"EXEC sp_set_session_context 'idTeacher', {idTeacher}")
        self.cursor.execute(f'Select * FROM TEACHER_TIMETABLE ORDER BY dayOfWeek ASC, time ASC')
        return self.cursor.fetchall()


    def getClasses(self):
        self.cursor.execute(f"Select numClass FROM Classes")
        classes = []
        while True:
            cl = self.cursor.fetchone()
            if cl == None:
                break
            classes.append(cl.numClass)
        return classes

    def getProgressForClass(self, numClass):
        self.cursor.execute(f"""Select Subjects.NameOfSubject, Students.Name, Grade from Grades 
	                                JOIN Students ON Students.idStudent = Grades.idStudent
	                                JOIN TeacherSubjects ON TeacherSubjects.idTeacherSubject = Grades.idTeacherSubject
	                                JOIN Subjects ON TeacherSubjects.idSubject = Subjects.idSubject
                                        WHERE Students.NumClass = '{numClass}'
                                            ORDER BY NameOfSubject, Name""")
        grades = []
        while True:
            gr = self.cursor.fetchone()
            if gr == None:
                break
            grades.append(gr)
        return grades


    def getProgressOfStudent(self, idStudent):
        self.cursor.execute(f"""Select Subjects.NameOfSubject, Grade from Grades
                                    JOIN Students ON Students.idStudent = Grades.idStudent
                                    JOIN TeacherSubjects ON TeacherSubjects.idTeacherSubject = Grades.idTeacherSubject
                                    JOIN Subjects ON TeacherSubjects.idSubject = Subjects.idSubject
                                        WHERE Students.idStudent = {idStudent}
                                            ORDER BY NameOfSubject""")
        grades = []
        while True:
            gr = self.cursor.fetchone()
            if gr == None:
                break
            grades.append(gr)
        return grades


    def put_grade(self, nameStudent, numClass, nameSubject, grade, dateOfGrade):
        self.cursor.execute(f"""INSERT INTO Grades(idStudent, idTeacherSubject, Grade, DateOfGrade)
                                VALUES((Select idStudent from Students where Name='{nameStudent}'),
                                        (Select DISTINCT TeacherSubjects.idTeacherSubject from TeacherSubjects 
                                            JOIN Subjects ON Subjects.idSubject = TeacherSubjects.idSubject
                                            JOIN Timetable ON Timetable.idTeacherSubject = TeacherSubjects.idTeacherSubject
                                            WHERE Subjects.NameOfSubject='{nameSubject}' and Timetable.numClass = (Select numClass from Students where name ='{nameStudent}' and numClass ='{numClass}')),
                                            {grade}, '{dateOfGrade}')""")
        self.connection_to_db.commit()

    def getTimeTableForClass(self, numClass):
        self.cursor.execute(f"EXEC sp_set_session_context 'numClass', '{numClass}'")
        self.cursor.execute(f'Select * FROM CLASS_TIMETABLE order by dayOfWeek ASC, time ASC')
        return self.cursor.fetchall()