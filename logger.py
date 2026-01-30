import os
import inspect

def log(message):
    filename = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
    with open(f"applogging/{filename}.log", "a") as log_file:
        log_file.write(str(message) + "\n")

def clear():
    filename = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
    open(f"applogging/{filename}.log", "w").close()

if __name__ == "__main__":
    # Example usage
    clear()
    log("This is a test log message.")