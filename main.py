import customtkinter as ctk
import sqlite3
import hashlib
import json
from datetime import datetime
from tkinter import messagebox
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB_NAME = "isbat_gradehub.db"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS performance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        average REAL NOT NULL,
        percentage REAL NOT NULL,
        results_json TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ================= PDF =================
def generate_pdf(name, results, stats):
    file_name = f"{name.replace(' ', '_')}_ScoreSheet.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 18)
    c.drawString(150, y, "ISBAT GRADEHUB SCORE SHEET")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Student: {name}")
    y -= 25
    c.drawString(50, y, f"Average: {stats['average']}")
    y -= 25
    c.drawString(50, y, f"Grade: {stats['grade']}")
    y -= 25
    c.drawString(50, y, f"Percentage: {stats['percentage']}%")
    y -= 40

    for sub, mark in results.items():
        c.drawString(50, y, f"{sub}: {mark}")
        y -= 20

    y -= 20
    c.drawString(50, y, f"Comment: {stats['comment']}")

    c.save()
    messagebox.showinfo("Success", f"Score sheet saved as {file_name}")

# ================= GRADE LOGIC =================
def get_grade(avg):
    if avg >= 90:
        return "A+ LEGEND"
    elif avg >= 80:
        return "A EXCELLENT"
    elif avg >= 70:
        return "B+ STRONG"
    elif avg >= 60:
        return "B SOLID"
    elif avg >= 50:
        return "C AVERAGE"
    elif avg >= 40:
        return "D NEEDS WORK"
    else:
        return "F KEEP PUSHING"

def get_comment(avg):
    if avg >= 80:
        return "Outstanding performance!"
    elif avg >= 60:
        return "Very good performance."
    elif avg >= 50:
        return "Satisfactory performance."
    else:
        return "Needs improvement."

# ================= MAIN APP =================
class GradeHubApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("ISBAT GradeHub")
        self.geometry("700x600")
        self.current_user = None
        init_db()
        self.show_login()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ================= LOGIN =================
    def show_login(self):
        self.clear()

        ctk.CTkLabel(self, text="ISBAT GradeHub", font=("Arial", 28)).pack(pady=20)

        self.username = ctk.CTkEntry(self, placeholder_text="Username")
        self.username.pack(pady=10)

        self.password = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password.pack(pady=10)

        ctk.CTkButton(self, text="Login", command=self.login).pack(pady=10)
        ctk.CTkButton(self, text="Sign Up", command=self.signup).pack()

    def login(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, password_hash, full_name FROM users WHERE username=?",
                  (self.username.get(),))
        row = c.fetchone()
        conn.close()

        if row and hash_password(self.password.get()) == row[1]:
            self.current_user = row
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid login!")

    def signup(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
                      (self.username.get(),
                       hash_password(self.password.get()),
                       self.username.get().upper()))
            conn.commit()
            messagebox.showinfo("Success", "Account created!")
        except:
            messagebox.showerror("Error", "Username already exists!")
        conn.close()

    # ================= DASHBOARD =================
    def show_dashboard(self):
        self.clear()

        user_id, _, full_name = self.current_user

        ctk.CTkLabel(self, text=f"Welcome {full_name}", font=("Arial", 22)).pack(pady=20)

        ctk.CTkButton(self, text="New Analysis", command=self.new_analysis).pack(pady=10)
        ctk.CTkButton(self, text="View History", command=self.view_history).pack(pady=10)
        ctk.CTkButton(self, text="Logout", command=self.show_login).pack(pady=10)

    # ================= NEW ANALYSIS =================
    def new_analysis(self):
        self.clear()

        ctk.CTkLabel(self, text="Enter Subjects and Marks (comma separated e.g Math:80,English:70)",
                     wraplength=500).pack(pady=20)

        self.marks_entry = ctk.CTkEntry(self, width=500)
        self.marks_entry.pack(pady=10)

        ctk.CTkButton(self, text="Analyze", command=self.calculate).pack(pady=10)
        ctk.CTkButton(self, text="Back", command=self.show_dashboard).pack()

    def calculate(self):
        try:
            raw = self.marks_entry.get()
            pairs = raw.split(",")
            results = {}

            for pair in pairs:
                sub, mark = pair.split(":")
                results[sub.strip()] = float(mark.strip())

            avg = round(sum(results.values()) / len(results), 1)
            percentage = avg
            grade = get_grade(avg)
            comment = get_comment(avg)

            stats = {
                "average": avg,
                "percentage": percentage,
                "grade": grade,
                "comment": comment
            }

            # Save to DB
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("""INSERT INTO performance_records
                         (user_id, timestamp, average, percentage, results_json)
                         VALUES (?, ?, ?, ?, ?)""",
                      (self.current_user[0],
                       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       avg, percentage, json.dumps(results)))
            conn.commit()
            conn.close()

            messagebox.showinfo("Result",
                                f"Average: {avg}\nGrade: {grade}\nComment: {comment}")

            generate_pdf(self.current_user[2], results, stats)

            # Chart
            plt.bar(results.keys(), results.values())
            plt.axhline(avg, linestyle='--')
            plt.title("Performance Chart")
            plt.show()

        except:
            messagebox.showerror("Error", "Invalid format!")

    # ================= HISTORY =================
    def view_history(self):
        self.clear()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT timestamp, average, percentage FROM performance_records WHERE user_id=?",
                  (self.current_user[0],))
        rows = c.fetchall()
        conn.close()

        ctk.CTkLabel(self, text="History", font=("Arial", 22)).pack(pady=20)

        for row in rows:
            ctk.CTkLabel(self,
                         text=f"{row[0]} | Avg: {row[1]} | {row[2]}%").pack()

        ctk.CTkButton(self, text="Back", command=self.show_dashboard).pack(pady=20)


if __name__ == "__main__":
    app = GradeHubApp()
    app.mainloop()