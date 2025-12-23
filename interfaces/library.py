from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QLineEdit, QListWidget, QMessageBox, QComboBox, QFormLayout, QMenu,
    QFileDialog, QTextEdit, QFrame  
)
from PySide6.QtGui import QKeySequence, QShortcut, QAction, QCursor
from PySide6.QtCore import Qt, Signal
import sys
import os
import json 
from docx import Document
import subprocess
import whisper
import os
import shutil

try:
    import mongo_api
except ImportError:
    from interfaces import mongo_api

