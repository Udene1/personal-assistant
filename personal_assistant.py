import datetime
import webbrowser
import os
import time
import math
import sqlite3
import schedule
import threading
import re
import requests
from bs4 import BeautifulSoup

# Database setup
conn = sqlite3.connect('personal_assistant.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS notes
             (id INTEGER PRIMARY KEY, date TEXT, content TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reminders
             (id INTEGER PRIMARY KEY, task TEXT, time TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS todo
             (id INTEGER PRIMARY KEY, task TEXT)''')
conn.commit()

def get_current_time():
    return datetime.datetime.now().strftime("%H:%M:%S")

def get_current_date():
    return datetime.date.today().strftime("%B %d, %Y")

def open_website(url):
    if not re.match(r'http(s)?://', url):
        url = 'http://' + url
    try:
        webbrowser.open(url)
        print(f"Opening {url}")
    except Exception as e:
        print(f"Error opening website: {e}")

def create_note(content):
    try:
        c.execute("INSERT INTO notes (date, content) VALUES (?, ?)", (get_current_date(), content))
        conn.commit()
        print("Note created successfully!")
    except sqlite3.Error as e:
        print(f"Error creating note: {e}")

def read_notes():
    try:
        c.execute("SELECT date, content FROM notes")
        notes = c.fetchall()
        if notes:
            return "\n".join([f"{date} - {content}" for date, content in notes])
        else:
            return "No notes found."
    except sqlite3.Error as e:
        return f"Error reading notes: {e}"

def set_reminder():
    task = input("Enter the reminder task: ")
    time_str = input("Enter the time for the reminder (HH:MM): ")
    try:
        reminder_time = datetime.datetime.strptime(time_str, "%H:%M").time()
        c.execute("INSERT INTO reminders (task, time) VALUES (?, ?)", (task, time_str))
        conn.commit()
        schedule.every().day.at(time_str).do(show_reminder, task)
        print("Reminder set successfully!")
    except ValueError:
        print("Invalid time format. Please use HH:MM.")
    except sqlite3.Error as e:
        print(f"Error setting reminder: {e}")

def show_reminder(task):
    print(f"REMINDER: {task}")

def check_reminders():
    try:
        c.execute("SELECT task, time FROM reminders")
        reminders = c.fetchall()
        for task, time_str in reminders:
            schedule.every().day.at(time_str).do(show_reminder, task)
    except sqlite3.Error as e:
        print(f"Error checking reminders: {e}")

def perform_calculation():
    expression = input("Enter a mathematical expression: ")
    try:
        if re.match(r'^[0-9+\-*/().]+$', expression):
            result = eval(expression)
            print(f"Result: {result}")
        else:
            print("Invalid characters in expression. Please use only numbers and basic operators (+, -, *, /).")
    except Exception as e:
        print(f"Error in calculation: {e}")

def search_internet():
    query = input("Enter your search query: ")
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    open_website(url)

def add_todo():
    task = input("Enter a new todo item: ")
    try:
        c.execute("INSERT INTO todo (task) VALUES (?)", (task,))
        conn.commit()
        print("Todo item added successfully!")
    except sqlite3.Error as e:
        print(f"Error adding todo item: {e}")

def view_todo():
    try:
        c.execute("SELECT id, task FROM todo")
        todos = c.fetchall()
        if todos:
            for id, task in todos:
                print(f"{id}. {task}")
        else:
            print("Your todo list is empty.")
    except sqlite3.Error as e:
        print(f"Error viewing todo list: {e}")

def remove_todo():
    view_todo()
    try:
        id = int(input("Enter the number of the item to remove: "))
        c.execute("DELETE FROM todo WHERE id = ?", (id,))
        conn.commit()
        if c.rowcount > 0:
            print("Todo item removed successfully!")
        else:
            print("No todo item found with that number.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    except sqlite3.Error as e:
        print(f"Error removing todo item: {e}")

def scrape_website():
    url = input("Enter the URL of the website to scrape: ")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\nWhat would you like to scrape?")
        print("1. All text")
        print("2. All links")
        print("3. Specific element by ID")
        print("4. Specific elements by class")
        print("5. Email addresses")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == "1":
            text = soup.get_text()
            print("\nAll text from the website:")
            print(text[:1000] + "..." if len(text) > 1000 else text)
        elif choice == "2":
            links = soup.find_all('a')
            print("\nAll links from the website:")
            for link in links[:20]:  # Limit to first 20 links
                print(link.get('href'))
            if len(links) > 20:
                print("... (more links available)")
        elif choice == "3":
            element_id = input("Enter the ID of the element to scrape: ")
            element = soup.find(id=element_id)
            if element:
                print(f"\nContent of element with ID '{element_id}':")
                print(element.get_text())
            else:
                print(f"No element found with ID '{element_id}'")
        elif choice == "4":
            element_class = input("Enter the class of the elements to scrape: ")
            elements = soup.find_all(class_=element_class)
            if elements:
                print(f"\nContent of elements with class '{element_class}':")
                for i, element in enumerate(elements[:5], 1):  # Limit to first 5 elements
                    print(f"{i}. {element.get_text()[:100]}...")
                if len(elements) > 5:
                    print("... (more elements available)")
            else:
                print(f"No elements found with class '{element_class}'")
        elif choice == "5":
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, response.text)
            if emails:
                print("\nEmail addresses found:")
                for i, email in enumerate(set(emails), 1):  # Use set to remove duplicates
                    print(f"{i}. {email}")
            else:
                print("No email addresses found on the page.")
        else:
            print("Invalid choice. Please try again.")
    except requests.exceptions.RequestException as e:
        print(f"Error scraping website: {e}")

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    check_reminders()
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()

    while True:
        print("\nPersonal Assistant")
        print("1. Get current time")
        print("2. Get current date")
        print("3. Open a website")
        print("4. Create a note")
        print("5. Read notes")
        print("6. Set a reminder")
        print("7. Perform a calculation")
        print("8. Search the internet")
        print("9. Manage todo list")
        print("10. Scrape a website")
        print("11. Exit")
        
        choice = input("Enter your choice (1-11): ")
        
        if choice == "1":
            print(f"Current time: {get_current_time()}")
        elif choice == "2":
            print(f"Current date: {get_current_date()}")
        elif choice == "3":
            url = input("Enter the website URL: ")
            open_website(url)
        elif choice == "4":
            content = input("Enter your note: ")
            create_note(content)
        elif choice == "5":
            print(read_notes())
        elif choice == "6":
            set_reminder()
        elif choice == "7":
            perform_calculation()
        elif choice == "8":
            search_internet()
        elif choice == "9":
            while True:
                print("\nTodo List Manager")
                print("1. Add todo item")
                print("2. View todo list")
                print("3. Remove todo item")
                print("4. Return to main menu")
                todo_choice = input("Enter your choice (1-4): ")
                if todo_choice == "1":
                    add_todo()
                elif todo_choice == "2":
                    view_todo()
                elif todo_choice == "3":
                    remove_todo()
                elif todo_choice == "4":
                    break
                else:
                    print("Invalid choice. Please try again.")
        elif choice == "10":
            scrape_website()
        elif choice == "11":
            print("Goodbye!")
            conn.close()
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()