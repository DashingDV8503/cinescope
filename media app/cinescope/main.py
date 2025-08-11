import sys
from cinescope.ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication

def run():
    """Initializes and runs the Qt application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        # We try to run the app normally
        run()
    except Exception as e:
        # If any error happens, we print it to the console
        print(f"AN ERROR OCCURRED: {e}")
    finally:
        # This will always run, pausing the window so you can see the message
        input("Press Enter to exit...")