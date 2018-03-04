Asynchronous Programming in Python
==================================

You will need to install the proper python packages. This easiest way is with `pip`:
  ```
  pip install -r requirements.txt
  ```

You might get an error install the `lxml` package, if this is the case Google how to install it on your machine.
Most Linux systems have a `python3-lxml` package that can be installed. I followed the following posts to get it to work:

- https://raspberrypi.stackexchange.com/questions/68894/cant-install-lxml
- https://stackoverflow.com/questions/5178416/pip-install-lxml-error

I would also recommend installing (https://virtualenv.pypa.io/en/stable/installation/)[virtualenv] so you can install the packages without root privelages. Once installed run the following in the directory with this code:
  ```
  virtualenv VENV --python=python3.6
  . VENV/bin/activate
  pip install -r requirements.txt
  ```
  
