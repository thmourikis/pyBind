#!/bin/bash

pyi-makespec --onefile --windowed --osx-bundle-identifier pyBind pyBind.py
pyinstaller pyBind.spec
