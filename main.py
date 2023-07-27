import sqlite3
import logging
import openai
import os
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkinter import Scrollbar
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.ERROR)

# Initialize Tkinter root window
root = Tk()

# Create a context menu
menu = Menu(root, tearoff=0)
menu.add_command(label="Copy", command=lambda: root.focus_get().event_generate('<<Copy>>'))
menu.add_command(label="Paste", command=lambda: root.focus_get().event_generate('<<Paste>>'))

def show_menu(e):
    menu.post(e.x_root, e.y_root)

root.bind("<Button-3>", show_menu)

# Create a Scrollbar
scrollbar = Scrollbar(root)
scrollbar.pack(side=RIGHT, fill=Y)

# Define SoapNote class
class SoapNote:
    def __init__(self):
        self.note = None

    def set_note(self, detail):
        self.note = detail

    def display(self):
        return self.note

# OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

# Generate detailed text using OpenAI API
def generate_detailed_text(session_type, details):
    if session_type == 'Indirect':
        system_message = """
        You are a professional BCBA (Board Certified Behavior Analyst) writing a note for an indirect ABA therapeutic activity for the client. You are to:

        1. Start with an introductory sentence mentioning the context and purpose of the note.
        2. Provide a concise summary of the main observations or activities during the session, which may include report writing, treatment planning, etc.
        3. Include relevant details and specific examples to support the observations or activities.
        4. If applicable, mention any recommendations, changes to the treatment plan, or areas of focus for future sessions.
        5. Conclude the note by summarizing the overall progress or outcomes of the session.
        
        Use clear and concise language, professional terminology when appropriate. Maintain a tone of professionalism and objectivity throughout the note, and write in third person.
        """
    else:
        system_message = """
        You are a professional BCBA (Board Certified Behavior Analyst) writing a note for a direct ABA therapy session for the client. You are to:

        1. Write in the third person using the details provided.
        2. Provide a concise summary of the main observations or activities during the session while expanding on the note.
        4. If applicable, mention any recommendations, changes to the treatment plan, or areas of focus for future sessions.        
        Use clear and concise language, professional terminology when appropriate. Maintain a tone of professionalism and objectivity throughout the note.
        """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Details: {details}"}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

def new_note():
    #Create new note option
    details_text.delete(1.0, "end-1c")
    result_text.delete(1.0, "end-1c")

def generate_note():
    # Collect user inputs here
    try:
        details = details_text.get(1.0, "end-1c")
        session_type = session_type_var.get() 

        detailed_text = generate_detailed_text(session_type, details)  # Generate detailed text using OpenAI API

        result_text.delete(1.0, END)  # Clear the result text box
        result_text.insert(END, detailed_text)  # Insert the generated detailed text to result text box
    except Exception as e:
        logging.error("Exception ocurred", exc_info=True)
# root = Tk()

# new function to save the note
def save_note():
    try:
        session_type = session_type_var.get()
        note = result_text.get(1.0, "end-1c")
    
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()
        c.execute("INSERT INTO notes (client_name, session_type, note) VALUES (?, ?, ?)", 
              (session_type, note))
        conn.commit()
        conn.close()
        messagebox.showinfo("Info", "Note saved successfully!")

    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
    

def view_note(note):
    # Create new window
    view_window = Toplevel(root)
    view_window.title("Note Details")
    Label(view_window, text="Note Details:").pack()
    detail_text = Text(view_window, height=20, state=NORMAL)
    detail_text.insert(END, note)
    detail_text.pack(pady=10)

def view_notes():
    try:
        # Connect to the database
        conn = sqlite3.connect('notes.db')
        c = conn.cursor()

        # Fetch all records from the table
        c.execute("SELECT * FROM notes")
        records = c.fetchall()

        # Close the database connection
        conn.close()

        # Create new window
        view_window = Toplevel(root)
        view_window.title("Saved Notes")

        # Create treeview to display the notes
        tree = ttk.Treeview(view_window, columns=("Session Type", "Note"), show="headings")

        # Define column names and widths
        tree.column("#2", anchor=CENTER, width=100)
        tree.column("#3", anchor=CENTER, width=500)
        tree.heading("#2", text="Session Type")
        tree.heading("#3", text="Note")

        # Add data to the treeview
        for record in records:
            tree.insert('', 'end', values=(record[2], record[3]))

        tree.pack()

        # Bind the treeview selection event
        def on_tree_select(event):
            selected_item = tree.selection()[0]
            note = tree.item(selected_item)["values"][2]
            view_note(note)

        tree.bind("<<TreeviewSelect>>", on_tree_select)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)

# root = Tk()

# Create a context menu
menu = Menu(root, tearoff=0)
menu.add_command(label="Copy", command=lambda: root.focus_get().event_generate('<<Copy>>'))
menu.add_command(label="Paste", command=lambda: root.focus_get().event_generate('<<Paste>>'))

def show_menu(e):
    menu.post(e.x_root, e.y_root)

root.bind("<Button-3>", show_menu)

# Dropdown for session type
Label(root, text="Session Type:").pack()
session_type_var = StringVar(root)
session_type_var.set("Direct")  # default value
session_type_option = OptionMenu(root, session_type_var, "Direct", "Indirect")
session_type_option.pack(pady=10)

# Text box for user input

Label(root, text="Details").pack()
details_text = Text(root, height=5, state=NORMAL)
details_text.pack(pady=10)

# Buttons for generating, saving, and viewing notes
Button(root, text="Generate Note", command=generate_note).pack(pady=10)
Button(root, text="Save Note", command=save_note).pack(pady=10)
Button(root, text="View Notes", command=view_notes).pack(pady=10)
Button(root, text="New Note", command=new_note).pack(pady=10)

# Text box for result
Label(root, text="Detailed Notes:").pack()
result_text = Text(root, height=20, state=NORMAL, yscrollcommand=scrollbar.set)  # Ensure text box is in 'normal' state
result_text.pack(pady=10, expand=True, fill='both')  # Added padding for better visibility, expand and fill options for resize


# Configure the scrollbar
scrollbar.config(command=result_text.yview)


root.mainloop()
