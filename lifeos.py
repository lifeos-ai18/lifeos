study_tasks = []

def show_menu():
    print("\n=== STUDY OS ===")
    print("1. Add study task")
    print("2. View tasks")
    print("3. Mark task as done")
    print("4. Remove task")
    print("5. Exit")

def add_task():
    task = input("Enter your study task: ")
    study_tasks.append({"task": task, "done": False})
    print("Task added!")

def view_tasks():
    if not study_tasks:
        print("No tasks yet.")
        return
    for i, item in enumerate(study_tasks, start=1):
        status = "Done" if item["done"] else "Pending"
        print(f"{i}. {item['task']} - {status}")

def mark_done():
    view_tasks()
    try:
        num = int(input("Enter task number to mark done: "))
        study_tasks[num - 1]["done"] = True
        print("Task marked as done!")
    except:
        print("Invalid task number.")

def remove_task():
    view_tasks()
    try:
        num = int(input("Enter task number to remove: "))
        removed = study_tasks.pop(num - 1)
        print(f"Removed: {removed['task']}")
    except:
        print("Invalid task number.")

while True:
    show_menu()
    choice = input("Choose an option: ")

    if choice == "1":
        add_task()
    elif choice == "2":
        view_tasks()
    elif choice == "3":
        mark_done()
    elif choice == "4":
        remove_task()
    elif choice == "5":
        print("Goodbye!")
        break
    else:
        print("Invalid choice.")
