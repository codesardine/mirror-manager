from src import app


def start():
    app.run(port=8000, host="127.0.0.1", debug=False)

if __name__ == "__main__":
    start()
