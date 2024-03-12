LABEL python_version=python{python_version}
RUN virtualenv --no-download /env -p python{python_version}

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
