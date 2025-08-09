
# CT-Guided Puncture Assistance System

![mainscreen](https://github.com/natekrth/puncture-system-python/blob/main/mainscreen.png?raw=true)

## Installation the application

1. Open terminal/command prompt
2. Clone the application from Github

``` bash

git clone https://github.com/21Gxme/puncture-system-python.git
```

### Creating Python virtualenv in Windows

Prerequisite

- Installed python version 3.10.7
- Using Window 10

Using command prompt

If python is installed in your system, then pip comes in handy. So simple steps are:

- Install virtualenv using

```python
pip install virtualenv
```

- Now in which ever directory you are, this line below will create a virtualenv there

``` python
python -m venv myenv
```

- Now if you are same directory then type to activate the virtual environment
  
``` pip
myenv\Scripts\activate
```

- Install the application dependencies

``` pip
pip install -r requirements.txt
```

### Creating Python virtualenv on macOS

Prerequisite

- Installed python version 3.10.7
- Using MacOS

Using terminal

- Install virtualenv using

``` pip
pip install virtualenv
```

- Now in which ever directory you are, this line below will create a virtualenv there
  
``` python
python3 -m venv env
```

- Upgrade pip

``` python
python3 -m pip install --upgrade pip
```

- Start virtual environment

``` python
source ./env/bin/activate
```

- Install the application dependencies
  
``` python
pip install -r requirements.txt
```

## Run the application

1. Open terminal/command prompt  
2. Go to the directory where main.py is in

``` bash
cd puncutre-system-python
```

1. Start the application

- For Windows

``` python
python main.py
```

- For MacOS

```python
python3 main.py
```

## Application Manual

[Application Manual Link](https://docs.google.com/document/d/1Kof0faIbQw6ZpipOMu2rQnFB9k94W7E_zarcA06d-6g/edit?usp=sharing)
