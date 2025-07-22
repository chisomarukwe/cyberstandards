import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QWebEngineView
from PyQt5.QtCore import QUrl

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cybersecurity Standards App")
        self.setGeometry(100, 100, 1200, 800)

        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Add a web view to load the Flask app
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("http://127.0.0.1:5000"))  # Flask app URL
        layout.addWidget(self.web_view)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Start the Flask app in the background (optional)
    import subprocess
    subprocess.Popen(["python", "run.py"])

    # Create and show the main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())