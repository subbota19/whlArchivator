# whlArchivator

This project provides a Makefile that sets up a virtual environment, constructs a dependency list using pip-compile, 
and then downloads all required packages using pip to a specified output directory. 
This setup allows you to create a collection of Python packages (whl files) that you can later use in isolated environments.

## How It Works

1) Sets up a Python virtual environment and installs pre-commit.

2) Uses pip-compile to generate a detailed list of package dependencies based on a requirements.in file.

3) All required packages are downloaded as .whl files to an output directory using pip, allowing offline installation later.

# Why Use This Setup?

Using this method enables you to gather a self-contained set of packages. Later, you can use the prepared folder or archive as needed without having to connect to PyPI to install packages.

There are various use cases for this approach, but I’d like to highlight one that’s particularly relevant to my experience:

Imagine you're a DevOps engineer and need to distribute Python packages across business-users laptops. Often, they may encounter issues with SSL or network access. By using this method, you can avoid the need for installing packages via the standard pip process.